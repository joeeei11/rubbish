FROM python:3.11-slim

WORKDIR /app
ENV PYTHONPATH=/app

# 安装系统依赖（Pillow 需要 libjpeg）
RUN apt-get update && apt-get install -y \
    libjpeg-dev \
    libpng-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
# CPU 版 PyTorch（避免拉取 GPU 镜像）
RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu \
    && pip install --no-cache-dir -r requirements.txt

COPY . .

# 确保入口脚本有执行权限
RUN chmod +x entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["./entrypoint.sh"]
