# 使用官方 Python 轻量镜像
FROM python:3.13-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量：不生成 .pyc 文件，不缓冲标准输出
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 安装系统依赖（如果有些包需要编译）
# 删除了 apt-get 步骤，因为大多数 NAS 网络连外网 apt 源可能会报错，并且现在这些库都有预编译的 wheel，可以直接装


# 复制 requirements 文件并安装依赖
COPY requirements.txt .

# 使用清晰镜像源加速下载并安装依赖
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 把整个项目复制进去
COPY . .

# 暴露 Streamlit 的默认端口
EXPOSE 8501

# 容器启动命令，指定运行 src/app.py 
CMD ["streamlit", "run", "src/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
