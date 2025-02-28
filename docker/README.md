# Dependencies installed by Docker

The folder contains the docker-compose.yml and related files for running the dependencies (PostgreSQL, MQTT Broker, mlflow) for the project quickly.

## Prerequisites

- Docker

## Install Docker

The official installation instructions can be found [here](https://docs.docker.com/get-started/get-docker/).

If you do not want to read the documentation and **the OS is Linux**, you can try the following (make sure you have the right (sudo) permission to run the script):
```bash
# If your machine is in China
curl -fsSL https://get.docker.com -o get-docker.sh && sh get-docker.sh --mirror Aliyun
# If your machine is not in China
curl -fsSL https://get.docker.com -o get-docker.sh && sh get-docker.sh
```

(Optional) After the installation, you can run the following command to check if the installation is successful:
```bash
docker run --rm hello-world
```

If you failed to run the command due to timeout, you should check your network connection to make sure that it can access the docker registry outside of China or just use the `docker-compose-cn.yml` file to start the dependencies.

Possible solutions for the timeout issue:
- Use a proxy
- Use a Docker mirror
- Use a VPN
- Use a local Docker registry

## Run the dependencies

We provide a `docker-compose.yml` file and a `docker-compose-cn.yml` file to start the dependencies.

If you are in China, you can use the `docker-compose-cn.yml` file to start the dependencies.

Before running the following command, you need to change the password in the `docker-compose.yml` (or `docker-compose-cn.yml`) and `basic_auth.ini` file.
And make sure the password part of `PG_DSN` in the `docker-compose.yml` (or `docker-compose-cn.yml`) file's `mlflow` service is the same as the `POSTGRESQL_PASSWORD` in the `docker-compose.yml` (or `docker-compose-cn.yml`) file's `postgresql` service.

```bash
cd docker # make sure the folder contains the same files as the ones in the repo
docker compose up -d # if you are not in China
docker compose -f ./docker-compose-cn.yml up # if you are in China
```

If you want to check if the dependencies are running correctly, you can run the following command instead of the above command:
```bash
cd docker
docker compose up # if you are not in China
docker compose -f ./docker-compose-cn.yml up # if you are in China
```
But you need to use `Ctrl+C` to stop the them and use `docker compose up -d` to start them again and put them in the background.

## Stop the dependencies

```bash
docker compose down # if you are not in China
docker compose -f ./docker-compose-cn.yml down # if you are in China
```

## Access the services

- MLflow: http://localhost:59000
- PostgreSQL: postgresql://postgres:CHANGE_ME@localhost:5432/postgres
  - The default username and password are `postgres` and `CHANGE_ME`, respectively.
  - The default database is `postgres`.
  - You can use some GUI tools to access the database, e.g., [DBeaver](https://dbeaver.io/).
- MQTT Broker: tcp://localhost:1883
- EMQX (MQTT Broker) Dashboard: http://localhost:18083
  - The default dashboard username and password are `admin` and `public`, respectively.
  - You can follow [EMQX Docs - Authentication](https://docs.emqx.com/en/emqx/latest/dashboard/authn.html) to set MQTT authentication.

## Attention

SECURITY WARNING:
- CHANGE THE PASSWORD OF POSTGRESQL AND MLFLOW IN THE docker-compose.yml FILE and `basic_auth.ini`.
- CHANGE THE PASSWORD OF MQTT BROKER BY ITS GUI.
- SET FIREWALL RULES ACCORDINGLY.
