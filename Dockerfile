# 使用官方的 Python 轻量级基础镜像
FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 安装必要的系统依赖（如果有些 Python 包需要编译）
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 将 requirements.txt 复制到容器中
COPY requirements.txt .

# 首先专门安装 CPU 版本的 PyTorch，省去好几个 G 的 CUDA 依赖包
RUN pip install torch torchvision --extra-index-url https://download.pytorch.org/whl/cpu

# 安装其余依赖
RUN pip install --no-cache-dir -r requirements.txt

# 将项目的其余代码复制到容器中
COPY . .

# （可选）创建一个目录来存放离线数据库和图片，并在容器中提供权限
RUN mkdir -p /app/offline_images /app/models

# 暴露 FastAPI 运行的端口
EXPOSE 8000

# 运行应用程序
CMD ["python", "app.py"]
