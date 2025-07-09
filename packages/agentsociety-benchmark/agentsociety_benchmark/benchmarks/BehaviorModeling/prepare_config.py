from pathlib import Path
from agentsociety.agent import IndividualAgentBase, CustomTool
from agentsociety.configs import IndividualConfig, TaskLoaderConfig, AgentConfig
from agentsociety_benchmark.utils.agent_loader import load_agent_class

from .task import BehaviorModelingTask
from .interactiontool import InteractionTool
from agentsociety_benchmark.cli import BenchmarkConfig

def prepare_config(benchmark_config: BenchmarkConfig, agent_config: AgentConfig, datasets_path: Path, mode: str) -> IndividualConfig:
    """
    Load and process configuration file with agent class from file or class name
    
    Args:
        config (BenchmarkConfig): Benchmark configuration
        agent_config (AgentConfig): Agent configuration
        datasets_path (Path): Path to datasets directory
        mode (str): Execution mode
    Returns:
        IndividualConfig: Processed configuration
    """
    # Handle agent_class if it's a string (could be file path or class name)
    if isinstance(agent_config.agent_class, str):
        agent_path = Path(agent_config.agent_class)
        
        # Check if it's a file path (ends with .py or exists as file)
        if agent_path.suffix == '.py' or agent_path.exists():
            # It's a file path, load agent class from file
            agent_class = load_agent_class(agent_path, IndividualAgentBase)
            agent_config.agent_class = agent_class

    # Add CustomTool for Information Retrieval
    agent_config.tools = [
        CustomTool(
            name="information_retrieval_tool",
            tool=InteractionTool(data_dir=str(datasets_path)),
            description="Retrieve information from the internet",
        ),
    ]
    
    # Create solver configuration
    individual_config = IndividualConfig(
        name="BehaviorModeling_benchmark",
        llm=benchmark_config.llm,
        env=benchmark_config.env,    
        individual=agent_config,
        task_loader=TaskLoaderConfig(
            task_type=BehaviorModelingTask,
            file_path=str(datasets_path / f"{mode}_tasks.json"),
            shuffle=True,
        ),
        logging_level="INFO"
    )
    
    return individual_config