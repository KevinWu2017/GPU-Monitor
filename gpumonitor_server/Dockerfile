FROM python:3.9.5-slim-buster
LABEL author="Chenpeng Wu"
LABEL email="cpwu2017@gmail.com"
LABEL version="1"
LABEL description="GPU-Monitor Server"

RUN ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime
RUN echo 'Asia/Shanghai' >/etc/timezone

# 创建.ssh目录
RUN mkdir -p /root/.ssh
RUN chmod 700 /root/.ssh

RUN mkdir /usr/src/gpumonitor_server -p
COPY . /usr/src/gpumonitor_server

# 复制SSH私钥
COPY id_ed25519 /root/.ssh/id_ed25519
RUN chmod 600 /root/.ssh/id_ed25519

WORKDIR /usr/src/gpumonitor_server
RUN pip install -r requirements.txt -i  https://pypi.tuna.tsinghua.edu.cn/simple
RUN ls
WORKDIR /usr/src/gpumonitor_server
RUN ls
EXPOSE 7030
CMD python -u main.py