# Development Guide

Now all the dependencies are publicly available or open-source in the project, you can start developing your own features or fixing bugs. This guide will help you set up your development environment and get started with contributing to the project.

## Agent Framework

Just write your codes in the `agentsociety` directory.

## WebUI

The WebUI is built using React+AntDesign and FastAPI.
The frontend code is located in the `frontend` directory and the backend code is located in the `agentsociety.webapi` directory.
The entry point (command line) of the WebUI is `agentsociety ui`.

When developing the WebUI, you can run the frontend and backend separately.

**Start the frontend**:

```bash
cd frontend
npm install
npm run dev
```

Now the frontend is running on `http://localhost:5173`.

**Start the backend**:

1. Create `config.yaml` to make you can run the backend without any parameters.

The format of `config.yaml` is

```yaml
addr: 127.0.0.1:8080
read_only: false
debug: true
logging_level: INFO
env:
  mlflow:
    enabled: true
    mlflow_uri: http://localhost:59000
    password: CHANGE_ME
    username: admin
  pgsql:
    dsn: postgresql://postgres:CHANGE_ME@localhost:5432/postgres
  redis:
    password: CHANGE_ME
    port: 6379
    server: localhost
```

2. Run the backend:

```bash
# After activating the virtual environment
agentsociety ui -c config.yaml
```

After development, YOU SHOULD RUN `scripts/rebuild_frontend.sh` TO BUILD THE FRONTEND CODE INTO THE PYTHON PACKAGE.

## Pack

After you have finished your development, you can pack the project and test it.

### Install the package locally

```bash
pip install .
```

### Build the distribution package

Current python version way (host architecture and python version):
```bash
pip install build
python -m build
```

The multiple python version way:
```bash
pip install cibuildwheel
cibuildwheel
```
