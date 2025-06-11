# AgentSociety 商业化功能

## 概述

`agentsociety/commercial/` 目录包含了 AgentSociety 的所有商业化功能，包括：

- **Casdoor 认证**：企业级用户认证和权限管理
- **Kubernetes 执行器**：云端分布式执行环境  
- **计费系统**：使用量计费和账户管理
- **支付集成**：支付宝等支付方式集成

## 架构设计

### 插件式架构
商业化功能采用插件式设计，通过动态导入的方式集成到主系统中：

```python
# 主系统会尝试加载商业化功能
try:
    from ..commercial import is_available, get_auth_provider
    if is_available():
        # 加载商业化功能
        auth_provider = get_auth_provider(config)
except ImportError:
    # 商业化功能不可用，使用开源版本
    pass
```

### 优雅降级
当商业化功能不可用时，系统会自动降级到开源版本：

- **认证**：降级为无认证模式
- **执行器**：降级为本地进程执行器
- **计费**：跳过计费逻辑

## 文件结构

```
agentsociety/commercial/
├── __init__.py              # 商业化功能入口
├── README.md               # 本文档
├── auth/                   # 认证模块
│   ├── __init__.py
│   ├── casdoor.py         # Casdoor 集成
│   └── api/               # 认证 API
├── executor/              # 执行器模块
│   ├── __init__.py
│   └── kubernetes.py      # Kubernetes 执行器
├── billing/              # 计费模块
│   ├── __init__.py
│   ├── models.py         # 计费数据模型
│   ├── api.py           # 计费 API
│   ├── calculator.py    # 计费计算逻辑
│   └── system.py        # 计费系统集成
└── webapi/              # 商业化 Web API
```

## 功能开关

### 认证功能
通过配置文件启用 Casdoor 认证：

```yaml
commercial:
  auth:
    enabled: true
    casdoor:
      client_id: "your_client_id"
      client_secret: "your_client_secret"
      # ... 其他配置
```

### Kubernetes 执行器
启用云端执行功能：

```yaml
commercial:
  executor:
    kubernetes:
      enabled: true
      config_paths: ["/path/to/kubeconfig"]
```

### 计费系统
启用使用量计费：

```yaml
commercial:
  billing:
    enabled: true
    currency: "CNY"
    rates:
      llm_input_token: 3.0    # 每百万token价格
      llm_output_token: 3.0   # 每百万token价格
      runtime: 0.001          # 每秒价格
```

## 分支管理策略

### 开源版本分支
```bash
# 删除商业化功能目录
rm -rf agentsociety/commercial/

# 或者通过 .gitignore 忽略
echo "agentsociety/commercial/" >> .gitignore
```

### 商业版本分支
保持 `agentsociety/commercial/` 目录，所有商业化功能会自动启用。

## 部署方式

### 开源版本部署
```bash
# 不包含商业化代码
pip install agentsociety
```

### 商业版本部署
```bash
# 包含商业化功能
pip install agentsociety[commercial]
# 或者从包含商业化代码的分支安装
```

## 开发指南

### 添加新的商业化功能

1. 在相应的模块下创建功能代码
2. 在 `agentsociety/commercial/__init__.py` 中添加导出函数
3. 在主系统中添加功能检测和加载逻辑

### 测试

```bash
# 测试开源版本
rm -rf agentsociety/commercial/
python -m pytest tests/

# 测试商业版本  
git checkout commercial-branch
python -m pytest tests/
```

## 许可证

商业化功能采用商业许可证，仅供授权用户使用。开源功能采用开源许可证。 