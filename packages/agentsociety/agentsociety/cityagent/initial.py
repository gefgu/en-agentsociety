import random
from copy import deepcopy

import numpy as np

from ..logger import get_logger
from ..simulation import AgentSociety
from .bankagent import BankAgent
from .firmagent import FirmAgent
from .governmentagent import GovernmentAgent
from .nbsagent import NBSAgent
from .societyagent import SocietyAgent

__all__ = ["initialize_social_network", "bind_agent_info"]


async def initialize_social_network(simulation: AgentSociety):
    """
    Initializes the social network between agents.

    - **Description**:
        - Creates friendship relationships between agents
        - Assigns relationship types (family, colleague, friend)
        - Sets relationship strengths based on type
        - Initializes chat histories and interaction records

    - **Returns**:
        - None
    """
    get_logger().info("Initializing social network...")

    # Define possible relationship types
    relation_types = ["family", "colleague", "friend"]

    # Get all agent IDs
    citizen_ids = await simulation.filter(types=(SocietyAgent,))
    for agent_id in citizen_ids:
        # Randomly select 2-5 friends for each agent
        num_friends = random.randint(2, 5)
        possible_friends = [aid for aid in citizen_ids if aid != agent_id]
        friends = random.sample(
            possible_friends, min(num_friends, len(possible_friends))
        )

        # Initialize friend relationships
        await simulation.update([agent_id], "friends", friends)

        # Initialize relationship types and strengths with each friend
        relationships = {}
        relation_type_map = {}

        for friend_id in friends:
            # Randomly select relationship type
            relation_type = random.choice(relation_types)
            # Set initial relationship strength range based on type
            if relation_type == "family":
                strength = random.randint(60, 90)  # Higher strength for family
            elif relation_type == "colleague":
                strength = random.randint(40, 70)  # Medium strength for colleagues
            else:  # friend
                strength = random.randint(30, 80)  # Wide range for friends

            relationships[friend_id] = strength
            relation_type_map[friend_id] = relation_type

        # Update relationship strengths and types
        await simulation.update([agent_id], "relationships", relationships)
        await simulation.update([agent_id], "relation_types", relation_type_map)

        # Initialize empty chat histories and interaction records
        await simulation.update(
            [agent_id], "chat_histories", {friend_id: "" for friend_id in friends}
        )
        await simulation.update(
            [agent_id], "interactions", {friend_id: [] for friend_id in friends}
        )


def zipf_distribution(N, F, s=1.0):
    """
    Generates employee counts for F companies following Zipf's law, with total employees N.

    - **Description**:
        - Uses Zipf's law to distribute N total employees across F companies
        - The distribution follows a power law where employee count is proportional to 1/rank^s
        - Normalizes the distribution to ensure total employees equals N

    - **Parameters**:
        - `N`: Total number of employees across all companies
        - `F`: Number of companies to distribute employees across
        - `s`: Power law exponent for Zipf's law, typically close to 1

    - **Returns**:
        - List of integer employee counts for each company, summing to N
    """
    ranks = np.arange(1, F + 1)  # Ranks from 1 to F
    sizes = 1 / (ranks**s)  # Calculate employee count ratio according to Zipf's law

    # Normalize to make total employees equal N
    total_size = np.sum(sizes)
    normalized_sizes = sizes / total_size * N

    # Convert to integers and adjust to ensure the sum equals N
    int_sizes = np.round(normalized_sizes).astype(int)
    current_sum = np.sum(int_sizes)

    # If rounding caused the total to deviate from N, adjust the largest entries
    if current_sum < N:
        difference = N - current_sum
        # Find indices of the largest differences and increment them
        for i in range(difference):
            idx = np.argmax(normalized_sizes - int_sizes)
            int_sizes[idx] += 1
    elif current_sum > N:
        difference = current_sum - N
        # Find indices of the smallest (most negative) differences and decrement them
        for i in range(difference):
            idx = np.argmin(normalized_sizes - int_sizes)
            int_sizes[idx] -= 1

    return int_sizes


async def bind_agent_info(simulation: AgentSociety):
    """
    Binds agent information including IDs for citizens, firms, government, banks and NBS.

    - **Description**:
        - Gathers all agent IDs and maps them between UUID and agent ID
        - Assigns employees to firms following Zipf's law distribution
        - Links citizens to government and bank systems

    - **Returns**:
        - None
    """
    get_logger().info("Binding economy relationship...")
    citizen_ids = await simulation.filter(types=(SocietyAgent,))
    try:
        firm_ids = await simulation.filter(types=(FirmAgent,))
    except Exception:
        firm_ids = []
    try:
        government_ids = await simulation.filter(types=(GovernmentAgent,))
    except Exception:
        government_ids = []
    try:
        bank_ids = await simulation.filter(types=(BankAgent,))
    except Exception:
        bank_ids = []
    try:
        nbs_ids = await simulation.filter(types=(NBSAgent,))
    except Exception:
        nbs_ids = []
    if len(firm_ids) == 0 or len(government_ids) == 0 or len(bank_ids) == 0 or len(nbs_ids) == 0:
        get_logger().warning("No firm, government, bank or NBS found, skipping economy binding")
        return
    random.shuffle(citizen_ids)
    employee_sizes = zipf_distribution(len(citizen_ids), len(firm_ids))

    orig_citizen_ids = deepcopy(citizen_ids)
    get_logger().debug(f"citizen_ids: {citizen_ids}")
    get_logger().debug(f"firm_ids: {firm_ids}")
    get_logger().debug(f"employee_sizes: {employee_sizes}")
    for firm_id, size in zip(firm_ids, employee_sizes):
        await simulation.economy_update(firm_id, "employees", citizen_ids[:size])
        await simulation.update(citizen_ids[:size], "firm_id", firm_id)
        citizen_ids = citizen_ids[size:]

    gathered_firm_ids = await simulation.gather(
        "firm_id",
        orig_citizen_ids,
    )
    get_logger().debug(f"Gathered firm_ids: {gathered_firm_ids}")
    for government_id in government_ids:
        await simulation.economy_update(government_id, "citizen_ids", citizen_ids)
    for bank_id in bank_ids:
        await simulation.economy_update(bank_id, "citizen_ids", citizen_ids)
    await simulation.update(nbs_ids, "citizen_ids", citizen_ids)
    for nbs_id in nbs_ids:
        await simulation.economy_update(nbs_id, "citizen_ids", citizen_ids)
    get_logger().info("Agent info binding completed!")
