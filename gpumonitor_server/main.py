import datetime
import paramiko
from flask import Flask
from flask import jsonify
from flask import request
from flask_cors import CORS

from config.setting import COON, SERVERS_CONFIG, AccessToken
from core.Server import Server
from service.announcement_service import AnnouncementService

from service.ip_service import IpService

def tprint(*args, **kwargs):
    """Print with a timestamp prefix."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}]", *args, **kwargs)

app = Flask(__name__)
CORS(app, resources=r'/*')
ip_service = IpService(COON)
announcement_service = AnnouncementService(COON)

# 创建服务器列表，只支持SSH密钥认证
servers = []
for server_config in SERVERS_CONFIG:
    if len(server_config) == 4:
        # 格式：(name, ip, user, key_path)
        servers.append(Server(*server_config))
    else:
        tprint(f"无效的服务器配置，应为4个参数: {server_config}")

tprint(f"已配置 {len(servers)} 台服务器")


@app.route('/get_gpu_state', methods=['GET'])
def get_gpu_state():
    # 获取访问ip
    ip = request.remote_addr
    # 插入
    ip_service.add_ip(ip)
    # 读取线程数据
    gup_data = []
    for server in servers:
        server.notify_thread()  # 只唤醒暂停的线程，不重置所有服务器的时间戳
        if not server.paused:
            gup_data.append(server.json())
    return gup_data


# 新增维护日志
@app.route('/add_log', methods=['POST'])
def add_log():
    server_name = request.json.get('server_name')
    pid = request.json.get('pid')
    log = request.json.get('cmd')
    for server in servers:
        if server.server_name == server_name:
            server.LOGGER.add_log(pid, log)
            # print(server.LOGGER.log_dict)
    return jsonify(
        {"code": 200,
         "message": "绑定  server : " + str(server_name) + " pid : " + str(pid) + " cmd : " + str(log) + " 成功!"})


# 更新日志维护
@app.route('/update_log', methods=['POST'])
def update_log():
    server_name = request.json.get('server_name')
    pid = request.json.get('pid')
    log = request.json.get('cmd')
    for server in servers:
        if server.server_name == server_name:
            server.LOGGER.update_log(pid, log)
            break
    return jsonify(
        {"code": 200,
         "message": "更新  server : " + str(server_name) + " pid : " + str(pid) + " cmd : " + str(log) + " 成功!"})


# 删除日志
@app.route('/delete_log', methods=['POST'])
def delete_log():
    server_name = request.json.get('server_name')
    pid = request.json.get('pid')
    for server in servers:
        if server.server_name == server_name:
            if server.LOGGER.log_dict.get(pid):
                server.LOGGER.del_log(pid)
                break
            else:
                return jsonify(
                    {"code": 400, "message": "日志  server : " + str(server_name) + " pid : " + str(pid) + " 不存在!"})
    return jsonify({"code": 200, "message": "删除  server : " + str(server_name) + " pid : " + str(pid) + " 成功!"})


# @app.route('/runMC', methods=['GET'])
# def run_mc():
#     # run_mc_server('219.216.64.204', 'mc', 'mc')
#     host = '219.216.64.204'
#     user = 'mc'
#     passwd = 'mc'
#     ssh = paramiko.SSHClient()
#     key = paramiko.AutoAddPolicy()
#     ssh.set_missing_host_key_policy(key)
#     ssh.connect(host, 22, user, passwd)
#     _, stdout, _ = ssh.exec_command(
#         'cd /opt/mc/paper/ && screen -dmS minecraft java -Xms2048m -Xmx4096m -jar paper118.jar nogui > minecraft.log 2>&1\n')
#     return jsonify({"code": 200, "message": "mc-server : 启动成功!"})


# # 彩蛋
# @app.route('/stopMC', methods=['GET'])
# def stop_mc():
#     host = '219.216.64.204'
#     user = 'mc'
#     passwd = 'mc'
#     ssh = paramiko.SSHClient()
#     key = paramiko.AutoAddPolicy()
#     ssh.set_missing_host_key_policy(key)
#     ssh.connect(host, 22, user, passwd)
#     _, stdout, _ = ssh.exec_command('cd /opt/mc/paper/ && screen -S minecraft -p 0 -X stuff "stop^M"\n')
#     return jsonify({"code": 200, "message": "mc-server : 关闭成功!"})


# 系统监测模块
@app.route('/get_ip_data', methods=['GET'])
def get_ip_data():
    his_ip_data = ip_service.gen_ip_data_one_month()
    return his_ip_data


@app.route('/get_statistics', methods=['GET'])
def get_statistics():
    ip_nums_today = ip_service.get_ip_nums_today()
    ip_nums_month = ip_service.get_ip_nums_this_month()
    ip_nums_all = ip_service.get_ip_nums_history()
    return {**ip_nums_today, **ip_nums_month, **ip_nums_all}


# 公告模块
@app.route('/add_announcement', methods=['POST'])
def add_announcement():
    try:
        if request.json['access_token'] == AccessToken:
            announcement_service.add_announcement(announcement=request.json["announcement"],
                                                  expire_date=int(request.json["expire_date"]),
                                                  available=int(request.json["available"]),
                                                  times=int(request.json["times"]))
            return jsonify({'code': 200, 'message': '添加成功!'})
        else:
            return jsonify({'code': 201, 'message': "认证失败!"})
    except Exception as e:
        tprint(str(e))
        return jsonify({'code': 200, 'message': "添加失败!"})


# 删除公告
@app.route('/delete_announcement', methods=['POST'])
def delete_announcement():
    try:
        if request.json['access_token'] == AccessToken:
            announcement_service.del_announcement_by_id(request.json["announcement_id"])
            return jsonify({'code': 200, 'message': '删除成功!'})
        else:
            return jsonify({'code': 201, 'message': "认证失败!"})
    except Exception as e:
        tprint(str(e))
        return jsonify({'code': 200, 'message': "删除失败!"})


@app.route('/get_announcement', methods=['GET'])
def get_announcement():
    return announcement_service.get_announcement_by_ip(request.remote_addr)


@app.route('/add_push_info', methods=['POST'])
def add_push_info():
    tprint(request.json)
    announcement_service.add_push_info(ip=request.remote_addr, announcement_id=request.json['announcement_id'])
    return jsonify({'code': 200, 'message': '添加成功!'})


@app.route('/get_all_history', methods=['GET'])
def get_all_history_announcement():
    res = announcement_service.get_all_history_announcement()
    return jsonify({'history': res})


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=7030, threaded=True)
