import datetime
import re
import threading
import time
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple

import paramiko

from config.setting import REFRESH_SEC
from config.setting import UPDATE_GAP
from core.GPU import GPU
from core.Program import Program


class Server(threading.Thread):
    def __init__(self, server_name: str, ip: str, username: str, key_path: str):
        super().__init__()
        self.server_name = server_name
        self.ip = ip
        self.username = username
        self.key_path = key_path
        self.gpu_list: List[GPU] = []
        self.ssh: paramiko.SSHClient = paramiko.SSHClient()
        self.update_time = datetime.datetime.timestamp(datetime.datetime.now())
        self.paused = False
        self.start()

    def _is_ssh_connected(self) -> bool:
        try:
            if not hasattr(self, "ssh") or self.ssh is None:
                return False
            transport = self.ssh.get_transport()
            return transport is not None and transport.is_active()
        except Exception:
            return False

    def _timestamp(self) -> str:
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def tprint(self, *args, **kwargs):
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
                except Exception as e:
                    self.tprint(str(e))
                    if not self.update_ssh():
                        self.gpu_list = []
                time.sleep(REFRESH_SEC)
            else:
                time.sleep(60)

    def resume(self):
        self.tprint("notify thread:", self.server_name)
        self.paused = False

    def pause(self):
        self.tprint("thread sleep:", self.server_name)
        self.paused = True

    def notify_thread(self):
        if self.paused:
            self.resume()
        self.update_time = datetime.datetime.timestamp(datetime.datetime.now())

    def json(self):
        return {
            "server_name": self.server_name,
            "gpu_list": [gpu.json() for gpu in self.gpu_list],
        }

    def update_ssh(self):
        ssh = paramiko.SSHClient()
        key = paramiko.AutoAddPolicy()
        ssh.set_missing_host_key_policy(key)
        try:
            private_key = paramiko.Ed25519Key.from_private_key_file(self.key_path)
            ssh.connect(self.ip, 22, self.username, pkey=private_key)
            self.tprint(f"SSH密钥认证成功: {self.server_name}")
            self.ssh = ssh
            return True
        except Exception as e:
            self.tprint(f"SSH连接失败 {self.server_name}: {str(e)}")
            return False

    def _to_int(self, value: str, default: int = 0) -> int:
        try:
            return int(float(value))
        except Exception:
            return default

    def _parse_ps_line(self, line: str) -> Optional[Tuple[str, str, str, str, str]]:
        match = re.match(
            r"^\s*(\d+)\s+(\S+)\s+([A-Za-z]{3}\s+[A-Za-z]{3}\s+\d+\s+\d{2}:\d{2}:\d{2}\s+\d{4})\s+(\S+)\s+(.*)$",
            line.strip(),
        )
        if not match:
            return None
        pid, username, start_raw, duration, command = match.groups()
        try:
            start_dt = datetime.datetime.strptime(start_raw, "%a %b %d %H:%M:%S %Y")
            start_time = str(start_dt)
        except Exception:
            start_time = start_raw
        return pid, username, start_time, duration, command

    def update_state(self):
        if not self._is_ssh_connected() and not self.update_ssh():
            raise RuntimeError("SSH未连接，无法更新GPU状态")

        cmd = (
            "export LC_ALL=C; "
            "echo '__GPU__'; "
            "nvidia-smi --query-gpu=index,uuid,name,memory.used,memory.total,temperature.gpu,fan.speed,power.draw,utilization.gpu "
            "--format=csv,noheader,nounits; "
            "echo '__PROC__'; "
            "nvidia-smi --query-compute-apps=gpu_uuid,pid,used_memory --format=csv,noheader,nounits; "
            "echo '__PS__'; "
            "ps -eo pid,user,lstart,etime,args --no-headers"
        )
        _, stdout, stderr = self.ssh.exec_command(cmd)
        out_lines = stdout.readlines()
        err_lines = stderr.readlines()
        if err_lines and not out_lines:
            raise RuntimeError("远程命令执行失败: " + "".join(err_lines).strip())

        section = None
        gpu_lines: List[str] = []
        proc_lines: List[str] = []
        ps_lines: List[str] = []
        for line in out_lines:
            text = line.strip()
            if text == "__GPU__":
                section = "gpu"
                continue
            if text == "__PROC__":
                section = "proc"
                continue
            if text == "__PS__":
                section = "ps"
                continue
            if not text:
                continue
            if section == "gpu":
                gpu_lines.append(text)
            elif section == "proc":
                proc_lines.append(text)
            elif section == "ps":
                ps_lines.append(line.rstrip("\n"))

        process_dict: Dict[str, Tuple[str, str, str, str]] = {}
        for line in ps_lines:
            parsed = self._parse_ps_line(line)
            if parsed is None:
                continue
            pid, username, start_time, duration, command = parsed
            process_dict[pid] = (username, command, start_time, duration)

        gpu_list: List[GPU] = []
        gpu_uuid_map: Dict[str, GPU] = {}
        for line in gpu_lines:
            items = [item.strip() for item in line.split(",")]
            if len(items) < 9:
                continue
            num, uuid, name, used, total, temp, fan, pwr, util = items[:9]
            gpu = GPU(
                num=num,
                name=name,
                use_memory=self._to_int(used),
                total_memory=self._to_int(total),
                temp=temp,
                fan=fan,
                pwr=pwr,
                gpu_util=self._to_int(util),
                program_list=[],
            )
            gpu_list.append(gpu)
            gpu_uuid_map[uuid] = gpu

        for line in proc_lines:
            if "No running processes found" in line:
                continue
            items = [item.strip() for item in line.split(",")]
            if len(items) < 3:
                continue
            gpu_uuid, pid, use_memory = items[:3]
            if pid not in process_dict or gpu_uuid not in gpu_uuid_map:
                continue
            username, command, start_time, duration = process_dict[pid]
            gpu_uuid_map[gpu_uuid].program_list.append(
                Program(
                    pid=pid,
                    command=command,
                    username=username,
                    use_memory=self._to_int(use_memory),
                    start_time=start_time,
                    duration=duration,
                )
            )

        self.gpu_list = gpu_list
