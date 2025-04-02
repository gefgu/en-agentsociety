# Agent Tools
Agents in our framework are equipped with a comprehensive set of tools that enable them to perceive, reason, and interact with their environment and other agents. These tools are bundled together in the `AgentToolbox`, which is provided to each agent upon initialization.

Each tool handles a distinct aspect of agent functionality, making the system more maintainable and extensible.

## LLM Client

The LLM Client manages communications between agents and large language models, representing the agent's "soul". 

### Core APIs

- `atext_request`: Asynchronously sends requests to the LLM service with full parameter control and automatic retries with exponential backoff.
- `get_consumption, show_consumption`: Methods to track and report token usage statistics across API keys, with optional cost estimation.

## Environment
The Environment tool provides access to the simulation environment, allowing agents to interact with the urban space, economy, and other simulation components.

Environment plays a crucial role in the simulation, as it provides the basic information for agents to make decisions.

### Core APIs

- `get_person(person_id)`: Retrieves information about a specific person by ID
- `add_person(dict_person)`: Adds a new person to the simulation
- `set_aoi_schedules(person_id, target_positions, departure_times, modes)`: Sets schedules for a person to visit Areas of Interest (AOIs)
- `reset_person_position(person_id, aoi_id, poi_id, lane_id, s)`: Resets the position of a person within the simulation
- `get_around_poi(center, radius, poi_type)`: Gets Points of Interest (POIs) around a central point based on type
- `get_datetime()`: Gets the current simulation time, optionally formatted
- `get_poi_categories(center, radius)`: Retrieves unique categories of POIs around a central point
- `sense(key)`: Retrieves the value of an environment variable by its key
- `update_environment(key, value)`: Updates the value of a single environment variable
- `get_environment()`: Gets a formatted string of all environment variables
