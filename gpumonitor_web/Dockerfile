# 第一阶段：构建阶段
FROM node:16-alpine as build-stage
LABEL author="Chenpeng Wu"
LABEL email="cpwu2017@gmail.com"
LABEL version="1"
LABEL description="GPU-Monitor Web"

WORKDIR /app

# 复制 package.json 和 package-lock.json (如果存在)
COPY package*.json ./

# 安装依赖
RUN npm install

# 复制源代码
COPY . .

# 构建项目
RUN npm run build

# 第二阶段：生产阶段
FROM nginx:alpine
RUN ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime
RUN echo 'Asia/Shanghai' >/etc/timezone

# 从构建阶段复制构建结果
COPY --from=build-stage /app/dist/ /usr/share/nginx/html/
COPY nginx/default.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
