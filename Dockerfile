#Dockerfile
FROM public.ecr.aws/lambda/python:3.12

ARG FUNCTION_ROOT_DIR="/var/task"
 
# Create function directory
RUN mkdir -p ${FUNCTION_ROOT_DIR}/solvis_graphql_api

# The lamba service functions
COPY ./solvis_graphql_api/ ${FUNCTION_ROOT_DIR}/solvis_graphql_api
COPY requirements.txt ${FUNCTION_ROOT_DIR}

WORKDIR ${FUNCTION_ROOT_DIR}

RUN dnf install git-core -y &&\
    pip install --upgrade pip &&\
    pip3 install -r requirements.txt &&\
    pip cache purge &&\
    dnf remove git-core -y &&\
    dnf clean all

# lambda entry point — Mangum handler (was the serverless-wsgi handler.py workaround).
# ENTRYPOINT is the base image's Runtime Interface Client (/lambda-entrypoint.sh); CMD is
# the handler. Matches serverless.yml functions.ecr-app.image.{entryPoint,command}.
CMD ["solvis_graphql_api.app.handler"]
