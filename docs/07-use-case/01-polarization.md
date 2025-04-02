# Polarization

We simulate agent discussions on immigration policy to investigate polarization, comparing a control group (no intervention) with two treatments—exposure to aligned messages (echo chambers) and opposing messages (backfiring effects)—to analyze their impact on deepening opinion divisions.

Codes are available at [Polarization](https://github.com/tsinghua-fib-lab/agentsociety/tree/main/examples/polarization).

## Background

Opinion polarization refers to the gradual divergence of viewpoints within social groups, leading to irreconcilable opposing factions. To investigate this phenomenon, we simulate the opinion evolution of social agents using gun control policy as the focal issue. The experiment comprises a control group and two intervention groups. In the control group, agents autonomously update their views through peer discussions without external interference, reflecting natural social interactions. The homogeneous information group mimics the "echo chamber" effect by exclusively exposing agents to stance-consistent information. Conversely, the opposing information group subjects agents solely to counter-attitudinal information to examine the impact of conflicting viewpoints. This tripartite design enables systematic exploration of how distinct information ecosystems influence polarization dynamics.

## Reproducing Phenomena with Our Framework 

### Initializing Agents' Attitudes

The first step involves initializing agents with initial attitudes towards gun control. This is achieved through an initialization function that randomly assigns each agent either a supportive or opposing stance. 

#### Control Group

The basic initialization function for control group.

```python
async def update_attitude(simulation: AgentSociety):
    citizen_ids = await simulation.filter(types=(SocietyAgent,))
    for agent_id in citizen_ids:
        if random.random() < 0.5:
            await simulation.update(
                [agent_id], "attitude", {"Whether to support stronger gun control?": 3}
            )
        else:
            await simulation.update(
                [agent_id], "attitude", {"Whether to support stronger gun control?": 7}
            )
    attitudes = await simulation.gather("attitude", citizen_ids)
    with open(f"exp1/attitudes_initial.json", "w", encoding="utf-8") as f:
        json.dump(attitudes, f, ensure_ascii=False, indent=2)
```

#### Experiment Group: Echo Chamber

For the Echo Chamber experiment, during the attitude initialization phase, we ensure that agents who are inclined to persuade their friends to support a positive stance (in favor of stronger gun control) are connected as friends with other agents who hold a positive view. Similarly, agents who aim to persuade their friends towards a negative stance (against stronger gun control) are linked with friends who also oppose it. 

In this context, being "friends" means that these agents can engage in conversations to influence each other's viewpoints.

```diff
async def update_attitude(simulation: AgentSociety):
+   agree_agent_id = await simulation.filter(types=(AgreeAgent,))
+   agree_agent_id = agree_agent_id[0]
+   disagree_agent_id = await simulation.filter(types=(DisagreeAgent,))
+   disagree_agent_id = disagree_agent_id[0]
+   agree_friends = []
+   disagree_friends = []
    for agent_id in citizen_ids:
        if random.random() < 0.5:
            await simulation.update(
                [agent_id], "attitude", {"Whether to support stronger gun control?": 3}
            )
+           disagree_friends.append(agent_id)
        else:
            await simulation.update(
                [agent_id], "attitude", {"Whether to support stronger gun control?": 7}
            )
+           agree_friends.append(agent_id)
        # remove original social network
        await simulation.update([agent_id], "friends", [])
+       await simulation.update([agree_agent_id], "friends", agree_friends)
+       await simulation.update([disagree_agent_id], "friends", disagree_friends)
    attitudes = await simulation.gather("attitude", citizen_ids)
    with open(f"exp2/attitudes_initial.json", "w", encoding="utf-8") as f:
        json.dump(attitudes, f, ensure_ascii=False, indent=2)
```

#### Experiment Group: Back Firing

For the Back Firing experiment, during the attitude initialization phase, we connect agents who are inclined to persuade their friends to support a positive stance (such as stronger gun control) as friends with agents who hold a negative stance. Similarly, agents who aim to persuade their friends towards a negative stance (opposing stronger gun control) are connected as friends with agents who hold a positive stance.

```diff
async def update_attitude(simulation: AgentSociety):
+   agree_agent_id = await simulation.filter(types=(AgreeAgent,))
+   agree_agent_id = agree_agent_id[0]
+   disagree_agent_id = await simulation.filter(types=(DisagreeAgent,))
+   disagree_agent_id = disagree_agent_id[0]
+   agree_friends = []
+   disagree_friends = []
    for agent_id in citizen_ids:
        if random.random() < 0.5:
            await simulation.update(
                [agent_id], "attitude", {"Whether to support stronger gun control?": 3}
            )
+           agree_friends.append(agent_id)
        else:
            await simulation.update(
                [agent_id], "attitude", {"Whether to support stronger gun control?": 7}
            )
+           disagree_friends.append(agent_id)
        # remove original social network
        await simulation.update([agent_id], "friends", [])
+       await simulation.update([agree_agent_id], "friends", agree_friends)
+       await simulation.update([disagree_agent_id], "friends", disagree_friends)
    attitudes = await simulation.gather("attitude", citizen_ids)
    with open(f"exp2/attitudes_initial.json", "w", encoding="utf-8") as f:
        json.dump(attitudes, f, ensure_ascii=False, indent=2)
```

#### Add Init-Functions to Your Workflow

To use these functions, you need to add them in your config file.

```python
WorkflowStepConfig(
    type=WorkflowType.FUNCTION,
    func=update_attitude,
    description="update attitude",
),
```
### Collecting Data

After allowing time for opinions to evolve, we collect data on agents' final attitudes. This involves gathering updated attitudes and recording any shifts from their original positions:

```python
async def gather_attitude(simulation: AgentSociety):
    print("gather attitude")
    citizen_ids = await simulation.filter(types=(SocietyAgent,))
    attitudes = await simulation.gather("attitude", citizen_ids)

    with open(f"exp1/attitudes_final.json", "w", encoding="utf-8") as f:
        json.dump(attitudes, f, ensure_ascii=False, indent=2)

    chat_histories = await simulation.gather("chat_histories", citizen_ids)
    with open(f"exp1/chat_histories.json", "w", encoding="utf-8") as f:
        json.dump(chat_histories, f, ensure_ascii=False, indent=2)
```

Similar to initializing the attitudes, you need to add the collecting function in your config file.

```python
WorkflowStepConfig(
    type=WorkflowType.FUNCTION,
    func=gather_attitude,
    description="gather attitude",
),
```

### Run the Codes

```bash
cd examples/polarization
# control group
python control.py
# echo chambers
python echo_chamber.py
# backfiring effects
python back_firing.py
```

## Experiment Result

![PolarizationResult](../_static/04-polarization-result.png)

As shown in the figure above, opinion dynamics under the three experimental settings exhibit distinct patterns regarding the gun control policy issue. In the control group, where agents engaged in free discussions without external intervention, 39% of agents became more polarized after interactions, while 33% adopted more moderate stances. In contrast, the homogeneous information group demonstrated significantly amplified polarization, with 52% of agents developing more extreme views. This aligns with real-world "echo chamber effects," suggesting that excessive interactions with like-minded individuals may intensify opinion divergence. Notably, the opposing information group revealed a striking mitigation of polarization: 89% of agents shifted toward moderate positions, with 11% even adopting opposing viewpoints. These results indicate that exposure to counter-attitudinal content can effectively reduce polarization, potentially serving as a viable strategy to counteract ideological fragmentation. The findings underscore the critical role of information ecosystems in shaping collective opinion trajectories.
