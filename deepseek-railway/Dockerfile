# 使用官方Python轻量镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 复制依赖文件并安装
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制所有应用代码
COPY . .

# 暴露端口（Zeabur的Caddy会将请求转发到8080）
EXPOSE 8080

# 设置环境变量，并启动Gunicorn服务器
# 关键：绑定到 0.0.0.0 以接受外部连接，使用环境变量 PORT
ENV PORT=8080
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:$PORT --timeout 300 app:app"]
