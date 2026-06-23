<div style="text-align: center; background-color: white; padding: 20px; border-radius: 30px;">
  <img src="./static/agentsociety_logo.png" alt="AgentSociety Logo" width="200" style="display: block; margin: 0 auto;">
  <h1 style="color: black; margin: 0; font-size: 3em;">En-AgentSociety: Enhanced AgentSociety</h1>
</div>


# 🚀 En-AgentSociety
![License](https://img.shields.io/badge/license-Apache%202.0-blue) &ensp;
[![Online Documentation](https://img.shields.io/badge/docs-online-blue)](https://en-agentsociety.readthedocs.io/en/latest/) &ensp;


AgentSociety is an advanced framework specifically designed for building agents in urban simulation environments. With AgentSociety, you can easily create and manage agents, enabling complex urban scenarios to be modeled and simulated efficiently.

## En-AgentSociety: Fork Contributions

**En-AgentSociety** is a fork of [AgentSociety](https://github.com/tsinghua-fib-lab/agentsociety) by FIB Lab, Tsinghua University,
developed by [Gustavo H. Santos](https://github.com/gefgu). The following features and improvements were added:

- **Checkpoint & Resume System** — Full simulation state serialization/deserialization, allowing interrupted experiments to be resumed from the last saved step. Includes checkpoint snapshots in both ClickHouse and DuckDB backends, config mismatch detection on resume, and guards against resuming already-finished experiments.
- **Pydantic-based Prompt System** — Replaced all TOML prompt files with typed `BasePrompt` Pydantic classes. Prompts are now versioned Python objects with schema validation, making them easier to maintain, test, and evolve.
- **DuckDB Database Backend** — A local alternative to ClickHouse (no server required), with full support for the resume path. Enables development and offline testing without external infrastructure.
- **Qdrant Semantic Cache** — Vector-based LLM response caching with championship selection logic. Includes a batched `EmbedActor` to reduce ONNX overhead, cache shadow-mode metrics, and persistence across runs.
- **LLM Load Balancing & Actor Pattern** — Refactored LLM layer into a distributed actor model with per-model routing and error handling for providers including Mistral.
- **Simulation Robustness** — Retry logic for malformed LLM outputs, SQLite corruption detection and recovery, per-step error isolation to prevent a single agent failure from crashing the simulation, and configurable resume-mismatch actions.
- **Mobility Block Refactoring** — Split into focused modules (`move_block`, `place_selection_block`, `transport_mode_selection_block`) with improved POI filtering, area selection, and null-result handling.

The paper for the original project is available at [arXiv](https://arxiv.org/abs/2502.08691):

```
@article{piao2025agentsociety,
  title={AgentSociety: Large-Scale Simulation of LLM-Driven Generative Agents Advances Understanding of Human Behaviors and Society},
  author={Piao, Jinghua and Yan, Yuwei and Zhang, Jun and Li, Nian and Yan, Junbo and Lan, Xiaochong and Lu, Zhihong and Zheng, Zhiheng and Wang, Jing Yi and Zhou, Di and others},
  journal={arXiv preprint arXiv:2502.08691},
  year={2025}
}
```

## 🌟 Features
- **Mind-Behavior Coupling**: Integrates LLMs' planning, memory, and reasoning capabilities to generate realistic behaviors or uses established theories like Maslow's Hierarchy of Needs and Theory of Planned Behavior for explicit modeling.
- **Environment Design**: Supports dataset-based, text-based, and rule-based environments with varying degrees of realism and interactivity.
- **Interactive Visualization**: Real-time interfaces for monitoring and interacting with agents during experiments.
- **Extensive Tooling**: Includes utilities for interviews, surveys, interventions, and metric recording tailored for social experimentation.

## 📑 Table of Contents

1. [News](#news)
2. [Framework](#framework)
3. [Setup](#setup)
4. [QuickStart](#quickstart)
5. [Contributing](#contributing)
6. [License](#license)

<a id="news"></a>
## 📰 News

- 📢 **02.07** - Initial update is now live!

Stay tuned for upcoming updates!

<a id="framework"></a>
## 🛠️ Framework

AgentSociety presents a robust framework for simulating social behaviors and economic activities in a controlled, virtual environment. 
Utilizing advanced LLMs, AgentSociety emulates human-like decision-making and interactions. 
Our framework is divided into several key layers, each responsible for different functionalities as depicted in the diagram below:

<img src="./static/framework.png" alt="AgentSociety Framework Overview" width="600" style="display: block; margin: 20px auto;">

### Architectural Layers
- **Model Layer**: At the core, this layer manages agent configuration, task definitions, logging setup, and result aggregation. It provides a unified execution entry point for all agent processes, ensuring centralized control over agent behaviors and objectives through task configuration.
- **Agent Layer**: This layer implements multi-head workflows to manage various aspects of agent actions. The Memory component stores agent-related information such as location and motion, with static profiles maintaining unchanging attributes and a custom data pool acting as working memory. The Multi-Head Workflow supports both normal and event-driven modes, utilizing Reason Blocks (for decision-making based on context and tools via LLMs), Route Blocks (for selecting optimal paths using LLMs or rules), and Action Blocks (for executing defined actions).
- **Message Layer**: Facilitating communication among agents, this layer supports peer-to-peer (P2P), peer-to-group (P2G), and group chat interactions, enabling rich, dynamic exchanges within the simulation.
- **Environment Layer**: Managing the interaction between agents and their urban environment, this layer includes Environment Sensing for reading environmental data, Interaction Handling for modifying environmental states, and Message Management for processing incoming and outgoing messages from agents.
- **LLM Layer**: Providing essential configuration and integration services for incorporating Large Language Models (LLMs) into the agents' workflow, this layer supports model invocation and monitoring through Prompting & Execution. It is compatible with various LLMs, including but not limited to OpenAI, Qwen, and Deepseek models, offering flexibility in model choice.
- **Tool Layer**: Complementing the framework's capabilities, this layer offers utilities like string processing for parsing and formatting, result analysis for interpreting responses in formats like JSON or dictionaries, and data storage and retrieval mechanisms that include ranking and search functionalities.

<a id="setup"></a>
## ⚙️ Setup

You can set up AgentSociety easily via pip:

### Install via pip

Linux AMD64 or macOs

Python >= 3.11

```bash
pip install en-agentsociety
```

<a id="quickstart"></a>
## 🚀 QuickStart

Get started with AgentSociety in just a few minutes!

### Example Usage
To get started quickly, please refer to the `examples` folder in the repository. It contains sample scripts and configurations to help you understand how to create and use agents in an urban simulation environment.
Check our online document for detailed usage tutorial: [AgentSociety Document](https://en-agentsociety.readthedocs.io/en/latest/index.html).

<a id="contributing"></a>
## 🤝 Contributing
We welcome contributions from the community!

Thank you to everyone who has contributed to this project:

<a href=" ">
  <img src="https://contrib.rocks/image?repo=tsinghua-fib-lab/agentsociety" />
</a>

<a id="license"></a>
## 📄 License

AgentSociety is licensed under the Apache License Version 2.0 except for the `packages/en-agentsociety/commercial` folder. See the [LICENSE](LICENSE) file for more details.

---

Feel free to reach out if you have any questions, suggestions, or want to collaborate!

---

> **Follow us**: Stay updated with the latest news and features by watching the repository.

---
