FROM python:3.9.5-slim-buster
LABEL author="Chenpeng Wu"
LABEL email="cpwu2017@gmail.com"
LABEL version="1"
LABEL description="GPU-Monitor Server"

# 合并时区设置指令减少层数
RUN ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime && \
    echo 'Asia/Shanghai' > /etc/timezone

# 创建.ssh目录并设置权限(合并指令减少层数)
RUN mkdir -p /root/.ssh && chmod 700 /root/.ssh

RUN mkdir /usr/src/gpumonitor_server -p
WORKDIR /usr/src/gpumonitor_server

# 先只复制requirements.txt，利用Docker缓存机制
COPY requirements.txt /usr/src/gpumonitor_server/
RUN pip install -r requirements.txt -i  https://pypi.tuna.tsinghua.edu.cn/simple

# 复制SSH私钥
COPY id_ed25519 /root/.ssh/id_ed25519
RUN chmod 600 /root/.ssh/id_ed25519

# 最后复制所有代码文件
COPY . /usr/src/gpumonitor_server
EXPOSE 7030
CMD python -u main.py