# HurricaneMobility Benchmark

## 概述

HurricaneMobility benchmark 以Hurricane Dorian为背景，评估LLM智能体在面对极端天气时的移动行为生成能力。该benchmark专注于模拟用户在飓风期间、飓风前和飓风后的出行模式变化，测试智能体对极端事件响应的建模能力。

## 评测任务

### 极端天气移动行为生成
- **任务描述**: 基于Hurricane Dorian的真实数据，生成用户在飓风前、飓风期间和飓风后的移动行为模式
- **输入**: 飓风信息、用户特征、时间阶段（前/中/后）
- **输出**: 用户的移动行为数据，包括：
  - 总出行时间 (Total Travel Times)
  - 小时出行分布 (Hourly Travel Times)
  - 相对变化率 (Relative Changes)

## 评测流程

### 数据准备阶段
1. **真实数据加载**: 从数据集加载Hurricane Dorian期间的真实移动行为数据
2. **智能体初始化**: 配置智能体参数和飓风环境设置
3. **任务分发**: 为不同时间阶段生成相应的移动行为任务

### 行为生成阶段
1. **环境感知**: 智能体理解飓风影响和交通状况变化
2. **风险评估**: 分析不同时间阶段的出行风险
3. **行为生成**: 生成符合极端天气条件的移动模式
4. **数据输出**: 输出结构化的移动行为数据

### 评估阶段
1. **变化率对比**: 比较生成数据与真实数据的变化率
2. **分布相似性**: 评估小时出行分布的相似性
3. **加权评分**: 综合各项指标得出最终评分

## 评价指标

### 1. 变化率准确度 (Change Rate Score)

评估生成数据在飓风期间和飓风后相对于飓风前的变化率准确性。

**公式**:
```
MAPE = (|真实变化率 - 生成变化率| / |真实变化率|) × 100%
变化率分数 = max(0, 100 - 平均MAPE)
```

其中：
- **飓风期间变化率**: (飓风期间出行时间 - 飓风前出行时间) / 飓风前出行时间 × 100%
- **飓风后变化率**: (飓风后出行时间 - 飓风前出行时间) / 飓风前出行时间 × 100%
- **平均MAPE**: (飓风期间MAPE + 飓风后MAPE) / 2

### 2. 分布相似度 (Distribution Score)

评估生成的小时出行分布与真实分布的相似性。

**公式**:
```
余弦相似度 = (A · B) / (||A|| × ||B||)
分布分数 = max(0, 平均余弦相似度 × 100)
```

其中：
- A, B: 归一化后的小时出行分布向量
- 平均余弦相似度: (飓风前相似度 + 飓风期间相似度 + 飓风后相似度) / 3

### 3. 最终评分 (Final Score)

**公式**:
```
最终分数 = 变化率分数 × 0.6 + 分布分数 × 0.4
```

**权重说明**:
- 变化率分数权重60%：直接衡量飓风影响的准确性
- 分布分数权重40%：评估出行模式的时间分布相似性

## 数据集信息

- **数据集仓库**: https://huggingface.co/datasets/tsinghua-fib-lab/hurricane-mobility-generation-benchmark
- **分支**: main
- **支持模式**: inference (test模式暂不支持)
- **数据特征**: Hurricane Dorian期间的真实移动行为数据

## 依赖要求

```python
numpy >= 1.26.4
```

## 使用示例

```shell
asbench run --config <YOUR-CONFIG-FILE>.yml --agent <YOUR-AGENT-FILE>.py --mode inference HurricaneMobility
```

## 输出数据格式

```python
{
    "total_travel_times": [120, 85, 95],  # [飓风前, 飓风期间, 飓风后] 总出行时间(分钟)
    "hourly_travel_times": [
        [10, 15, 20, 25, 30, 35, 40, 35, 30, 25, 20, 15, 10, 5, 0, 0, 0, 0, 5, 10, 15, 20, 15, 10],  # 飓风前24小时分布
        [5, 8, 12, 15, 18, 20, 22, 20, 18, 15, 12, 8, 5, 2, 0, 0, 0, 0, 2, 5, 8, 12, 8, 5],  # 飓风期间24小时分布
        [8, 12, 16, 20, 24, 28, 32, 28, 24, 20, 16, 12, 8, 4, 0, 0, 0, 0, 4, 8, 12, 16, 12, 8]   # 飓风后24小时分布
    ]
}
```

## 详细评估指标

评估结果还包含以下详细指标：

```python
{
    "change_rate_score": 85.2,  # 变化率准确度分数
    "distribution_score": 78.9,  # 分布相似度分数
    "final_score": 82.7,  # 最终加权分数
    "detailed_metrics": {
        "real_change_rates": {
            "during_vs_before": -29.2,  # 真实飓风期间变化率(%)
            "after_vs_before": -20.8    # 真实飓风后变化率(%)
        },
        "generated_change_rates": {
            "during_vs_before": -31.5,  # 生成飓风期间变化率(%)
            "after_vs_before": -22.1    # 生成飓风后变化率(%)
        },
        "change_rate_error": {
            "during_vs_before": 2.3,    # 飓风期间变化率误差
            "after_vs_before": 1.3      # 飓风后变化率误差
        }
    }
}
```

## 版本信息

- **版本**: 1.0.0
- **作者**: AgentSociety Team
- **标签**: hurricane-mobility, extreme-weather 