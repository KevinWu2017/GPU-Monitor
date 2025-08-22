import os
import sqlite3

"""
系统配置
"""
# ip 更新时间间隔 (min)
IP_UPDATE_TIME = 5
# 查询GPU数据间隔
REFRESH_SEC = 300
# 20s调用接口 休眠线程
UPDATE_GAP = 900
# 配置需要监控的服务器
private_key_path = '/root/.ssh/id_ed25519'  # 私钥钥路径
SERVERS_CONFIG = [
    # 使用SSH密钥认证（容器内的私钥路径）
    # ('<server_name>', '<ip>', '<username>', '<private_key_path>'),
    
]

"""
数据库配置
"""
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = str(BASE_DIR).replace('config', 'database')
os.makedirs(BASE_DIR, exist_ok=True)
print("db path: ", BASE_DIR)
db_path = os.path.join(BASE_DIR, "ip.db")
COON = sqlite3.connect(db_path, check_same_thread=False)

"""
管理员授权码
"""
AccessToken = "ISCS1411"
