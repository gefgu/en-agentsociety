import pycityproto.city.economy.v2.economy_pb2 as economyv2

from agentsociety.cityagent import SocietyAgent


async def mobility_metric(simulation):
    # Use function attributes to store counts
    if not hasattr(mobility_metric, "step_count"):
        mobility_metric.step_count = 0  # type:ignore

    # Count the number of visited locations
    citizen_agents = await simulation.filter(types=[SocietyAgent])
    poi_visited_info = await simulation.gather("number_poi_visited", citizen_agents)
    poi_visited_sum = 0
    for group_gather in poi_visited_info:
        for agent_id, poi_visited in group_gather.items():
            poi_visited_sum += poi_visited
    average_poi_visited = float(poi_visited_sum / len(citizen_agents))
    print(f"Metric: Average POIs visited: {average_poi_visited}")
    await simulation.mlflow_client.log_metric(
        key="average_poi_visited",
        value=average_poi_visited,
        step=mobility_metric.step_count,  # type:ignore
    )
    await simulation.mlflow_client.log_metric(
        key="poi_visited_sum",
        value=poi_visited_sum,
        step=mobility_metric.step_count,  # type:ignore
    )
    mobility_metric.step_count += 1  # type:ignore


async def economy_metric(simulation):
    # Use function attributes to store counts
    if not hasattr(economy_metric, "nbs_id"):
        economy_metric.nbs_id = None  # type:ignore

    if economy_metric.nbs_id is None:  # type:ignore
        nbs_id = await simulation.economy_client.get_nbs_ids()
        nbs_id = nbs_id[0]
        economy_metric.nbs_id = nbs_id  # type:ignore

    try:
        real_gdp = await simulation.economy_client.get(
            economy_metric.nbs_id, "real_gdp"  # type:ignore
        )
    except:
        real_gdp = {}
    if len(real_gdp) > 0:
        # Get the latest real GDP value from the dictionary
        latest_time = max(real_gdp.keys())
        real_gdp = real_gdp[latest_time]
        forward_times_info = await simulation.gather(
            "forward_times", [economy_metric.nbs_id]  # type:ignore
        )
        step_count = 0
        for group_gather in forward_times_info:
            for agent_id, forward_times in group_gather.items():
                if agent_id == economy_metric.nbs_id:  # type:ignore
                    step_count = forward_times
        await simulation.mlflow_client.log_metric(
            key="real_gdp", value=real_gdp, step=step_count
        )
        other_metrics = [
            "prices",
            "working_hours",
            "depression",
            "consumption_currency",
            "income_currency",
        ]
        other_metrics_names = [
            "price",
            "working_hours",
            "depression",
            "consumption",
            "income",
        ]
        for metric, metric_name in zip(other_metrics, other_metrics_names):
            metric_value = (
                await simulation.economy_client.get(
                    economy_metric.nbs_id, metric  # type:ignore
                )
            )[latest_time]
            await simulation.mlflow_client.log_metric(
                key=metric_name, value=metric_value, step=step_count
            )
