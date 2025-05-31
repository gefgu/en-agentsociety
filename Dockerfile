# Stage 1: Compile the frontend code
FROM node:20 AS builder

WORKDIR /app

RUN npm config set registry https://registry.npmmirror.com
COPY ./frontend/package.json ./frontend/package-lock.json ./
RUN npm ci
COPY ./frontend/ .
RUN npm run build

# Stage 2: Copy the compiled frontend code to the python image
FROM python:3.12-slim

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app
RUN pip config set global.index-url https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple

# 1. copy pyproject.toml first
COPY pyproject.toml .
COPY scripts/pyproject2requirements.py .

# 2. install build tools and extract dependencies
RUN pip install --upgrade pip && \
    pip install tomli && \
    python pyproject2requirements.py

# 3. install project dependencies
RUN pip install --no-cache-dir -r requirements.txt

# 4. copy the whole project code
COPY agentsociety /app/agentsociety
COPY setup.py /app/setup.py
COPY --from=builder /app/dist /app/agentsociety/_dist
RUN pip install . --no-cache-dir \
    && rm -rf /app
RUN pip install agentsociety-community==0.2.2 --no-cache-dir
