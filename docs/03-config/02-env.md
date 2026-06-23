# 环境配置

环境配置包含数据库、文件存储等基础设施设置。

## 配置字段

- `db` (DatabaseConfig): 数据库配置
  - `enabled` (bool): 是否启用数据库存储，默认true
  - `db_type` (str): 数据库类型，支持`sqlite`和`postgresql`
  - `pg_dsn` (Optional[str]): PostgreSQL连接字符串，使用PostgreSQL时必需
- `home_dir` (str): AgentSociety数据存储目录，默认`./agentsociety_data`
- `llm_response_storage` (`detailed` | `lightview`): LLM调用记录存储模式，默认`detailed`。`detailed`保存完整prompt和response；`lightview`只保存步骤、时间、智能体、Block、函数、token和字符数等元数据。

## 配置示例

**SQLite配置（适合开发和小规模实验）**：
```yaml
env:
  db:
    enabled: true
    db_type: sqlite
  llm_response_storage: lightview
  home_dir: ./agentsociety_data
```

**PostgreSQL配置（适合生产环境）**：
```yaml
env:
  db:
    enabled: true
    db_type: postgresql
    pg_dsn: postgresql://user:password@localhost:5432/database
  home_dir: /var/lib/agentsociety
```
