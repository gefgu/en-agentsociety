# {py:mod}`en_agentsociety.environment.sim.person_service`

```{py:module} en_agentsociety.environment.sim.person_service
```

```{autodoc2-docstring} en_agentsociety.environment.sim.person_service
:allowtitles:
```

## Module Contents

### Classes

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`PersonService <en_agentsociety.environment.sim.person_service.PersonService>`
  - ```{autodoc2-docstring} en_agentsociety.environment.sim.person_service.PersonService
    :summary:
    ```
````

### Functions

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`default_person_template_generator <en_agentsociety.environment.sim.person_service.default_person_template_generator>`
  - ```{autodoc2-docstring} en_agentsociety.environment.sim.person_service.default_person_template_generator
    :summary:
    ```
````

### Data

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`__all__ <en_agentsociety.environment.sim.person_service.__all__>`
  - ```{autodoc2-docstring} en_agentsociety.environment.sim.person_service.__all__
    :summary:
    ```
````

### API

````{py:data} __all__
:canonical: en_agentsociety.environment.sim.person_service.__all__
:value: >
   ['PersonService']

```{autodoc2-docstring} en_agentsociety.environment.sim.person_service.__all__
```

````

````{py:function} default_person_template_generator() -> pycityproto.city.person.v2.person_pb2.Person
:canonical: en_agentsociety.environment.sim.person_service.default_person_template_generator

```{autodoc2-docstring} en_agentsociety.environment.sim.person_service.default_person_template_generator
```
````

`````{py:class} PersonService(aio_channel: grpc.aio.Channel)
:canonical: en_agentsociety.environment.sim.person_service.PersonService

```{autodoc2-docstring} en_agentsociety.environment.sim.person_service.PersonService
```

```{rubric} Initialization
```

```{autodoc2-docstring} en_agentsociety.environment.sim.person_service.PersonService.__init__
```

````{py:method} default_person(return_dict: bool = False) -> typing.Union[pycityproto.city.person.v2.person_pb2.Person, dict]
:canonical: en_agentsociety.environment.sim.person_service.PersonService.default_person
:staticmethod:

```{autodoc2-docstring} en_agentsociety.environment.sim.person_service.PersonService.default_person
```

````

````{py:method} GetPerson(req: typing.Union[pycityproto.city.person.v2.person_service_pb2.GetPersonRequest, dict[str, typing.Any]], dict_return: bool = True) -> collections.abc.Coroutine[typing.Any, typing.Any, typing.Union[dict[str, typing.Any], pycityproto.city.person.v2.person_service_pb2.GetPersonResponse]]
:canonical: en_agentsociety.environment.sim.person_service.PersonService.GetPerson

```{autodoc2-docstring} en_agentsociety.environment.sim.person_service.PersonService.GetPerson
```

````

````{py:method} AddPerson(req: typing.Union[pycityproto.city.person.v2.person_service_pb2.AddPersonRequest, dict[str, typing.Any]], dict_return: bool = True) -> collections.abc.Coroutine[typing.Any, typing.Any, typing.Union[dict[str, typing.Any], pycityproto.city.person.v2.person_service_pb2.AddPersonResponse]]
:canonical: en_agentsociety.environment.sim.person_service.PersonService.AddPerson

```{autodoc2-docstring} en_agentsociety.environment.sim.person_service.PersonService.AddPerson
```

````

````{py:method} SetSchedule(req: typing.Union[pycityproto.city.person.v2.person_service_pb2.SetScheduleRequest, dict[str, typing.Any]], dict_return: bool = True) -> collections.abc.Coroutine[typing.Any, typing.Any, typing.Union[dict[str, typing.Any], pycityproto.city.person.v2.person_service_pb2.SetScheduleResponse]]
:canonical: en_agentsociety.environment.sim.person_service.PersonService.SetSchedule

```{autodoc2-docstring} en_agentsociety.environment.sim.person_service.PersonService.SetSchedule
```

````

````{py:method} ResetPersonPosition(req: typing.Union[pycityproto.city.person.v2.person_service_pb2.ResetPersonPositionRequest, dict[str, typing.Any]], dict_return: bool = True) -> collections.abc.Coroutine[typing.Any, typing.Any, typing.Union[dict[str, typing.Any], pycityproto.city.person.v2.person_service_pb2.ResetPersonPositionResponse]]
:canonical: en_agentsociety.environment.sim.person_service.PersonService.ResetPersonPosition

```{autodoc2-docstring} en_agentsociety.environment.sim.person_service.PersonService.ResetPersonPosition
```

````

````{py:method} GetGlobalStatistics(req: typing.Union[pycityproto.city.person.v2.person_service_pb2.GetGlobalStatisticsRequest, dict[str, typing.Any]], dict_return: bool = True) -> collections.abc.Coroutine[typing.Any, typing.Any, typing.Union[dict[str, typing.Any], pycityproto.city.person.v2.person_service_pb2.GetGlobalStatisticsResponse]]
:canonical: en_agentsociety.environment.sim.person_service.PersonService.GetGlobalStatistics

```{autodoc2-docstring} en_agentsociety.environment.sim.person_service.PersonService.GetGlobalStatistics
```

````

`````
