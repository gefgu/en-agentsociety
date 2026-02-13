from typing import TYPE_CHECKING
import numpy as np

from ..memory.const import SocialRelation, RelationType
from ..logger import get_logger

if TYPE_CHECKING:
    from ..simulation.simulationengine import SimulationEngine
    from ..agent import CitizenAgentBase


def cosine_similarity(v1: np.ndarray, v2: np.ndarray) -> float:
    """Compute cosine similarity between two vectors."""
    norm1 = np.linalg.norm(v1)
    norm2 = np.linalg.norm(v2)
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return np.dot(v1, v2) / (norm1 * norm2)


async def initialize_social_network_by_similarity(
    engine: "SimulationEngine", min_friends: int = 1, max_friends: int = 5
):
    """
    Initialize social networks for agents with empty social networks based on persona similarity.

    Builds a social graph where agents have between min_friends and max_friends connections,
    selected via weighted random sampling based on Big Five personality trait similarity.

    Args:
        engine: The simulation engine instance.
        min_friends: Minimum number of friends per agent (default: 1).
        max_friends: Maximum number of friends per agent (default: 5).
    """
    # Import here to avoid circular dependency
    from ..agent import CitizenAgentBase

    get_logger().info(
        "Starting social network initialization based on persona similarity..."
    )

    citizen_ids = await engine.filter(types=(CitizenAgentBase,))

    need_network = True
    for agent_id in citizen_ids:
        agent = engine._id2agent[agent_id]
        social_network = await agent.memory.status.get("social_network", [])
        if len(social_network) > 0:
            need_network = False
            break

    if not need_network:
        get_logger().info(
            "At least one agent already has a social network. Skipping initialization for all agents."
        )
        return

    persona_features = {}
    for agent_id in citizen_ids:
        agent = engine._id2agent[agent_id]
        age = await agent.memory.status.get("age", 30)
        big5 = await agent.memory.status.get("big5", {})
        persona_features[agent_id] = [
            age,
            big5.get("openness", 2),
            big5.get("conscientiousness", 2),
            big5.get("extraversion", 2),
            big5.get("agreeableness", 2),
            big5.get("neuroticism", 2),
        ]

    np.random.seed(42)  # For reproducibility

    similarity_matrix = np.zeros((len(citizen_ids), len(citizen_ids)))
    for i in range(len(citizen_ids)):
        for j in range(i + 1, len(citizen_ids)):
            sim = cosine_similarity(
                np.array(persona_features[citizen_ids[i]]),
                np.array(persona_features[citizen_ids[j]])
            )
            similarity_matrix[i][j] = sim
            similarity_matrix[j][i] = sim

    friendship_matrix = np.zeros((len(citizen_ids), len(citizen_ids)))

    for i in range(len(citizen_ids)):
        similarities = similarity_matrix[i].copy()
        similarities[i] = 0  # Don't befriend yourself
        probabilities = (
            similarities / np.sum(similarities)
            if np.sum(similarities) > 0
            else np.ones(len(similarities)) / len(similarities)
        )
        current_friends = np.where(friendship_matrix[i] == 1)[0]
        if len(current_friends) >= max_friends:
            continue
        num_friends = np.random.randint(
            min_friends, (max_friends - len(current_friends)) + 1
        )
        available_indices = [
            idx
            for idx in range(len(citizen_ids))
            if idx != i and friendship_matrix[i][idx] == 0
        ]
        if len(available_indices) == 0:
            continue
        available_probs = probabilities[available_indices]
        available_probs = available_probs / np.sum(available_probs)
        selected_indices = np.random.choice(
            available_indices,
            size=min(num_friends, len(available_indices)),
            replace=False,
            p=available_probs
        )
        friendship_matrix[i][selected_indices] = 1
        friendship_matrix[selected_indices, i] = 1

    for i in range(len(citizen_ids)):
        agent_id = citizen_ids[i]
        agent = engine._id2agent[agent_id]
        friends = np.where(friendship_matrix[i] == 1)[0]
        social_network = []
        for friend_idx in friends:
            friend_id = citizen_ids[friend_idx]
            sim = similarity_matrix[i][friend_idx]
            base_value = 0.3 + (sim * 0.5)
            relation = SocialRelation(
                source_id=agent_id,
                target_id=friend_id,
                kind=RelationType.FRIEND,
                affinity=float(np.clip(base_value + np.random.uniform(-0.1, 0.1), -1.0, 1.0)),
                trust=float(np.clip(base_value + np.random.uniform(-0.1, 0.1), -1.0, 1.0)),
                familiarity=float(np.clip(base_value + np.random.uniform(-0.1, 0.1), -1.0, 1.0)),
            )
            social_network.append(relation)
        
        await agent.memory.status.update("social_network", social_network)
        get_logger().debug(f"Agent {agent_id} initialized with {len(social_network)} friends")

    get_logger().info(
        f"Social network initialization complete for {len(citizen_ids)} agents."
    )