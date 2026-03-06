import datetime

from flask import Flask
from flask_cors import CORS

from config.setting import SERVERS_CONFIG
from core.Server import Server


def tprint(*args, **kwargs):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}]", *args, **kwargs)


app = Flask(__name__)
CORS(app, resources=r"/*")

servers = []
for server_config in SERVERS_CONFIG:
    if len(server_config) == 4:
        servers.append(Server(*server_config))
    else:
        tprint(f"无效的服务器配置，应为4个参数: {server_config}")

tprint(f"已配置 {len(servers)} 台服务器")


@app.route("/get_gpu_state", methods=["GET"])
def get_gpu_state():
    gup_data = []
    for server in servers:
        server.notify_thread()
        if not server.paused:
            gup_data.append(server.json())
    return gup_data


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=7030, threaded=True)
