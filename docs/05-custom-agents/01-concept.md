# Concepts

In our framework, agents are autonomous entities that simulate realistic behaviors within a virtual environment. 
These agents interact with each other, reason about their surroundings, etc.

## Agent Identity and Types

At their core, agents have distinct identities represented by unique identifiers and names. Currently we support two primary agent types:

- **Citizen Agents**: Represent individuals within the society. They have homes, workplaces, personal attributes, and can navigate through the urban environment.

- **Institution Agents**: Represent organizations such as businesses, government bodies, and service providers. They typically have fixed locations and interact with citizens and other institutions.

Each agent type serves different roles in the simulation ecosystem, with specialized behaviors and attributes tailored to their function.

## Cognitive Architecture

![](../_static/social-agent-architecture.png)

Agents in our framework possess a sophisticated cognitive architecture that enables them to:

1. **Perceive**: Gather information about their environment and other agents
2. **Remember**: Store and retrieve relevant experiences and knowledge
3. **Reason**: Process information and make decisions based on goals and constraints
4. **Communicate**: Exchange information and intentions with other agents
5. **Act**: Execute behaviors that affect the simulation state

The cognitive flow typically involves processing current perceptions against existing memories to determine appropriate actions, which are then executed through the simulation interface.

## Integration with Language Models

```{admonition} Note
:class: note
Refer to [Integration with Language Models](./02-agent-tools.md#llm-client) for details.
```

A key innovation in our framework is the integration of Large Language Models (LLMs) that power agent reasoning. This integration enables:

- **Natural Language Understanding**: Processing and generating human-like text
- **Context-Aware Reasoning**: Making decisions informed by historical context
- **Adaptive Behaviors**: Evolving responses based on changing circumstances
- **Realistic Interactions**: Creating believable dialogue between agents

The LLM integration serves as the "brain" of the agent, allowing for complex decision-making processes beyond traditional rule-based approaches.

## Simulation Binding

Agents don't exist in isolation—they're integrated with broader simulation systems:

- **Urban Environment**: Agents are bound to a spatial simulation representing cities
- **Economic System**: Agents participate in economic activities including employment, spending, and wealth accumulation
- **Social Networks**: Agents form relationships and communities that influence their behaviors

This binding process establishes the agent's presence in the simulation world and enables them to affect and be affected by their environment.

## Memory Systems

```{admonition} Note
:class: note
Refer to [Memory Systems](./03-memory.md) for details.
```

Agents maintain two primary types of memory:

- **Status Memory**: Represents persistent attributes and relatively stable information about the agent. This includes demographic details, preferences, affiliations, and long-term goals.

- **Stream Memory**: Captures the agent's experiences, interactions, and observations over time. This episodic memory allows agents to recall and learn from past events when making future decisions.

Memory systems are designed to be searchable based on relevance, enabling agents to retrieve contextually appropriate information when responding to situations.

## Communication Framework

Agents communicate through a message-passing system that supports:

- **Direct Messages**: One-to-one communications between agents
- **Surveys & Interviews**: Mechanisms for gathering structured information from agents. Check [Surveys & Interviews](../04-experiment-design/01-survey-and-interview.md) for details.
- **Thought Sharing**: Recording internal reasoning processes for analysis. *TODO*

The communication framework includes capabilities for message interception, which allows for monitoring, filtering, or modifying messages between agents for research or control purposes.

## Integrate Blocks into your Design

```{admonition} Note
:class: note
Refer to [agent-block-action architecture](../02-version-1.5/02.agent-block-action architecture.md) for details.
```

Agent behaviors are organized using a modular "Block" design pattern (optional):

- **Blocks**: Self-contained units of functionality that encapsulate specific agent capabilities
- **Hierarchical Structure**: Blocks can contain other blocks, creating a composable architecture
- **Configurable Parameters**: Each block exposes parameters that can be adjusted to tune behavior
- **Event-Driven Execution**: Blocks can be triggered based on specific conditions or events

This modular design allows researchers to create complex behaviors by combining simpler components, promoting code reuse and systematic experimentation with agent designs.

### Block System Architecture

The Block system provides a flexible way to extend agent capabilities:

1. **Community Blocks**: You can leverage pre-built blocks from the community to quickly add capabilities to your agents
2. **Custom Blocks**: Design and implement your own blocks to create specialized agent behaviors, you can refer to [Implement Custom Blocks](./04-agent-customization.md#Implementation-Example) for details.
3. **Block Dispatcher**: Coordinate block execution through a central dispatcher that manages block invocation

By using the Block architecture, you can:
- Easily share and reuse agent capabilities across different projects
- Create complex agent behaviors by combining simpler functional components
- Extend agent functionality without modifying core agent logic
- Contribute your custom blocks back to the community
