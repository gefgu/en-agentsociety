# {py:mod}`en_agentsociety.agent.context`

```{py:module} en_agentsociety.agent.context
```

```{autodoc2-docstring} en_agentsociety.agent.context
:allowtitles:
```

## Module Contents

### Classes

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`AgentContext <en_agentsociety.agent.context.AgentContext>`
  - ```{autodoc2-docstring} en_agentsociety.agent.context.AgentContext
    :summary:
    ```
* - {py:obj}`BlockContext <en_agentsociety.agent.context.BlockContext>`
  - ```{autodoc2-docstring} en_agentsociety.agent.context.BlockContext
    :summary:
    ```
* - {py:obj}`DotDict <en_agentsociety.agent.context.DotDict>`
  - ```{autodoc2-docstring} en_agentsociety.agent.context.DotDict
    :summary:
    ```
````

### Functions

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`context_to_dot_dict <en_agentsociety.agent.context.context_to_dot_dict>`
  - ```{autodoc2-docstring} en_agentsociety.agent.context.context_to_dot_dict
    :summary:
    ```
* - {py:obj}`auto_deepcopy_dotdict <en_agentsociety.agent.context.auto_deepcopy_dotdict>`
  - ```{autodoc2-docstring} en_agentsociety.agent.context.auto_deepcopy_dotdict
    :summary:
    ```
* - {py:obj}`apply_auto_deepcopy_to_module <en_agentsociety.agent.context.apply_auto_deepcopy_to_module>`
  - ```{autodoc2-docstring} en_agentsociety.agent.context.apply_auto_deepcopy_to_module
    :summary:
    ```
````

### API

````{py:class} AgentContext(/, **data: typing.Any)
:canonical: en_agentsociety.agent.context.AgentContext

Bases: {py:obj}`pydantic.BaseModel`

```{autodoc2-docstring} en_agentsociety.agent.context.AgentContext
```

```{rubric} Initialization
```

```{autodoc2-docstring} en_agentsociety.agent.context.AgentContext.__init__
```

````

````{py:class} BlockContext(/, **data: typing.Any)
:canonical: en_agentsociety.agent.context.BlockContext

Bases: {py:obj}`pydantic.BaseModel`

```{autodoc2-docstring} en_agentsociety.agent.context.BlockContext
```

```{rubric} Initialization
```

```{autodoc2-docstring} en_agentsociety.agent.context.BlockContext.__init__
```

````

`````{py:class} DotDict(*args, **kwargs)
:canonical: en_agentsociety.agent.context.DotDict

Bases: {py:obj}`dict`

```{autodoc2-docstring} en_agentsociety.agent.context.DotDict
```

```{rubric} Initialization
```

```{autodoc2-docstring} en_agentsociety.agent.context.DotDict.__init__
```

````{py:method} __getattr__(key)
:canonical: en_agentsociety.agent.context.DotDict.__getattr__

```{autodoc2-docstring} en_agentsociety.agent.context.DotDict.__getattr__
```

````

````{py:method} __setattr__(key, value)
:canonical: en_agentsociety.agent.context.DotDict.__setattr__

````

````{py:method} __delattr__(key)
:canonical: en_agentsociety.agent.context.DotDict.__delattr__

````

````{py:method} merge(other)
:canonical: en_agentsociety.agent.context.DotDict.merge

```{autodoc2-docstring} en_agentsociety.agent.context.DotDict.merge
```

````

````{py:method} __or__(other)
:canonical: en_agentsociety.agent.context.DotDict.__or__

```{autodoc2-docstring} en_agentsociety.agent.context.DotDict.__or__
```

````

````{py:method} __ior__(other)
:canonical: en_agentsociety.agent.context.DotDict.__ior__

```{autodoc2-docstring} en_agentsociety.agent.context.DotDict.__ior__
```

````

`````

````{py:function} context_to_dot_dict(context: typing.Union[en_agentsociety.agent.context.AgentContext, en_agentsociety.agent.context.BlockContext]) -> en_agentsociety.agent.context.DotDict
:canonical: en_agentsociety.agent.context.context_to_dot_dict

```{autodoc2-docstring} en_agentsociety.agent.context.context_to_dot_dict
```
````

````{py:function} auto_deepcopy_dotdict(func)
:canonical: en_agentsociety.agent.context.auto_deepcopy_dotdict

```{autodoc2-docstring} en_agentsociety.agent.context.auto_deepcopy_dotdict
```
````

````{py:function} apply_auto_deepcopy_to_module(module)
:canonical: en_agentsociety.agent.context.apply_auto_deepcopy_to_module

```{autodoc2-docstring} en_agentsociety.agent.context.apply_auto_deepcopy_to_module
```
````
