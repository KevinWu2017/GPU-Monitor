import datetime
import threading
import time
from typing import List

import paramiko

from config.setting import REFRESH_SEC, UPDATE_GAP
from core.GPU import GPU
from core.Program import Program
from core.ProgramLogger import ProgramLogger


class Server(threading.Thread):
    def __init__(self, server_name: str, ip: str, username: str, key_path: str):
        super().__init__()
        self.LOGGER = ProgramLogger()
        self.server_name = server_name
        self.ip = ip
        self.username = username
        self.key_path = key_path  # SSH私钥路径

        self.gpu_list: List[GPU] = []

        self.ssh: paramiko.SSHClient = paramiko.SSHClient()  # ssh连接
        # 线程相关
        self.update_time = datetime.datetime.timestamp(datetime.datetime.now())  # 更新时间
        self.paused = False
        self.start()

    def _is_ssh_connected(self) -> bool:
        """Return True if self.ssh has an active transport (connected)."""
        try:
            if not hasattr(self, 'ssh') or self.ssh is None:
                return False
            transport = self.ssh.get_transport()
            return transport is not None and transport.is_active()
        except Exception:
            return False

    def _timestamp(self) -> str:
        """Return current timestamp string for log prefix."""
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def tprint(self, *args, **kwargs):
        """Print with a timestamp prefix."""
        print(f"[{self._timestamp()}]", *args, **kwargs)

    def check(self):
        if datetime.datetime.timestamp(datetime.datetime.now()) - self.update_time > UPDATE_GAP:
            self.pause()
            return True
        return False

    def run(self) -> None:
        while True:
            if not self.paused and not self.check():
                try:
                    self.update_state()
                    time.sleep(REFRESH_SEC)
                except Exception as e:
                    self.tprint(str(e))
                    # 若异常大概率是未建立SSH连接，尝试建立连接
                    if self.update_ssh():
                        # 冷启动或断连恢复后，立刻采集一次数据，不等待整个REFRESH_SEC
                        try:
                            self.update_state()
                        except Exception as e2:
                            self.tprint(str(e2))
                        # 立即采集完成后，再进入正常周期性等待
                        time.sleep(REFRESH_SEC)
                    else:
                        # 连接失败则清空数据并按原周期等待
                        self.gpu_list = []
                        time.sleep(REFRESH_SEC)
            else:
                # 线程暂停时使用更长的等待时间，减少资源消耗
                time.sleep(60)  # 暂停时每分钟检查一次即可

    def resume(self):
        self.tprint("notify thread:", self.server_name)
        self.paused = False

    def pause(self):
        self.tprint("thread sleep:", self.server_name)
        self.paused = True

    def notify_thread(self):
        if self.paused:
            # 如果线程没有启动，启动线程
            self.resume()
        # 更新时间戳，避免线程立即暂停
        self.update_time = datetime.datetime.timestamp(datetime.datetime.now())

    def json(self):
        return {
            'server_name': self.server_name,
            'gpu_list': [gpu.json() for gpu in self.gpu_list],
        }

    def update_ssh(self):
        ssh = paramiko.SSHClient()
        key = paramiko.AutoAddPolicy()
        ssh.set_missing_host_key_policy(key)
        try:
            # 使用SSH密钥认证
            private_key = paramiko.Ed25519Key.from_private_key_file(self.key_path)
            ssh.connect(self.ip, 22, self.username, pkey=private_key)
            self.tprint(f"SSH密钥认证成功: {self.server_name}")
            
            self.ssh = ssh
            return True
        except Exception as e:
            self.tprint(f"SSH连接失败 {self.server_name}: {str(e)}")
            return False

    def get_pro_time(self, pid):
        # 进程运行时间
        if not self._is_ssh_connected():
            # 最小侵入式：尝试连接，失败则抛出让上层处理
            if not self.update_ssh():
                raise RuntimeError("SSH未连接，无法获取进程时间")
        _, stdout, _ = self.ssh.exec_command('ps -o lstart,etime -p ' + pid)
        start_time, duration = 0, 0
        for line in stdout:
            items = line.split()
            if items[0] == 'STARTED':
                continue
            start_time = ':'.join(items[:5])
            duration = str(items[5]).replace('\n', '')
        start_time = datetime.datetime.strptime(start_time, "%a:%b:%d:%H:%M:%S:%Y")
        return str(start_time), duration

    def get_log(self, pid):
        # 获取日志
        if not self._is_ssh_connected():
            if not self.update_ssh():
                return '日志获取失败：SSH未连接'
        cmd = self.LOGGER.get_log(pid)
        _, stdout, _ = self.ssh.exec_command(cmd)
        log = stdout.readlines()
        cur_log = ''.join(log)
        cur_log = cur_log.replace('\n', '<br>').replace('\r', '<br>')
        return cur_log[-2000:]

    def update_state(self):
        # 进程状态
        if not self._is_ssh_connected():
            # 尝试恢复连接，失败则抛异常给上层run()去处理
            if not self.update_ssh():
                raise RuntimeError("SSH未连接，无法更新GPU状态")
        _, stdout, _ = self.ssh.exec_command('ps -o ruser=userForLongName -e -o pid,cmd')
        process_dict = {}
        for line in stdout:
            items = line.split()
            if len(items) >= 3:  # 确保有足够的字段
                username = items[0]
                pid = items[1]
                des = ' '.join(items[2:])
                process_dict[pid] = (username, des)  # 使用PID作为键
        # GPU 状态
        _, stdout, _ = self.ssh.exec_command(
            'nvidia-smi --query-gpu=index,name,memory.used,memory.total,temperature.gpu,fan.speed,power.draw,utilization.gpu --format=csv,noheader')
        gpu_list = []
        for line in stdout:
            num, name, use_memory, total_memory, temp, fan, pwr, gpu_util = map(str.strip, line.split(','))
            if str(use_memory).__contains__("MiB"):
                use_memory = int(use_memory[:-3])
            if str(total_memory).__contains__("MiB"):
                total_memory = int(total_memory[:-3])
            if str(gpu_util).__contains__("%"):
                gpu_util = int(gpu_util[:-1])  # 移除%符号并转换为整数
            gpu_list.append(GPU(num, name, use_memory, total_memory, temp, fan, pwr, gpu_util, []))
        # GPU 程序
        for gpu in gpu_list:
            _, stdout, _ = self.ssh.exec_command(
                f'nvidia-smi -i {gpu.num} --query-compute-apps=pid,used_memory --format=csv,noheader')
            for line in stdout:
                pid, use_memory = map(str.strip, line.split(','))
                # 删除不存在的pid
                cur_log = ''
                log_cmd = '请先绑定日志!'
                try:
                    log_cmd_result = self.LOGGER.get_log(pid)
                    if log_cmd_result:
                        # 获取日志
                        cur_log = self.get_log(pid)
                        log_cmd = log_cmd_result
                except Exception as e:
                    self.tprint(f"获取进程 {pid} 日志时出错: {str(e)}")
                try:
                    if pid in process_dict:
                        username, command = process_dict[pid]
                        if use_memory.__contains__("MiB"):
                            use_memory = int(use_memory[:-3])
                        start_time, duration = self.get_pro_time(pid)
                        gpu.program_list.append(
                            Program(pid, command, username, use_memory, start_time, duration, cur_log, log_cmd))
                    else:
                        self.tprint(f"进程 {pid} 在进程列表中未找到")
                except Exception as e:
                    self.tprint(f"处理进程 {pid} 时出错: {str(e)}")

        self.gpu_list = gpu_list
