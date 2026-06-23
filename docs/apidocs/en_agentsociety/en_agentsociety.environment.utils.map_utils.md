# {py:mod}`en_agentsociety.environment.utils.map_utils`

```{py:module} en_agentsociety.environment.utils.map_utils
```

```{autodoc2-docstring} en_agentsociety.environment.utils.map_utils
:allowtitles:
```

## Module Contents

### Functions

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`get_angle <en_agentsociety.environment.utils.map_utils.get_angle>`
  - ```{autodoc2-docstring} en_agentsociety.environment.utils.map_utils.get_angle
    :summary:
    ```
* - {py:obj}`point_on_line_given_distance <en_agentsociety.environment.utils.map_utils.point_on_line_given_distance>`
  - ```{autodoc2-docstring} en_agentsociety.environment.utils.map_utils.point_on_line_given_distance
    :summary:
    ```
* - {py:obj}`get_key_index_in_lane <en_agentsociety.environment.utils.map_utils.get_key_index_in_lane>`
  - ```{autodoc2-docstring} en_agentsociety.environment.utils.map_utils.get_key_index_in_lane
    :summary:
    ```
* - {py:obj}`get_xy_in_lane <en_agentsociety.environment.utils.map_utils.get_xy_in_lane>`
  - ```{autodoc2-docstring} en_agentsociety.environment.utils.map_utils.get_xy_in_lane
    :summary:
    ```
* - {py:obj}`get_direction_by_s <en_agentsociety.environment.utils.map_utils.get_direction_by_s>`
  - ```{autodoc2-docstring} en_agentsociety.environment.utils.map_utils.get_direction_by_s
    :summary:
    ```
````

### API

````{py:function} get_angle(x, y)
:canonical: en_agentsociety.environment.utils.map_utils.get_angle

```{autodoc2-docstring} en_agentsociety.environment.utils.map_utils.get_angle
```
````

````{py:function} point_on_line_given_distance(start_node, end_node, distance)
:canonical: en_agentsociety.environment.utils.map_utils.point_on_line_given_distance

```{autodoc2-docstring} en_agentsociety.environment.utils.map_utils.point_on_line_given_distance
```
````

````{py:function} get_key_index_in_lane(nodes: list[dict[str, float]], distance: float, direction: typing.Union[typing.Literal[front], typing.Literal[back]]) -> int
:canonical: en_agentsociety.environment.utils.map_utils.get_key_index_in_lane

```{autodoc2-docstring} en_agentsociety.environment.utils.map_utils.get_key_index_in_lane
```
````

````{py:function} get_xy_in_lane(nodes: list[dict[str, float]], distance: float, direction: typing.Union[typing.Literal[front], typing.Literal[back]]) -> tuple[float, float]
:canonical: en_agentsociety.environment.utils.map_utils.get_xy_in_lane

```{autodoc2-docstring} en_agentsociety.environment.utils.map_utils.get_xy_in_lane
```
````

````{py:function} get_direction_by_s(nodes: list[dict[str, float]], distance: float, direction: typing.Union[typing.Literal[front], typing.Literal[back]]) -> float
:canonical: en_agentsociety.environment.utils.map_utils.get_direction_by_s

```{autodoc2-docstring} en_agentsociety.environment.utils.map_utils.get_direction_by_s
```
````
