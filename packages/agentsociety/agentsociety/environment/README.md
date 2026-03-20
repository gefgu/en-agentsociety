# `environment/` — City Environment Clients

This package wraps the external city simulators and provides agents with a view of the physical city (map, mobility, economy).

---

## Files

| File | Purpose |
|---|---|
| `environment.py` | `Environment` facade — unified interface to all sub-systems |
| `mapdata.py` | `MapData` — POI, road network, and area data |
| `download_sim.py` | Utility to download city simulator binaries |
| `sim/` | Mobility simulator client (gRPC) |
| `economy/` | Economic simulator client |
| `syncer/` | State synchronization between Python agents and C++ simulator |
| `utils/` | Helper converters and math utilities |

---

## `Environment`

The `Environment` facade aggregates all sub-systems:

```python
env = toolbox.environment

# Map queries
pois = await env.map.get_pois_near(lat=39.9, lng=116.4, radius=500)
area = await env.map.get_area_info(area_id=42)

# Mobility
await env.move_person(person_id=1, dest_aoi_id=123)
position = await env.get_person_position(person_id=1)

# Economy
wage = await env.economy.get_wage(firm_id=5)
await env.economy.transfer(from_id=1, to_id=2, amount=100.0)
```

---

## `EnvironmentConfig`

```python
class EnvironmentConfig(BaseModel):
    work_start_time: int = 8     # hour of day
    work_end_time: int = 18
    sleep_start_time: int = 22
    sleep_end_time: int = 7
    # mobility simulator endpoint, map data paths, etc.
```

---

## `MapData`

Provides access to a pre-processed city map:

- **POIs** (Points of Interest): restaurants, hospitals, parks, offices, …
- **AOIs** (Areas of Interest): neighborhoods, districts
- **Road network**: for routing

```python
map_data = MapData(map_path="city_map.pb")
pois = map_data.query_pois(center=(39.9, 116.4), radius=1000, categories=["restaurant"])
```

---

## `EnvironmentStarter`

Utility that starts the external simulator processes (mobility, economy) as subprocesses and waits for them to be ready before the simulation begins.

---

## Notes

- Agents access the environment only through `self.toolbox.environment` or `self.environment` (inside Blocks).
- The city simulators are external C++ / Go binaries; this package contains only the Python gRPC/REST clients.
- Map data is loaded once at startup and shared across all Ray workers.
