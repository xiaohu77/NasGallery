# ==================== 后端构建阶段 ====================
FROM python:3.11-alpine AS backend-builder

WORKDIR /app

# 安装系统依赖
RUN apk add --no-cache \
    gcc \
    musl-dev

# 复制后端文件
COPY backend/requirements.txt ./
COPY backend/app ./app
COPY backend/run.py ./
COPY backend/.env.example ./

# 创建虚拟环境并安装依赖
RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install --no-cache-dir -r requirements.txt
# ==================== 最终镜像阶段 ====================
FROM python:3.11-alpine

WORKDIR /app

# 安装运行时依赖（最小化）
RUN apk add --no-cache \
    sqlite

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

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# 启动命令
CMD ["python", "run.py"]
