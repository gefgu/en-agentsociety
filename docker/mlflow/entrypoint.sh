#!/bin/bash

python -m mlflow.server.auth db upgrade --url sqlite:///basic_auth.db

mlflow server --backend-store-uri $PG_DSN --app-name basic-auth --host 0.0.0.0:59000
