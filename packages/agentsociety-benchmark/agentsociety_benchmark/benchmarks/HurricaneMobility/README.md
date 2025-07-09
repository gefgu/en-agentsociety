# HurricaneMobility Benchmark

## Overview

The HurricaneMobility benchmark evaluates LLM agents' capabilities in generating mobility behavior during extreme weather events, using Hurricane Dorian as the context. This benchmark focuses on simulating user travel pattern changes before, during, and after hurricanes, testing agents' modeling capabilities for extreme event responses.

## Evaluation Task

### Extreme Weather Mobility Behavior Generation
- **Task Description**: Generate user mobility behavior patterns before, during, and after Hurricane Dorian based on real data
- **Input**: Hurricane information, user features, time phases (before/during/after)
- **Output**: User mobility behavior data, including:
  - Total Travel Times
  - Hourly Travel Times
  - Relative Changes

## Evaluation Process

### Data Preparation Phase
1. **Real Data Loading**: Load real mobility behavior data during Hurricane Dorian from dataset
2. **Agent Initialization**: Configure agent parameters and hurricane environment settings
3. **Task Distribution**: Generate corresponding mobility behavior tasks for different time phases

### Behavior Generation Phase
1. **Environment Perception**: Agent understands hurricane impact and transportation condition changes
2. **Risk Assessment**: Analyze travel risks in different time phases
3. **Behavior Generation**: Generate mobility patterns conforming to extreme weather conditions
4. **Data Output**: Output structured mobility behavior data

### Evaluation Phase
1. **Change Rate Comparison**: Compare change rates between generated and real data
2. **Distribution Similarity**: Evaluate similarity of hourly travel distributions
3. **Weighted Scoring**: Combine various metrics to obtain final score

## Evaluation Metrics

### 1. Change Rate Accuracy (Change Rate Score)

Evaluate the accuracy of change rates in generated data during and after hurricane relative to before hurricane.

**Formula**:
```
MAPE = (|Real Change Rate - Generated Change Rate| / |Real Change Rate|) × 100%
Change Rate Score = max(0, 100 - Average MAPE)
```

where:
- **During Hurricane Change Rate**: (During Travel Time - Before Travel Time) / Before Travel Time × 100%
- **After Hurricane Change Rate**: (After Travel Time - Before Travel Time) / Before Travel Time × 100%
- **Average MAPE**: (During MAPE + After MAPE) / 2

### 2. Distribution Similarity (Distribution Score)

Evaluate similarity between generated and real hourly travel distributions.

**Formula**:
```
Cosine Similarity = (A · B) / (||A|| × ||B||)
Distribution Score = max(0, Average Cosine Similarity × 100)
```

where:
- A, B: Normalized hourly travel distribution vectors
- Average Cosine Similarity: (Before Similarity + During Similarity + After Similarity) / 3

### 3. Final Score

**Formula**:
```
Final Score = Change Rate Score × 0.6 + Distribution Score × 0.4
```

**Weight Explanation**:
- Change Rate Score weight 60%: Directly measures hurricane impact accuracy
- Distribution Score weight 40%: Evaluates temporal distribution similarity of travel patterns

## Dataset Information

- **Dataset Repository**: https://huggingface.co/datasets/tsinghua-fib-lab/hurricane-mobility-generation-benchmark
- **Branch**: main
- **Supported Modes**: inference (test mode not supported)
- **Data Features**: Real mobility behavior data during Hurricane Dorian

## Dependencies

```python
numpy >= 1.26.4
```

## Usage Example

```shell
asbench run --config <YOUR-CONFIG-FILE>.yml --agent <YOUR-AGENT-FILE>.py --mode inference HurricaneMobility
```

## Output Data Format

```python
{
    "total_travel_times": [120, 85, 95],  # [Before, During, After] Total travel time (minutes)
    "hourly_travel_times": [
        [10, 15, 20, 25, 30, 35, 40, 35, 30, 25, 20, 15, 10, 5, 0, 0, 0, 0, 5, 10, 15, 20, 15, 10],  # Before 24-hour distribution
        [5, 8, 12, 15, 18, 20, 22, 20, 18, 15, 12, 8, 5, 2, 0, 0, 0, 0, 2, 5, 8, 12, 8, 5],  # During 24-hour distribution
        [8, 12, 16, 20, 24, 28, 32, 28, 24, 20, 16, 12, 8, 4, 0, 0, 0, 0, 4, 8, 12, 16, 12, 8]   # After 24-hour distribution
    ]
}
```

## Detailed Evaluation Metrics

Evaluation results also include the following detailed metrics:

```python
{
    "change_rate_score": 85.2,  # Change rate accuracy score
    "distribution_score": 78.9,  # Distribution similarity score
    "final_score": 82.7,  # Final weighted score
    "detailed_metrics": {
        "real_change_rates": {
            "during_vs_before": -29.2,  # Real during hurricane change rate (%)
            "after_vs_before": -20.8    # Real after hurricane change rate (%)
        },
        "generated_change_rates": {
            "during_vs_before": -31.5,  # Generated during hurricane change rate (%)
            "after_vs_before": -22.1    # Generated after hurricane change rate (%)
        },
        "change_rate_error": {
            "during_vs_before": 2.3,    # During hurricane change rate error
            "after_vs_before": 1.3      # After hurricane change rate error
        }
    }
}
```

## Version Information

- **Version**: 1.0.0
- **Author**: AgentSociety Team
- **Tags**: hurricane-mobility, extreme-weather 