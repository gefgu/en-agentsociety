# BehaviorModeling Benchmark

## Overview

The BehaviorModeling benchmark evaluates LLM agents' capabilities in user behavior modeling, including two core tasks: item recommendation and review generation. This benchmark supports both test and inference modes, providing a comprehensive evaluation framework for agent behavior modeling research.

## Evaluation Tasks

### 1. Item Recommendation Task
- **Task Description**: Recommend the most suitable items to users based on their historical behavior and preferences
- **Input**: User ID, candidate item category, candidate item list
- **Output**: Ranked item list by recommendation priority

### 2. Review Generation Task
- **Task Description**: Simulate user review generation for specific items, including ratings and review text
- **Input**: User ID, item ID, item information
- **Output**: Star rating (1-5 stars) and review text

## Evaluation Process

### Test Mode
1. **Data Preparation**: Load test dataset containing user behavior history and ground truth labels
2. **Task Execution**: Agent processes recommendation and review generation tasks
3. **Result Evaluation**: Calculate various evaluation metrics
4. **Score Calculation**: Combine recommendation accuracy and review quality for final score

### Inference Mode
1. **Inference Execution**: Agent performs reasoning based on given context
2. **Result Validation**: Compare with ground truth labels
3. **Metric Collection**: Collecting results for evaluation to a .pkl file

## Evaluation Metrics

### Recommendation Metrics

#### Hit Rate@N
Calculate the proportion of samples where the ground truth item appears in the top-N recommendations:

**Formula**:
```
HR@N = (Number of samples with ground truth item in top-N recommendations) / (Total number of samples)
```

**Specific Metrics**:
- **Top-1 Hit Rate**: HR@1, hit rate for the first item in recommendation list
- **Top-3 Hit Rate**: HR@3, hit rate for top three items in recommendation list
- **Top-5 Hit Rate**: HR@5, hit rate for top five items in recommendation list
- **Average Hit Rate**: (HR@1 + HR@3 + HR@5) / 3

### Simulation Metrics

#### 1. Preference Estimation Accuracy
Based on star rating accuracy:

**Formula**:
```
Preference Estimation = 1 - (Average Star Rating Error / 5)
```

where Star Rating Error = |Predicted Rating - Ground Truth Rating| / 5

#### 2. Review Generation Quality
Comprehensive evaluation considering sentiment, emotion, and topic similarity:

**Formula**:
```
Review Generation = 1 - (Sentiment Error × 0.25 + Emotion Error × 0.25 + Topic Error × 0.5)
```

**Sub-metrics**:
- **Sentiment Error**: Calculate sentiment polarity difference between generated and ground truth reviews using VADER sentiment analyzer
- **Emotion Error**: Calculate emotion distribution difference using RoBERTa emotion classifier
- **Topic Error**: Calculate semantic similarity using SentenceTransformer

#### 3. Overall Quality
**Formula**:
```
Overall Quality = (Preference Estimation + Review Generation) / 2
```

### Final Score
**Formula**:
```
Final Score = ((Average Hit Rate + Overall Quality) / 2) × 100
```

## Dataset Information

- **Dataset Repository**: https://huggingface.co/datasets/tsinghua-fib-lab/behavior-modeling-benchmark
- **Branch**: main
- **Supported Modes**: test, inference

## Dependencies

```python
numpy >= 1.26.4
scipy >= 1.13.0
nltk
transformers
sentence-transformers
torch
```

## Usage Example

```shell
asbench run --config <YOUR-CONFIG>.yml --agent <YOUR-AGENT>.py --mode test BehaviorModeling
asbench run --config <YOUR-CONFIG>.yml --agent <YOUR-AGENT>.py --mode inference BehaviorModeling
```
```

## Version Information

- **Version**: 1.0.0
- **Author**: AgentSociety Team
- **Tags**: behavior-modeling, recommendation, review-writing 