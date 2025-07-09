# BenchmarkRunner 使用指南

## 概述

`BenchmarkRunner` 是一个独立的基准测试运行器，提供了统一的接口来执行基准测试和评估结果。它抽象了CLI命令的核心功能，支持程序化调用。

## 主要特性

- **统一接口**: 提供简洁的API来运行基准测试和评估结果
- **异步支持**: 支持异步操作，提高性能
- **数据库集成**: 自动处理数据库更新和结果存储
- **错误处理**: 完善的错误处理和状态管理
- **灵活配置**: 支持多种配置格式和参数

## 基本用法

### 初始化 BenchmarkRunner

```python
from pathlib import Path
from agentsociety_benchmark import BenchmarkRunner

# 创建 BenchmarkRunner 实例
runner = BenchmarkRunner(
    home_dir=Path.home() / ".agentsociety",
    tenant_id="your_tenant_id",
    exp_id="your_experiment_id"
)
```

### 运行基准测试

```python
import asyncio
from agentsociety.configs import AgentConfig, LLMConfig, EnvConfig
from agentsociety.llm.llm import LLMProviderType
from agentsociety.storage import DatabaseConfig
from agentsociety_benchmark.cli.config import BenchmarkConfig

async def run_benchmark():
    # 创建配置对象
    benchmark_config = BenchmarkConfig(
        llm=[LLMConfig(
            provider=LLMProviderType.OpenAI,
            model="gpt-4",
            api_key="your_api_key",
            base_url=None,
            concurrency=200,
            timeout=30
        )],
        env=EnvConfig(
            db=DatabaseConfig(
                enabled=True,
                db_type="sqlite",
                pg_dsn=None
            ),
            home_dir="/path/to/home"
        )
    )
    
    agent_config = AgentConfig(
        agent_class="path/to/agent.py",
        number=1
    )
    
    result = await runner.run(
        task_name="DailyMobility",
        benchmark_config=benchmark_config,
        agent_config=agent_config,
        datasets_path=Path("datasets"),
        mode="test",  # 或 "inference"
        official_validated=False,
        save_results=True
    )
    
    print(f"Benchmark completed: {result}")

# 运行
asyncio.run(run_benchmark())
```

### 评估结果

```python
async def evaluate_results():
    result = await runner.evaluate(
        task_name="DailyMobility",
        results_file="results.pkl",
        datasets_path=Path("datasets"),
        output_file=Path("evaluation_result.json"),
        save_results=True
    )
    
    print(f"Evaluation completed: {result}")

# 运行
asyncio.run(evaluate_results())
```

## API 参考

### BenchmarkRunner 类

#### 构造函数

```python
BenchmarkRunner(
    home_dir: Optional[Path] = None,
    tenant_id: str = "",
    exp_id: str = ""
)
```

**参数**:
- `home_dir`: 数据库和日志的主目录
- `tenant_id`: 数据库操作的租户ID
- `exp_id`: 实验ID，用于跟踪

#### 方法

##### run()

运行基准测试实验。

```python
async def run(
    self,
    task_name: str,
    benchmark_config: BenchmarkConfig,
    agent_config: AgentConfig,
    datasets_path: Optional[Path] = None,
    mode: str = "test",
    official_validated: bool = False,
    callback_url: str = "",
    save_results: bool = True
) -> Dict[str, Any]
```

**参数**:
- `task_name`: 基准测试任务名称
- `benchmark_config`: 基准测试配置对象
- `agent_config`: 代理配置对象
- `datasets_path`: 数据集目录路径（可选）
- `mode`: 执行模式 ('test' 或 'inference')
- `official_validated`: 是否为官方验证
- `callback_url`: 完成通知的回调URL
- `save_results`: 是否保存结果到数据库

**返回**:
- 包含执行结果和元数据的字典

##### evaluate()

评估基准测试结果。

```python
async def evaluate(
    self,
    task_name: str,
    results_file: str,
    datasets_path: Optional[Path] = None,
    output_file: Optional[Path] = None,
    save_results: bool = True
) -> Dict[str, Any]
```

**参数**:
- `task_name`: 基准测试任务名称
- `results_file`: 结果文件路径
- `datasets_path`: 数据集目录路径（可选）
- `output_file`: 评估结果输出文件路径（可选）
- `save_results`: 是否保存结果到数据库

**返回**:
- 包含评估结果和元数据的字典

##### list_available_tasks()

列出所有可用的基准测试任务。

```python
def list_available_tasks(self) -> list
```

**返回**:
- 可用任务名称列表

##### get_task_info()

获取特定任务的详细信息。

```python
def get_task_info(self, task_name: str) -> Optional[Dict[str, Any]]
```

**参数**:
- `task_name`: 任务名称

**返回**:
- 任务信息字典或None

## 使用示例

### 完整的工作流程

```python
import asyncio
from pathlib import Path
from agentsociety_benchmark import BenchmarkRunner

async def complete_workflow():
    # 1. 初始化运行器
    runner = BenchmarkRunner(
        home_dir=Path.home() / ".agentsociety",
        tenant_id="workflow_tenant",
        exp_id="workflow_experiment_001"
    )
    
    # 2. 查看可用任务
    tasks = runner.list_available_tasks()
    print(f"Available tasks: {tasks}")
    
    # 3. 创建配置对象
    from agentsociety.configs import AgentConfig, LLMConfig, EnvConfig
    from agentsociety.llm.llm import LLMProviderType
    from agentsociety.storage import DatabaseConfig
    from agentsociety_benchmark.cli.config import BenchmarkConfig
    
    benchmark_config = BenchmarkConfig(
        llm=[LLMConfig(
            provider=LLMProviderType.OpenAI,
            model="gpt-4",
            api_key="your_api_key",
            base_url=None,
            concurrency=200,
            timeout=30
        )],
        env=EnvConfig(
            db=DatabaseConfig(
                enabled=True,
                db_type="sqlite",
                pg_dsn=None
            ),
            home_dir="/path/to/home"
        )
    )
    
    agent_config = AgentConfig(
        agent_class="path/to/agent.py",
        number=1
    )
    
    # 4. 运行基准测试
    result = await runner.run(
        task_name="DailyMobility",
        benchmark_config=benchmark_config,
        agent_config=agent_config,
        datasets_path=Path("datasets"),
        mode="test"
    )
    
    # 4. 检查结果
    if result.get('success'):
        print(f"Benchmark completed successfully")
        print(f"Results file: {result.get('results_file')}")
        
        # 5. 单独运行评估（如果需要）
        if result.get('results_file'):
            eval_result = await runner.evaluate(
                task_name="DailyMobility",
                results_file=result['results_file'],
                datasets_path=Path("datasets"),
                output_file=Path("evaluation.json")
            )
            print(f"Evaluation result: {eval_result}")

# 运行完整工作流程
asyncio.run(complete_workflow())
```

### 错误处理

```python
async def run_with_error_handling():
    runner = BenchmarkRunner()
    
    try:
        # 创建配置对象
        benchmark_config = BenchmarkConfig(...)  # 你的配置
        agent_config = AgentConfig(...)  # 你的代理配置
        
        result = await runner.run(
            task_name="DailyMobility",
            benchmark_config=benchmark_config,
            agent_config=agent_config
        )
        print(f"Success: {result}")
        
    except ValueError as e:
        print(f"Invalid configuration: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
```

## 与CLI的集成

BenchmarkRunner 已经集成到现有的CLI命令中。当你运行 `asbench run` 或 `asbench evaluate` 命令时，它们现在使用 BenchmarkRunner 来执行操作。

### CLI 命令示例

```bash
# 运行基准测试
asbench run DailyMobility --config config.json --agent agent.json

# 评估结果
asbench evaluate DailyMobility results.pkl --config config.json
```

## 配置要求

### 基准测试配置文件

支持 JSON 和 YAML 格式：

```json
{
  "llm": [
    {
      "model": "gpt-4",
      "api_key": "your_api_key"
    }
  ],
  "env": {
    "home_dir": "/path/to/home"
  }
}
```

### 代理配置文件

支持 JSON、YAML 和 Python 文件格式：

```json
{
  "agent_class": "path/to/agent.py",
  "number": 1
}
```

## 注意事项

1. **异步操作**: 所有主要方法都是异步的，需要使用 `await` 或 `asyncio.run()`
2. **文件路径**: 确保所有文件路径都是有效的
3. **数据库连接**: 如果启用数据库存储，确保数据库配置正确
4. **错误处理**: 建议使用 try-catch 块来处理可能的异常
5. **资源清理**: BenchmarkRunner 会自动处理数据库连接的清理

## 故障排除

### 常见问题

1. **任务未找到**: 确保任务名称正确，并且任务已正确安装
2. **配置文件错误**: 检查配置文件格式和内容
3. **数据集路径**: 确保数据集目录存在且包含必要文件
4. **数据库错误**: 检查数据库配置和权限

### 调试技巧

```python
# 启用详细日志
import logging
logging.basicConfig(level=logging.DEBUG)

# 检查任务信息
task_info = runner.get_task_info("DailyMobility")
print(f"Task info: {task_info}")
``` 