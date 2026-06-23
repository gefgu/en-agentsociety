# {py:mod}`en_agentsociety.agent.distribution`

```{py:module} en_agentsociety.agent.distribution
```

```{autodoc2-docstring} en_agentsociety.agent.distribution
:allowtitles:
```

## Module Contents

### Classes

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`DistributionType <en_agentsociety.agent.distribution.DistributionType>`
  - ```{autodoc2-docstring} en_agentsociety.agent.distribution.DistributionType
    :summary:
    ```
* - {py:obj}`DistributionConfig <en_agentsociety.agent.distribution.DistributionConfig>`
  - ```{autodoc2-docstring} en_agentsociety.agent.distribution.DistributionConfig
    :summary:
    ```
* - {py:obj}`Distribution <en_agentsociety.agent.distribution.Distribution>`
  - ```{autodoc2-docstring} en_agentsociety.agent.distribution.Distribution
    :summary:
    ```
* - {py:obj}`ChoiceDistribution <en_agentsociety.agent.distribution.ChoiceDistribution>`
  - ```{autodoc2-docstring} en_agentsociety.agent.distribution.ChoiceDistribution
    :summary:
    ```
* - {py:obj}`UniformIntDistribution <en_agentsociety.agent.distribution.UniformIntDistribution>`
  - ```{autodoc2-docstring} en_agentsociety.agent.distribution.UniformIntDistribution
    :summary:
    ```
* - {py:obj}`UniformFloatDistribution <en_agentsociety.agent.distribution.UniformFloatDistribution>`
  - ```{autodoc2-docstring} en_agentsociety.agent.distribution.UniformFloatDistribution
    :summary:
    ```
* - {py:obj}`NormalDistribution <en_agentsociety.agent.distribution.NormalDistribution>`
  - ```{autodoc2-docstring} en_agentsociety.agent.distribution.NormalDistribution
    :summary:
    ```
* - {py:obj}`ConstantDistribution <en_agentsociety.agent.distribution.ConstantDistribution>`
  - ```{autodoc2-docstring} en_agentsociety.agent.distribution.ConstantDistribution
    :summary:
    ```
````

### Functions

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`get_distribution <en_agentsociety.agent.distribution.get_distribution>`
  - ```{autodoc2-docstring} en_agentsociety.agent.distribution.get_distribution
    :summary:
    ```
* - {py:obj}`sample_field_value <en_agentsociety.agent.distribution.sample_field_value>`
  - ```{autodoc2-docstring} en_agentsociety.agent.distribution.sample_field_value
    :summary:
    ```
````

### Data

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`__all__ <en_agentsociety.agent.distribution.__all__>`
  - ```{autodoc2-docstring} en_agentsociety.agent.distribution.__all__
    :summary:
    ```
````

### API

````{py:data} __all__
:canonical: en_agentsociety.agent.distribution.__all__
:value: >
   ['Distribution', 'ChoiceDistribution', 'UniformIntDistribution', 'UniformFloatDistribution', 'Normal...

```{autodoc2-docstring} en_agentsociety.agent.distribution.__all__
```

````

`````{py:class} DistributionType()
:canonical: en_agentsociety.agent.distribution.DistributionType

Bases: {py:obj}`str`, {py:obj}`enum.Enum`

```{autodoc2-docstring} en_agentsociety.agent.distribution.DistributionType
```

```{rubric} Initialization
```

```{autodoc2-docstring} en_agentsociety.agent.distribution.DistributionType.__init__
```

````{py:attribute} CHOICE
:canonical: en_agentsociety.agent.distribution.DistributionType.CHOICE
:value: >
   'choice'

```{autodoc2-docstring} en_agentsociety.agent.distribution.DistributionType.CHOICE
```

````

````{py:attribute} UNIFORM_INT
:canonical: en_agentsociety.agent.distribution.DistributionType.UNIFORM_INT
:value: >
   'uniform_int'

```{autodoc2-docstring} en_agentsociety.agent.distribution.DistributionType.UNIFORM_INT
```

````

````{py:attribute} UNIFORM_FLOAT
:canonical: en_agentsociety.agent.distribution.DistributionType.UNIFORM_FLOAT
:value: >
   'uniform_float'

```{autodoc2-docstring} en_agentsociety.agent.distribution.DistributionType.UNIFORM_FLOAT
```

````

````{py:attribute} NORMAL
:canonical: en_agentsociety.agent.distribution.DistributionType.NORMAL
:value: >
   'normal'

```{autodoc2-docstring} en_agentsociety.agent.distribution.DistributionType.NORMAL
```

````

````{py:attribute} CONSTANT
:canonical: en_agentsociety.agent.distribution.DistributionType.CONSTANT
:value: >
   'constant'

```{autodoc2-docstring} en_agentsociety.agent.distribution.DistributionType.CONSTANT
```

````

`````

`````{py:class} DistributionConfig(/, **data: typing.Any)
:canonical: en_agentsociety.agent.distribution.DistributionConfig

Bases: {py:obj}`pydantic.BaseModel`

```{autodoc2-docstring} en_agentsociety.agent.distribution.DistributionConfig
```

```{rubric} Initialization
```

```{autodoc2-docstring} en_agentsociety.agent.distribution.DistributionConfig.__init__
```

````{py:attribute} model_config
:canonical: en_agentsociety.agent.distribution.DistributionConfig.model_config
:value: >
   'ConfigDict(...)'

```{autodoc2-docstring} en_agentsociety.agent.distribution.DistributionConfig.model_config
```

````

````{py:attribute} dist_type
:canonical: en_agentsociety.agent.distribution.DistributionConfig.dist_type
:type: en_agentsociety.agent.distribution.DistributionType
:value: >
   'Field(...)'

```{autodoc2-docstring} en_agentsociety.agent.distribution.DistributionConfig.dist_type
```

````

````{py:attribute} choices
:canonical: en_agentsociety.agent.distribution.DistributionConfig.choices
:type: typing.Optional[list[typing.Any]]
:value: >
   None

```{autodoc2-docstring} en_agentsociety.agent.distribution.DistributionConfig.choices
```

````

````{py:attribute} weights
:canonical: en_agentsociety.agent.distribution.DistributionConfig.weights
:type: typing.Optional[list[float]]
:value: >
   None

```{autodoc2-docstring} en_agentsociety.agent.distribution.DistributionConfig.weights
```

````

````{py:attribute} min_value
:canonical: en_agentsociety.agent.distribution.DistributionConfig.min_value
:type: typing.Optional[typing.Union[int, float]]
:value: >
   None

```{autodoc2-docstring} en_agentsociety.agent.distribution.DistributionConfig.min_value
```

````

````{py:attribute} max_value
:canonical: en_agentsociety.agent.distribution.DistributionConfig.max_value
:type: typing.Optional[typing.Union[int, float]]
:value: >
   None

```{autodoc2-docstring} en_agentsociety.agent.distribution.DistributionConfig.max_value
```

````

````{py:attribute} mean
:canonical: en_agentsociety.agent.distribution.DistributionConfig.mean
:type: typing.Optional[float]
:value: >
   None

```{autodoc2-docstring} en_agentsociety.agent.distribution.DistributionConfig.mean
```

````

````{py:attribute} std
:canonical: en_agentsociety.agent.distribution.DistributionConfig.std
:type: typing.Optional[float]
:value: >
   None

```{autodoc2-docstring} en_agentsociety.agent.distribution.DistributionConfig.std
```

````

````{py:attribute} value
:canonical: en_agentsociety.agent.distribution.DistributionConfig.value
:type: typing.Optional[typing.Any]
:value: >
   None

```{autodoc2-docstring} en_agentsociety.agent.distribution.DistributionConfig.value
```

````

`````

`````{py:class} Distribution
:canonical: en_agentsociety.agent.distribution.Distribution

```{autodoc2-docstring} en_agentsociety.agent.distribution.Distribution
```

````{py:method} __repr__() -> str
:canonical: en_agentsociety.agent.distribution.Distribution.__repr__
:abstractmethod:

```{autodoc2-docstring} en_agentsociety.agent.distribution.Distribution.__repr__
```

````

````{py:method} __str__() -> str
:canonical: en_agentsociety.agent.distribution.Distribution.__str__

````

````{py:method} sample() -> typing.Any
:canonical: en_agentsociety.agent.distribution.Distribution.sample
:abstractmethod:

```{autodoc2-docstring} en_agentsociety.agent.distribution.Distribution.sample
```

````

````{py:method} create(dist_type: str, **kwargs) -> en_agentsociety.agent.distribution.Distribution
:canonical: en_agentsociety.agent.distribution.Distribution.create
:staticmethod:

```{autodoc2-docstring} en_agentsociety.agent.distribution.Distribution.create
```

````

````{py:method} from_config(config: en_agentsociety.agent.distribution.DistributionConfig) -> en_agentsociety.agent.distribution.Distribution
:canonical: en_agentsociety.agent.distribution.Distribution.from_config
:staticmethod:

```{autodoc2-docstring} en_agentsociety.agent.distribution.Distribution.from_config
```

````

`````

`````{py:class} ChoiceDistribution(choices: typing.List[typing.Any], weights: typing.Optional[typing.List[float]] = None)
:canonical: en_agentsociety.agent.distribution.ChoiceDistribution

Bases: {py:obj}`en_agentsociety.agent.distribution.Distribution`

```{autodoc2-docstring} en_agentsociety.agent.distribution.ChoiceDistribution
```

```{rubric} Initialization
```

```{autodoc2-docstring} en_agentsociety.agent.distribution.ChoiceDistribution.__init__
```

````{py:method} __repr__() -> str
:canonical: en_agentsociety.agent.distribution.ChoiceDistribution.__repr__

````

````{py:method} sample() -> typing.Any
:canonical: en_agentsociety.agent.distribution.ChoiceDistribution.sample

````

`````

`````{py:class} UniformIntDistribution(min_value: int, max_value: int)
:canonical: en_agentsociety.agent.distribution.UniformIntDistribution

Bases: {py:obj}`en_agentsociety.agent.distribution.Distribution`

```{autodoc2-docstring} en_agentsociety.agent.distribution.UniformIntDistribution
```

```{rubric} Initialization
```

```{autodoc2-docstring} en_agentsociety.agent.distribution.UniformIntDistribution.__init__
```

````{py:method} __repr__() -> str
:canonical: en_agentsociety.agent.distribution.UniformIntDistribution.__repr__

````

````{py:method} sample() -> int
:canonical: en_agentsociety.agent.distribution.UniformIntDistribution.sample

````

`````

`````{py:class} UniformFloatDistribution(min_value: float, max_value: float)
:canonical: en_agentsociety.agent.distribution.UniformFloatDistribution

Bases: {py:obj}`en_agentsociety.agent.distribution.Distribution`

```{autodoc2-docstring} en_agentsociety.agent.distribution.UniformFloatDistribution
```

```{rubric} Initialization
```

```{autodoc2-docstring} en_agentsociety.agent.distribution.UniformFloatDistribution.__init__
```

````{py:method} __repr__() -> str
:canonical: en_agentsociety.agent.distribution.UniformFloatDistribution.__repr__

````

````{py:method} sample() -> float
:canonical: en_agentsociety.agent.distribution.UniformFloatDistribution.sample

````

`````

`````{py:class} NormalDistribution(mean: float, std: float, min_value: typing.Optional[float] = None, max_value: typing.Optional[float] = None)
:canonical: en_agentsociety.agent.distribution.NormalDistribution

Bases: {py:obj}`en_agentsociety.agent.distribution.Distribution`

```{autodoc2-docstring} en_agentsociety.agent.distribution.NormalDistribution
```

```{rubric} Initialization
```

```{autodoc2-docstring} en_agentsociety.agent.distribution.NormalDistribution.__init__
```

````{py:method} __repr__() -> str
:canonical: en_agentsociety.agent.distribution.NormalDistribution.__repr__

````

````{py:method} sample() -> float
:canonical: en_agentsociety.agent.distribution.NormalDistribution.sample

````

`````

`````{py:class} ConstantDistribution(value: typing.Any)
:canonical: en_agentsociety.agent.distribution.ConstantDistribution

Bases: {py:obj}`en_agentsociety.agent.distribution.Distribution`

```{autodoc2-docstring} en_agentsociety.agent.distribution.ConstantDistribution
```

```{rubric} Initialization
```

```{autodoc2-docstring} en_agentsociety.agent.distribution.ConstantDistribution.__init__
```

````{py:method} __repr__() -> str
:canonical: en_agentsociety.agent.distribution.ConstantDistribution.__repr__

````

````{py:method} sample() -> typing.Any
:canonical: en_agentsociety.agent.distribution.ConstantDistribution.sample

````

`````

````{py:function} get_distribution(distributions: dict[str, en_agentsociety.agent.distribution.Distribution], field: str) -> en_agentsociety.agent.distribution.Distribution
:canonical: en_agentsociety.agent.distribution.get_distribution

```{autodoc2-docstring} en_agentsociety.agent.distribution.get_distribution
```
````

````{py:function} sample_field_value(distributions: dict[str, en_agentsociety.agent.distribution.Distribution], field: str) -> typing.Any
:canonical: en_agentsociety.agent.distribution.sample_field_value

```{autodoc2-docstring} en_agentsociety.agent.distribution.sample_field_value
```
````
