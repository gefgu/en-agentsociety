# Neighborhoods in the Simulation

This note explains how neighborhood data is loaded and where it affects agent behavior.

## What neighborhood data is

Neighborhoods are optional polygon regions loaded in addition to AOIs and POIs.
They are stored in `MapData.neighborhoods` and indexed with a spatial tree for point and radius queries.

Each neighborhood record is expected to include:
- `id`
- `positions` (polygon vertices in map XY coordinates)
- optional metadata such as `name` and `description`

## How neighborhoods are loaded

Neighborhood loading is controlled by `MapConfig.neighborhood_file_path`.

Flow:
1. `MapData` loads AOIs and POIs from the map protobuf.
2. If `neighborhood_file_path` is set, it loads JSON neighborhood data from local disk or S3.
3. Supported formats are:
   - object with `hoods` field
   - raw list of neighborhood objects
4. During parse, neighborhood polygons are converted into:
   - `shapely_xy` for geometric queries in map XY space
   - `shapely_lnglat` for lat/lng geometry views
5. A neighborhood `STRtree` index is built for fast lookup.

Cache behavior:
- map cache without neighborhoods: `<map_file>.cache`
- map cache with neighborhoods: `<map_file>.with_hoods.cache`

## Runtime usage in decision making

Neighborhoods are currently used by the place selection stage in the mobility block.

Behavior summary:
1. Agent queries candidate POIs by intention category and search radius.
2. For each POI, the block maps POI position to a containing neighborhood via `query_neighborhood_by_point`.
3. Neighborhoods are ranked by number of matching POIs.
4. LLM prompt receives ranked neighborhood candidates and chooses neighborhood ids.
5. POIs are filtered to only selected neighborhoods.
6. If neighborhood filtering fails or returns empty results, flow falls back to AOI-based filtering.

This adds a semantic area selection step before AOI fallback, which helps choose places from coherent local zones.

## APIs exposed by MapData

Neighborhood-related methods:
- `get_all_neighborhoods()`
- `get_neighborhood(neighborhood_id)`
- `query_neighborhood_by_point(point)`
- `query_neighborhoods(center, radius)`

## Important notes

- Neighborhood support is optional. If no neighborhood file is configured, neighborhood queries return no results and mobility logic falls back to AOI filtering.
- Neighborhood polygons must be valid for reliable contains/intersection behavior.
- The mobility simulator binary is not neighborhood-aware directly; this is Python-side decision logic used to filter candidate POIs before destination selection.
