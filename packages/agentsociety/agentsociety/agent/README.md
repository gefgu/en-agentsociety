## Dispatcher Prompt (Block Routing)

`BlockDispatcher` uses a prompt template to decide which block should handle the current step.

- Default source: `agent/dispatcher.py` (`DISPATCHER_PROMPT`)
- Runtime override: `SocietyAgentConfig.block_dispatch_prompt` in `cityagent/sharing_params.py`

### Current default prompt (in code)

```text
Based on the task information (which describes the needs of the user), select the most appropriate block to handle the task.
Each block has its specific functionality as described in the function schema.

Task information:
${context.current_intention}
```

### Reconstructed context-rich prompt template

Use this as `block_dispatch_prompt` when you want the dispatcher to consider full state (time, emotion, location, weather, etc.):

```text
You are a block routing system for an autonomous agent.
Select exactly one block from the provided function schema.
Route to the block that is most appropriate for the current context and immediate intention.
If no block is suitable, select `no_suitable_block`.

Current Context
- Time: ${context.current_time}
- Need: ${context.current_need}
- Intention: ${context.current_intention}
- Emotion: ${context.current_emotion}
- Thought: ${context.current_thought}
- Location: ${context.current_location}
- Plan target: ${context.plan_target}
- Area information: ${context.area_information}
- Weather: ${context.weather}
- Temperature: ${context.temperature}
- Other information: ${context.other_information}

Routing Rules
1. Prioritize `current_intention` and `current_need`.
2. Use emotion/thought as secondary signals for behavioral nuance.
3. Use time/location/weather/temperature to disambiguate action feasibility.
4. Return a concise reason grounded in the context.
5. Do not invent unavailable context values.
```