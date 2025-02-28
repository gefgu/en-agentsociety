# Prerequisites

Before using this framework, several prerequisite dependencies need to be prepared:
- LLM API
- [MQTT](https://mqtt.org/)
- [PostgreSQL](https://www.postgresql.org/)
- [MLflow](https://mlflow.org/)

## LLM API

To use this framework, you **need access to LLM APIs**. We support multiple providers:

- [DeepSeek](https://deepseek.com/)
- [OpenAI](https://openai.com/)
- [Qwen](https://tongyi.aliyun.com/)
- [SiliconFlow](https://siliconflow.cn/)
- [ZhipuAI](https://chatglm.cn/)

```{admonition} Warning
:class: warning
For the best simulation results, we recommend using `DeepSeek-v3` to showcase the capabilities of LLM agents. 
However, be aware of the usage limits and costs from providers, as they often cannot meet the simulation needs.
```

As a simple example, you can use GLM-4-Flash, the free model provided by Zhipu.

Here is how to obtain the ZhipuAI API:
1. Visit https://open.bigmodel.cn/
2. Register an account and authorize yourself at https://open.bigmodel.cn/usercenter/settings/auth/
3. Create an API key of `GLM-4-Flash` (free model) at https://open.bigmodel.cn/usercenter/apikeys/

As shown in the figure below, you will have successfully acquired an API key.

![Zhipu API](../_static/01-llm-api.png)

## MQTT

MQTT is a lightweight messaging protocol for the Internet of Things (IoT). It is a publish/subscribe network protocol that transports messages between devices.
We use [EMQX](https://www.emqx.com/) as the MQTT broker in this framework to provide X-to-agent communication.
The "X" contains agents and the GUI.

## PostgreSQL

PostgreSQL is a powerful, open-source object-relational database system.
We use it to store the simulation data for the visualization and analysis.

## MLflow

MLflow is an open-source platform for managing and tracking experiments.
We use it to help researchers to manage the simulation experiments and record some metrics.

## Install MQTT Broker (EMQX), PostgreSQL, and MLflow by Docker

We provide a *Docker-based* way to help you install the dependencies quickly.
Please refer to the [Docker](https://github.com/tsinghua-fib-lab/agentsociety/blob/main/docker/README.md) page for more details.

In short, the steps are as follows:
1. Install Docker.
2. Download the `docker` folder from [here](https://github.com/tsinghua-fib-lab/agentsociety/blob/main/docker/).
3. Change the default password in the `docker/docker-compose.yml` (or `docker/docker-compose-cn.yml` if you are in China) and `docker/mlflow/basic_auth.ini` file.
4. Run `docker compose up -d` (or `docker compose -f ./docker-compose-cn.yml up -d` if you are in China) to start the dependencies in the `docker` folder.
5. Access the services by the following URLs:
   - MLflow: http://localhost:59000
   - PostgreSQL: postgresql://postgres:YOUR_PASSWORD@localhost:5432/postgres
   - MQTT Broker: tcp://localhost:1883
   - EMQX (MQTT Broker) Dashboard: http://localhost:18083
6. Change EMQX Dashboard default password by its GUI.
7. Go ahead and start your first simulation!

