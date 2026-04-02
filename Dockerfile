# ==================== 后端构建阶段 ====================
FROM python:3.11-slim AS backend-builder

WORKDIR /app

# 安装构建依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libc6-dev \
    && rm -rf /var/lib/apt/lists/*

# 复制后端文件
COPY backend/requirements.txt ./
COPY backend/app ./app
COPY backend/run.py ./
COPY .env.example ./

# 创建虚拟环境并安装依赖
RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install --no-cache-dir -r requirements.txt && \
    /opt/venv/bin/pip install --no-cache-dir onnxruntime-openvino

# ==================== 最终镜像阶段 ====================
FROM python:3.11-slim

WORKDIR /app

# 添加 non-free 仓库源（替换原有 sources.list）
RUN rm -f /etc/apt/sources.list.d/debian.sources && \
    echo "deb http://deb.debian.org/debian trixie main contrib non-free non-free-firmware" > /etc/apt/sources.list && \
    echo "deb http://deb.debian.org/debian-security trixie-security main contrib non-free non-free-firmware" >> /etc/apt/sources.list

# 安装运行时依赖，包括 Intel GPU 支持
RUN apt-get update && apt-get install -y --no-install-recommends \
    sqlite3 \
    tini \
    # Intel GPU 和 OpenCL 运行时
    mesa-opencl-icd \
    intel-media-va-driver-non-free \
    # OpenCL 通用库
    ocl-icd-libopencl1 \
    # OpenVINO 运行时依赖
    libtbb12 \
    libpugixml1v5 \
    && rm -rf /var/lib/apt/lists/*

# 复制虚拟环境
COPY --from=backend-builder /opt/venv /opt/venv

# 复制后端代码
COPY --from=backend-builder /app/app ./app
COPY --from=backend-builder /app/run.py ./
COPY --from=backend-builder /app/.env.example ./

# 复制前端构建产物到后端静态目录
COPY frontend/dist ./app/static

# 创建必要的目录
RUN mkdir -p /app/data/images /app/data/tmp/cache /app/data/tmp/covers

# 设置环境变量
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
# OpenCL 环境变量
ENV OCL_ICD_VENDORS=/etc/OpenCL/vendors

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# 使用 tini 作为 init 进程，避免僵尸进程
ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
