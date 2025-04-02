# Universal Basic Income (UBI)

Our experiment simulates the impact of a Universal Basic Income (UBI) policy, granting each agent $1,000 monthly, on the socio-economic environment of Texas, USA, comparing macroeconomic outcomes such as real GDP and consumption levels with and without UBI intervention.

Codes are available at [UBI](https://github.com/tsinghua-fib-lab/agentsociety/tree/main/examples/UBI).

## Background

Universal Basic Income (UBI) has emerged as a prominent policy tool for alleviating poverty, enhancing economic stability, and improving social welfare, despite ongoing debates over its financial feasibility and broader economic implications. As a mechanism to address income inequality and strengthen social safety nets, UBI has garnered significant research attention. This experiment evaluates the potential effects of UBI by simulating its implementation within a controlled framework, focusing on shifts in individual economic behaviors—such as consumption patterns, savings rates, and labor market participation—as well as macroeconomic outcomes. The study employs a comparative design with two groups: a control group, where agents operate under existing economic conditions without UBI, and an intervention group, where agents receive unconditional monthly payments of $1,000. Leveraging demographic distribution data from UBI pilot regions, including Texas in the United States, the simulation analyzes economic and social indicators across both groups to assess how UBI influences individual decision-making and aggregate economic dynamics. By comparing simulated outcomes with empirical findings from real-world UBI trials, the experiment aims to validate theoretical models and deepen understanding of UBI's practical viability as a socioeconomic policy.

## Reproducing Phenomena with Our Framework  

### Simulating UBI Economic Dynamics  

#### Workflow Design  

```python
config = Config(
    ...
    exp=ExpConfig(
        name="ubi_experiment",
        workflow=[
            WorkflowStepConfig(
                type=WorkflowType.RUN,
                days=10,
            )
        ],
        environment=EnvironmentConfig(
            start_tick=6 * 60 * 60,
            total_tick=18 * 60 * 60,
        ),
        metric_extractors=[
            MetricExtractorConfig(
                type=MetricType.FUNCTION, func=economy_metric, step_interval=1
            ),
            MetricExtractorConfig(
                type=MetricType.FUNCTION, func=gather_ubi_opinions, step_interval=12
            ),
        ],
    ),
)
```

### Data Collection and Metrics

#### UBI Opinions

The `gather_ubi_opinions` method collects qualitative sentiment data about UBI and store it locally with `pickle`.

```python
async def gather_ubi_opinions(simulation: AgentSociety):
    citizen_agents = await simulation.filter(types=[SocietyAgent])
    opinions = await simulation.gather("ubi_opinion", citizen_agents)
    with open("opinions.pkl", "wb") as f:
        pkl.dump(opinions, f)
```

#### Economy Metrics

The `economy_metric` monitors macroeconomic indicators  through `'prices', 'working_hours', 'depression', 'consumption_currency', 'income_currency'`.

```python
# Metric extraction configuration
config = Config(
    ...
    exp=ExpConfig(
        metric_extractors=[
            MetricExtractorConfig(
                type=MetricType.FUNCTION, func=economy_metric, step_interval=1
            ),
            MetricExtractorConfig(
                type=MetricType.FUNCTION, func=gather_ubi_opinions, step_interval=12
            ),
        ],
    ),
```

### Run the Codes

```bash
cd examples/UBI
python main.py
```

## Experiment Result

![UbiResult](../_static/04-ubi-result.png)

The experimental results revealed that the simulated economic system gradually stabilized over time, with diminishing fluctuations in real GDP and agent consumption levels. Following the implementation of a UBI policy at step 96, subsequent analysis of economic and social indicators over 24 steps demonstrated that UBI significantly elevated consumption levels and reduced depressive symptoms, as measured by CES-D scale assessments. These outcomes mirrored the observed effects of Texas' real-world UBI initiatives, validating the simulation's alignment with empirical socioeconomic dynamics. 

Agent interviews further uncovered nuanced perceptions of UBI, with its perceived impacts closely tied to interest rates, long-term welfare benefits, savings behaviors, and access to essential goods—factors consistent with public discourse surrounding UBI in reality. The findings concurrently substantiate UBI's dual efficacy in stimulating economic activity and enhancing psychological well-being, while also confirming the simulation platform's utility as a cost-effective experimental environment for policy prototyping and impact assessment.
