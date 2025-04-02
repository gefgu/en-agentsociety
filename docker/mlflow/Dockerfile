ARG BASE_IMAGE
FROM ${BASE_IMAGE}

WORKDIR /mlflow
COPY ./entrypoint.sh /entrypoint.sh
COPY ./basic_auth.ini /mlflow/basic_auth.ini

EXPOSE 59000

ENTRYPOINT ["bash", "/entrypoint.sh"]
