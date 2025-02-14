# Spread of Inflammatory Messages

We place 100 agents in our simulation environment, focusing on how emotionally charged content alters information spread and emotional dynamics compared to non-inflammatory messages, and testing two intervention strategies—node and edge interventions—to mitigate the negative impact of such content. 

Codes are available at [Inflammatory Messages](https://github.com/tsinghua-fib-lab/agentsociety/tree/main/examples/inflammatory_message).

## Run the Codes

```bash
cd examples/inflammatory_message
# control group
python control.py
# emotional message
python emotional.py
# interception: edge mode
python edge_intercept.py
# interception: node mode
python node_intercept.py
```

## Step-by-Step Code Explanation

## Tool Functions

```python
async def gather_memory(simulation: AgentSimulation):
    print("gather memory")
    citizen_uuids = await simulation.filter(types=[SocietyAgent])
    chat_histories = await simulation.gather("chat_histories", citizen_uuids)
    memories = await simulation.gather("stream_memory", citizen_uuids)
    with open(f"chat_histories.json", "w", encoding="utf-8") as f:
        json.dump(chat_histories, f, ensure_ascii=False, indent=2)
    with open(f"memories.json", "w", encoding="utf-8") as f:
        json.dump(memories, f, ensure_ascii=False, indent=2)


async def update_chat_histories(simulation: AgentSimulation):
    citizen_uuids = await simulation.filter(types=[SocietyAgent])
    selected_citizen_uuids = random.sample(citizen_uuids, k=3)
    chat_histories = await simulation.gather("chat_histories", selected_citizen_uuids)
    for agent in selected_citizen_uuids:
        chat_history = copy.deepcopy(chat_histories[1][agent])
        for chat in chat_history.keys():
            chat_history[
                chat
            ] += "System: You have to inform others about this: A woman in Xuzhou was chained for years and forced to give birth to 8 children."
        await simulation.update(agent, "chat_histories", chat_history)
```

- `gather_memory` gathers chat histories and stream memory for each agent.
- `update_chat_histories` randomly selects 3 citizen and give them the message in specific way. In control group, it is described in a rational way.

## `control.py`

The control group. No intervention is applied.

### Configuration

```python
sim_config = (
    SimConfig()
    .SetLLMRequest(
        request_type=LLMRequestType.ZhipuAI, api_key="YOUR-API-KEY", model="GLM-4-Flash"
    )
    .SetSimulatorRequest(min_step_time=50)
    .SetMQTT(server="mqtt.example.com", username="user", port=1883, password="pass")
    # change to your file path
    .SetMapRequest(file_path="map.pb")
    # .SetAvro(path="./__avro", enabled=True)
)
exp_config = (
    ExpConfig(exp_name="social_control", llm_semaphore=200, logging_level=logging.INFO)
    .SetAgentConfig(number_of_citizen=100, group_size=50)
    .SetWorkFlow(
        [
            WorkflowStep(
                type=WorkflowType.INTERVENE,
                func=update_chat_histories,
                description="update chat histories",
            ),
            WorkflowStep(type=WorkflowType.RUN, days=5),
            WorkflowStep(
                type=WorkflowType.FUNCTION,
                func=gather_memory,
                description="gather memories to support analysis",
            ),
        ]
    )
)
```
Initialize 100 agents with `number_of_citizen=100`. The overall workflow contains three steps.
- Step1: utilize `update_chat_histories` to initially send messages to randomly selected agents.
- Step2: simulate for 5 days, providing enough time for agents to chat with each other.
- Step3: utilize `gather_memory` to gather the chatting histories and memories of all agents after 5 simulation days.

### Main Function

```python
async def main():
    llm_log_lists, mqtt_log_lists, simulator_log_lists, agent_time_log_lists = (
        await AgentSimulation.run_from_config(exp_config, sim_config)
    )
    with open(f"social_control_llm_log_lists.json", "w", encoding="utf-8") as f:
        json.dump(llm_log_lists, f, ensure_ascii=False, indent=2)
    with open(f"social_control_mqtt_log_lists.json", "w", encoding="utf-8") as f:
        json.dump(mqtt_log_lists, f, ensure_ascii=False, indent=2)
    with open(f"social_control_simulator_log_lists.json", "w", encoding="utf-8") as f:
        json.dump(simulator_log_lists, f, ensure_ascii=False, indent=2)
    with open(f"social_control_agent_time_log_lists.json", "w", encoding="utf-8") as f:
        json.dump(agent_time_log_lists, f, ensure_ascii=False, indent=2)
    ray.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
```

`main` perform the simulation with configs defined above, and collect the log list of each framework part.

## `emotional.py`

The experiment group. The message is described in an emotional way.

### Configuration

```python
sim_config = (
    SimConfig()
    .SetLLMRequest(
        request_type=LLMRequestType.ZhipuAI, api_key="YOUR-API-KEY", model="GLM-4-Flash"
    )
    .SetSimulatorRequest(min_step_time=50)
    .SetMQTT(server="mqtt.example.com", username="user", port=1883, password="pass")
    # change to your file path
    .SetMapRequest(file_path="map.pb")
    # .SetAvro(path='./__avro', enabled=True)
)
exp_config = (
    ExpConfig(
        exp_name="social_experiment", llm_semaphore=200, logging_level=logging.INFO
    )
    .SetAgentConfig(number_of_citizen=100, group_size=50)
    .SetWorkFlow(
        [
            WorkflowStep(
                type=WorkflowType.INTERVENE,
                func=update_chat_histories,
                description="update chat histories",
            ),
            WorkflowStep(type=WorkflowType.RUN, days=5),
            WorkflowStep(
                type=WorkflowType.FUNCTION,
                func=gather_memory,
                description="gather memories to support analysis",
            ),
        ]
    )
)
```
Initialize 100 agents with `number_of_citizen=100`. The overall workflow contains three steps.
- Step1: utilize `update_chat_histories` to initially send messages to randomly selected agents.
- Step2: simulate for 5 days, providing enough time for agents to chat with each other.
- Step3: utilize `gather_memory` to gather the chatting histories and memories of all agents after 5 simulation days.

### Main Function

```python
async def main():
    llm_log_lists, mqtt_log_lists, simulator_log_lists, agent_time_log_lists = (
        await AgentSimulation.run_from_config(exp_config, sim_config)
    )
    with open(f"social_experiment_llm_log_lists.json", "w", encoding="utf-8") as f:
        json.dump(llm_log_lists, f, ensure_ascii=False, indent=2)
    with open(f"social_experiment_mqtt_log_lists.json", "w", encoding="utf-8") as f:
        json.dump(mqtt_log_lists, f, ensure_ascii=False, indent=2)
    with open(
        f"social_experiment_simulator_log_lists.json", "w", encoding="utf-8"
    ) as f:
        json.dump(simulator_log_lists, f, ensure_ascii=False, indent=2)
    with open(
        f"social_experiment_agent_time_log_lists.json", "w", encoding="utf-8"
    ) as f:
        json.dump(agent_time_log_lists, f, ensure_ascii=False, indent=2)
    ray.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
```

`main` perform the simulation with configs defined above, and collect the log list of each framework part.

## `edge_intercept.py`

Edge mode intervention is applied. If a sender exceeds the maximum number of prohibited attempts to send messages to a specific recipient, the system will prevent this sender from sending any further messages to that particular recipient. 

### Configuration

```python
sim_config = (
    SimConfig()
    .SetLLMRequest(
        request_type=LLMRequestType.ZhipuAI, api_key="YOUR-API-KEY", model="GLM-4-Flash"
    )
    .SetSimulatorRequest(min_step_time=50)
    .SetMQTT(server="mqtt.example.com", username="user", port=1883, password="pass")
    # change to your file path
    .SetMapRequest(file_path="map.pb")
    # .SetAvro(path='./__avro', enabled=True)
)
exp_config = (
    ExpConfig(exp_name="social_edge", llm_semaphore=200, logging_level=logging.INFO)
    .SetAgentConfig(
        number_of_citizen=100,
        group_size=50,
    )
    .SetMessageIntercept(
        message_interceptor_blocks=[EdgeMessageBlock()],
        message_listener=MessageBlockListener(),
    )
    .SetWorkFlow(
        [
            WorkflowStep(
                type=WorkflowType.INTERVENE,
                func=update_chat_histories,
                description="update chat histories",
            ),
            WorkflowStep(type=WorkflowType.RUN, days=5),
            WorkflowStep(
                type=WorkflowType.FUNCTION,
                func=gather_memory,
                description="gather memories to support analysis",
            ),
        ]
    )
)
```

Message interceptor are set to `EdgeMessageBlock` with `SetMessageIntercept`. It will continually check the messages from the senders, and if it is offensive (judged by LLM), it counts for one violation.

Initialize 100 agents with `number_of_citizen=100`. The overall workflow contains three steps.
- Step1: utilize `update_chat_histories` to initially send messages to randomly selected agents.
- Step2: simulate for 5 days, providing enough time for agents to chat with each other.
- Step3: utilize `gather_memory` to gather the chatting histories and memories of all agents after 5 simulation days.

### Main Function

```python
async def main():
    llm_log_lists, mqtt_log_lists, simulator_log_lists, agent_time_log_lists = (
        await AgentSimulation.run_from_config(exp_config, sim_config)
    )
    with open(f"social_control_llm_log_lists.json", "w", encoding="utf-8") as f:
        json.dump(llm_log_lists, f, ensure_ascii=False, indent=2)
    with open(f"social_control_mqtt_log_lists.json", "w", encoding="utf-8") as f:
        json.dump(mqtt_log_lists, f, ensure_ascii=False, indent=2)
    with open(f"social_control_simulator_log_lists.json", "w", encoding="utf-8") as f:
        json.dump(simulator_log_lists, f, ensure_ascii=False, indent=2)
    with open(f"social_control_agent_time_log_lists.json", "w", encoding="utf-8") as f:
        json.dump(agent_time_log_lists, f, ensure_ascii=False, indent=2)
    ray.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
```

`main` perform the simulation with configs defined above, and collect the log list of each framework part.

## `node_intercept.py`

Node mode intervention is applied. If prohibitions are exceeded, the sender will be banned from sending messages to anyone. 

### Configuration

```python
sim_config = (
    SimConfig()
    .SetLLMRequest(
        request_type=LLMRequestType.ZhipuAI, api_key="YOUR-API-KEY", model="GLM-4-Flash"
    )
    .SetSimulatorRequest(min_step_time=50)
    .SetMQTT(server="mqtt.example.com", username="user", port=1883, password="pass")
    # change to your file path
    .SetMapRequest(file_path="map.pb")
    # .SetAvro(path='./__avro', enabled=True)
)
exp_config = (
    ExpConfig(exp_name="social_node", llm_semaphore=200, logging_level=logging.INFO)
    .SetAgentConfig(
        number_of_citizen=100,
        group_size=50,
    )
    .SetMessageIntercept(
        message_interceptor_blocks=[PointMessageBlock()],
        message_listener=MessageBlockListener(),
    )
    .SetWorkFlow(
        [
            WorkflowStep(
                type=WorkflowType.INTERVENE,
                func=update_chat_histories,
                description="update chat histories",
            ),
            WorkflowStep(type=WorkflowType.RUN, days=5),
            WorkflowStep(
                type=WorkflowType.FUNCTION,
                func=gather_memory,
                description="gather memories to support analysis",
            ),
        ]
    )
)
```

Message interceptor are set to `PointMessageBlock` with `SetMessageIntercept`. It will continually check the messages from the senders, and if it is offensive (judged by LLM), it counts for one violation.

Initialize 100 agents with `number_of_citizen=100`. The overall workflow contains three steps.
- Step1: utilize `update_chat_histories` to initially send messages to randomly selected agents.
- Step2: simulate for 5 days, providing enough time for agents to chat with each other.
- Step3: utilize `gather_memory` to gather the chatting histories and memories of all agents after 5 simulation days.

### Main Function

```python
async def main():
    llm_log_lists, mqtt_log_lists, simulator_log_lists, agent_time_log_lists = (
        await AgentSimulation.run_from_config(exp_config, sim_config)
    )
    with open(f"social_control_llm_log_lists.json", "w", encoding="utf-8") as f:
        json.dump(llm_log_lists, f, ensure_ascii=False, indent=2)
    with open(f"social_control_mqtt_log_lists.json", "w", encoding="utf-8") as f:
        json.dump(mqtt_log_lists, f, ensure_ascii=False, indent=2)
    with open(f"social_control_simulator_log_lists.json", "w", encoding="utf-8") as f:
        json.dump(simulator_log_lists, f, ensure_ascii=False, indent=2)
    with open(f"social_control_agent_time_log_lists.json", "w", encoding="utf-8") as f:
        json.dump(agent_time_log_lists, f, ensure_ascii=False, indent=2)
    ray.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
```

`main` perform the simulation with configs defined above, and collect the log list of each framework part.
