# Create Experiment on UI

To start an experiment through the web interface, the configured form on the webpage is sent to the backend, which then creates containers and launches the experiment based on the form content.

The experiment creation interface is shown in the figure below:
![create-exp](../_static/webui/exp-create.png)

Click the `Create` button shown in the figure to initiate a new experiment.

To start an experiment, you need to configure the following four forms:
- LLM Config
- Map Config
- Agent Config
- Workflow Config

After completing the selection of all four configuration forms, click the `Start experiment` button to launch your experiment.

To fill out the configuration forms, you can either click the `Create New` button or select a specific form button in the top left corner to create a new configuration.

After starting your experiment, the page will automatically redirect to the Experiment page where you can monitor the experiment's running status. For more details, please refer to [UI Home Page](./02-ui-introduction.md).
Once the experiment is completed, you can use the Goto button to view detailed information and progress.