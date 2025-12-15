FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
# 新增：测试命令，检查环境
RUN pwd && ls -la && python --version
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8080
ENV PORT=8080
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--timeout", "300", "app:app"]
