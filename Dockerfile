# Stage 1: Compile the frontend code
FROM node:20 AS builder

WORKDIR /app

RUN npm config set registry https://registry.npmmirror.com
COPY ./frontend/package.json ./frontend/package-lock.json ./
RUN npm ci
COPY ./frontend/ .
ENV VITE_WITH_AUTH=true
RUN npm run build

# Stage 2: Copy the compiled frontend code to the python image
FROM python:3.12-slim

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

# Copy dependency files
COPY README.md LICENSE ./
COPY pyproject.toml uv.lock ./
COPY packages/ ./packages/
COPY --from=builder /app/dist /app/packages/agentsociety/agentsociety/_dist

# 使用清华源安装依赖
RUN mkdir -p /etc/uv
RUN echo "[[index]]\nurl = \"https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple/\"\ndefault = true" > /etc/uv/uv.toml
RUN uv sync --frozen --no-dev

# 使用uv venv作为默认Python环境
ENV PATH="/app/.venv/bin:$PATH"
