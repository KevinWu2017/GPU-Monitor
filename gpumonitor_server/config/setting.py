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
    
    ('Omega', '10.0.16.126', 'cpwu', private_key_path),
    ('R740', '10.0.16.45', 'cpwu', private_key_path),
    ('R750', '10.0.16.12', 'cpwu', private_key_path),
    ('A100-R760', '10.0.16.20', 'cpwu', private_key_path),
    ('R760', '10.0.16.21', 'cpwu', private_key_path),
    ('ASUS4090x8', '10.0.16.31', 'cpwu', private_key_path),
    ('ASUS4090x82', '10.0.16.42', 'cpwu', private_key_path),
    ('Herta', '10.0.16.55', 'cpwu', private_key_path),
    ('Sparkle', '10.0.16.52', 'cpwu', private_key_path),
    ('Firefly', '10.0.16.46', 'cpwu', private_key_path),
    ('Venti', '10.0.16.77', 'cpwu', private_key_path),
    ('Mona', '10.0.16.79', 'cpwu', private_key_path),
    ('Eula', '10.0.16.82', 'cpwu', private_key_path),
    ('Keqing', '10.0.16.83', 'cpwu', private_key_path),
    ('Zhongli', '10.0.16.86', 'cpwu', private_key_path),
    ('Ayaka', '10.0.16.87', 'cpwu', private_key_path),
    ('40904', '10.0.16.114', 'cpwu', private_key_path),
    ('A1004', '10.0.16.116', 'cpwu', private_key_path),
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
