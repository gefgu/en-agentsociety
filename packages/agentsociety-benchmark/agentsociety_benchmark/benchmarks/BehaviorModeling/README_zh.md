# BehaviorModeling Benchmark

## 概述

BehaviorModeling benchmark 旨在评估LLM智能体在用户行为建模方面的能力，包括物品推荐和评价生成两类核心任务。该benchmark支持test和inference两种运行模式，为智能体行为建模研究提供全面的评估框架。

## 评测任务

### 1. 物品推荐任务 (Recommendation Task)
- **任务描述**: 基于用户历史行为和偏好，为用户推荐最合适的物品
- **输入**: 用户ID、候选物品类别、候选物品列表
- **输出**: 按推荐优先级排序的物品列表

### 2. 评价生成任务 (Review Writing Task)
- **任务描述**: 模拟用户对特定物品的评价生成，包括评分和评论文本
- **输入**: 用户ID、物品ID、物品信息
- **输出**: 星级评分(1-5星)和评论文本

## 评测流程

### Test模式
1. **数据准备**: 加载测试数据集，包含用户行为历史和真实标签
2. **任务执行**: 智能体处理推荐和评价生成任务
3. **结果评估**: 计算各项评价指标
4. **分数计算**: 综合推荐准确率和评价质量得出最终分数

### Inference模式
1. **推理执行**: 智能体基于给定上下文进行推理
2. **结果验证**: 与真实标签进行对比
3. **指标收集**: 收集用于智能体执行效果评价的指标

## 评价指标

### 推荐任务指标 (Recommendation Metrics)

#### Hit Rate@N
计算推荐列表中前N个物品包含真实目标物品的比例：

**公式**:
```
HR@N = (推荐列表前N个物品中包含真实物品的样本数) / (总样本数)
```

**具体指标**:
- **Top-1 Hit Rate**: HR@1，推荐列表第一个物品的命中率
- **Top-3 Hit Rate**: HR@3，推荐列表前三个物品的命中率  
- **Top-5 Hit Rate**: HR@5，推荐列表前五个物品的命中率
- **Average Hit Rate**: (HR@1 + HR@3 + HR@5) / 3

### 评价生成任务指标 (Simulation Metrics)

#### 1. 偏好估计准确率 (Preference Estimation)
基于星级评分的准确性：

**公式**:
```
Preference Estimation = 1 - (平均星级误差 / 5)
```

其中星级误差 = |预测星级 - 真实星级| / 5

#### 2. 评价生成质量 (Review Generation)
综合考虑情感、情绪和主题相似性：

**公式**:
```
Review Generation = 1 - (情感误差 × 0.25 + 情绪误差 × 0.25 + 主题误差 × 0.5)
```

**子指标**:
- **情感误差**: 使用VADER情感分析器计算生成评价与真实评价的情感极性差异
- **情绪误差**: 使用RoBERTa情绪分类器计算情绪分布差异
- **主题误差**: 使用SentenceTransformer计算语义相似度

#### 3. 整体质量 (Overall Quality)
**公式**:
```
Overall Quality = (Preference Estimation + Review Generation) / 2
```

### 最终评分 (Final Score)
**公式**:
```
Final Score = ((Average Hit Rate + Overall Quality) / 2) × 100
```

## 数据集信息

- **数据集仓库**: https://huggingface.co/datasets/tsinghua-fib-lab/behavior-modeling-benchmark
- **分支**: main
- **支持模式**: test, inference

## 依赖要求

```python
numpy >= 1.26.4
scipy >= 1.13.0
nltk
transformers
sentence-transformers
torch
```

## 使用示例

```shell
asbench run --config <YOUR-CONFIG>.yml --agent <YOUR-AGENT>.py --mode test BehaviorModeling
asbench run --config <YOUR-CONFIG>.yml --agent <YOUR-AGENT>.py --mode inference BehaviorModeling
```

## 版本信息

- **版本**: 1.0.0
- **作者**: AgentSociety Team
- **标签**: behavior-modeling, recommendation, review-writing 