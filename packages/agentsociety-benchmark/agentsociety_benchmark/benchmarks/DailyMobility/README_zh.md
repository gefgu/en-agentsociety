# DailyMobility Benchmark

## 概述

DailyMobility benchmark 以北京市用户为基础，评估LLM智能体在日常移动行为生成方面的能力。该benchmark专注于模拟真实用户的日常出行模式，包括活动半径、每日访问地点数量、意图序列和意图比例等关键移动特征。

## 评测任务

### 日常移动行为生成
- **任务描述**: 基于用户特征和城市环境，生成符合真实用户行为的日常移动模式
- **输入**: 用户人口统计学特征、城市地理信息、时间约束
- **输出**: 用户的日常移动行为数据，包括：
  - 回转半径 (Gyration Radius)
  - 每日访问地点数量 (Daily Location Numbers)
  - 意图序列 (Intention Sequences)
  - 意图比例分布 (Intention Proportions)

## 评测流程

### 数据准备阶段
1. **真实数据加载**: 从数据集加载北京市用户的真实移动行为数据
2. **智能体初始化**: 配置智能体参数和环境设置
3. **任务分发**: 为每个用户生成相应的移动行为任务

### 行为生成阶段
1. **用户特征分析**: 智能体分析用户的人口统计学特征
2. **环境感知**: 理解城市地理布局和交通网络
3. **行为生成**: 生成符合用户特征的日常移动模式
4. **数据输出**: 输出结构化的移动行为数据

### 评估阶段
1. **分布对比**: 将生成数据与真实数据的分布进行对比
2. **JSD计算**: 计算Jensen-Shannon散度评估分布相似性
3. **分数计算**: 综合各项指标得出最终评分

## 评价指标

### Jensen-Shannon散度 (JSD)

Jensen-Shannon散度用于衡量生成数据分布与真实数据分布的相似性。JSD值越小，表示分布越相似。

**公式**:
```
JSD(P||Q) = 0.5 × KL(P||M) + 0.5 × KL(Q||M)
```

其中：
- P: 真实数据分布
- Q: 生成数据分布  
- M: (P + Q) / 2
- KL: Kullback-Leibler散度

### 具体评价指标

#### 1. 回转半径JSD (JSD Gyration Radius)
**描述**: 评估生成的回转半径分布与真实分布的相似性
**公式**: `JSD(真实回转半径分布 || 生成回转半径分布)`

#### 2. 每日地点数量JSD (JSD Daily Location Numbers)
**描述**: 评估生成的每日访问地点数量分布与真实分布的相似性
**公式**: `JSD(真实地点数量分布 || 生成地点数量分布)`

#### 3. 意图序列JSD (JSD Intention Sequences)
**描述**: 评估生成的意图序列分布与真实分布的相似性
**公式**: `JSD(真实意图序列分布 || 生成意图序列分布)`

#### 4. 意图比例JSD (JSD Intention Proportions)
**描述**: 评估生成的意图比例分布与真实分布的相似性
**公式**: `JSD(真实意图比例分布 || 生成意图比例分布)`

### 最终评分 (Final Score)

**公式**:
```
Final Score = ((1 - JSD_gyration + 1 - JSD_locations + 1 - JSD_sequences + 1 - JSD_proportions) / 4) × 100
```

**说明**:
- 每个JSD指标转换为相似性分数: `1 - JSD`
- 四个指标等权重平均
- 最终分数范围为0-100，分数越高表示生成质量越好

## 数据集信息

- **数据集仓库**: https://huggingface.co/datasets/tsinghua-fib-lab/daily-mobility-generation-benchmark
- **分支**: main
- **支持模式**: inference (test模式暂不支持)
- **数据特征**: 北京市用户日常移动行为数据

## 依赖要求

```python
numpy >= 1.26.4
scipy >= 1.13.0
```

## 使用示例

```shell
asbench run --config <YOUR-CONFIG-FILE>.yml --agent <YOUR-AGENT-FILE>.py --mode inference DailyMobility
```

## 输出数据格式

```python
{
    "gyration_radius": [2.5, 3.1, 1.8, ...],  # 用户回转半径列表
    "daily_location_numbers": [5, 7, 4, ...],  # 每日访问地点数量列表
    "intention_sequences": [[1,2,3,1], [2,1,4,2], ...],  # 意图序列列表
    "intention_proportions": [[0.3,0.2,0.5], [0.4,0.3,0.3], ...]  # 意图比例列表
}
```

## 版本信息

- **版本**: 1.0.0
- **作者**: AgentSociety Team
- **标签**: mobility-generation 