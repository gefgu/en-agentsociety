# DailyMobility Benchmark

## Overview

The DailyMobility benchmark evaluates LLM agents' capabilities in daily mobility behavior generation based on Beijing users. This benchmark focuses on simulating real users' daily travel patterns, including key mobility features such as gyration radius, daily location numbers, intention sequences, and intention proportions.

## Evaluation Task

### Daily Mobility Behavior Generation
- **Task Description**: Generate daily mobility patterns that conform to real user behavior based on user characteristics and urban environment
- **Input**: User demographic features, city geographic information, time constraints
- **Output**: User daily mobility behavior data, including:
  - Gyration Radius
  - Daily Location Numbers
  - Intention Sequences
  - Intention Proportions

## Evaluation Process

### Data Preparation Phase
1. **Real Data Loading**: Load real mobility behavior data of Beijing users from dataset
2. **Agent Initialization**: Configure agent parameters and environment settings
3. **Task Distribution**: Generate corresponding mobility behavior tasks for each user

### Behavior Generation Phase
1. **User Feature Analysis**: Agent analyzes user demographic characteristics
2. **Environment Perception**: Understand city geographic layout and transportation network
3. **Behavior Generation**: Generate daily mobility patterns conforming to user characteristics
4. **Data Output**: Output structured mobility behavior data

### Evaluation Phase
1. **Distribution Comparison**: Compare generated data distribution with real data distribution
2. **JSD Calculation**: Calculate Jensen-Shannon divergence to evaluate distribution similarity
3. **Score Calculation**: Combine various metrics to obtain final score

## Evaluation Metrics

### Jensen-Shannon Divergence (JSD)

Jensen-Shannon divergence is used to measure the similarity between generated data distribution and real data distribution. Lower JSD values indicate more similar distributions.

**Formula**:
```
JSD(P||Q) = 0.5 × KL(P||M) + 0.5 × KL(Q||M)
```

where:
- P: Real data distribution
- Q: Generated data distribution
- M: (P + Q) / 2
- KL: Kullback-Leibler divergence

### Specific Evaluation Metrics

#### 1. Gyration Radius JSD
**Description**: Evaluate similarity between generated and real gyration radius distributions
**Formula**: `JSD(Real Gyration Radius Distribution || Generated Gyration Radius Distribution)`

#### 2. Daily Location Numbers JSD
**Description**: Evaluate similarity between generated and real daily location numbers distributions
**Formula**: `JSD(Real Location Numbers Distribution || Generated Location Numbers Distribution)`

#### 3. Intention Sequences JSD
**Description**: Evaluate similarity between generated and real intention sequences distributions
**Formula**: `JSD(Real Intention Sequences Distribution || Generated Intention Sequences Distribution)`

#### 4. Intention Proportions JSD
**Description**: Evaluate similarity between generated and real intention proportions distributions
**Formula**: `JSD(Real Intention Proportions Distribution || Generated Intention Proportions Distribution)`

### Final Score

**Formula**:
```
Final Score = ((1 - JSD_gyration + 1 - JSD_locations + 1 - JSD_sequences + 1 - JSD_proportions) / 4) × 100
```

**Explanation**:
- Each JSD metric is converted to similarity score: `1 - JSD`
- Four metrics are averaged with equal weights
- Final score ranges from 0-100, higher scores indicate better generation quality

## Dataset Information

- **Dataset Repository**: https://huggingface.co/datasets/tsinghua-fib-lab/daily-mobility-generation-benchmark
- **Branch**: main
- **Supported Modes**: inference (test mode not supported)
- **Data Features**: Beijing users' daily mobility behavior data

## Dependencies

```python
numpy >= 1.26.4
scipy >= 1.13.0
```

## Usage Example

```shell
asbench run --config <YOUR-CONFIG-FILE>.yml --agent <YOUR-AGENT-FILE>.py --mode inference DailyMobility
```

## Output Data Format

```python
{
    "gyration_radius": [2.5, 3.1, 1.8, ...],  # User gyration radius list
    "daily_location_numbers": [5, 7, 4, ...],  # Daily location numbers list
    "intention_sequences": [[1,2,3,1], [2,1,4,2], ...],  # Intention sequences list
    "intention_proportions": [[0.3,0.2,0.5], [0.4,0.3,0.3], ...]  # Intention proportions list
}
```

## Version Information

- **Version**: 1.0.0
- **Author**: AgentSociety Team
- **Tags**: mobility-generation 