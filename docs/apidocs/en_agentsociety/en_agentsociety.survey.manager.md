# {py:mod}`en_agentsociety.survey.manager`

```{py:module} en_agentsociety.survey.manager
```

```{autodoc2-docstring} en_agentsociety.survey.manager
:allowtitles:
```

## Module Contents

### Classes

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`SurveyManager <en_agentsociety.survey.manager.SurveyManager>`
  - ```{autodoc2-docstring} en_agentsociety.survey.manager.SurveyManager
    :summary:
    ```
````

### API

`````{py:class} SurveyManager()
:canonical: en_agentsociety.survey.manager.SurveyManager

```{autodoc2-docstring} en_agentsociety.survey.manager.SurveyManager
```

```{rubric} Initialization
```

```{autodoc2-docstring} en_agentsociety.survey.manager.SurveyManager.__init__
```

````{py:method} create_survey(title: str, description: str, pages: list[dict]) -> en_agentsociety.survey.models.Survey
:canonical: en_agentsociety.survey.manager.SurveyManager.create_survey

```{autodoc2-docstring} en_agentsociety.survey.manager.SurveyManager.create_survey
```

````

````{py:method} get_survey(survey_id: str) -> typing.Optional[en_agentsociety.survey.models.Survey]
:canonical: en_agentsociety.survey.manager.SurveyManager.get_survey

```{autodoc2-docstring} en_agentsociety.survey.manager.SurveyManager.get_survey
```

````

````{py:method} get_all_surveys() -> list[en_agentsociety.survey.models.Survey]
:canonical: en_agentsociety.survey.manager.SurveyManager.get_all_surveys

```{autodoc2-docstring} en_agentsociety.survey.manager.SurveyManager.get_all_surveys
```

````

`````
