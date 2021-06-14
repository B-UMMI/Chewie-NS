FROM python:3.8.3-slim-buster

# set working directory
RUN mkdir /app
WORKDIR /app

# set environment varibles
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# set Virtuoso environment variables
ENV DEFAULT_GRAPH http://localhost:8890/chewiens
ENV VIRTUOSO_DB_USER demo
ENV VIRTUOSO_DB_PASSWORD chewiens
ENV DBA_PASSWORD ummi
ENV DAV_PASSWORD ummi
ENV LOCAL_SPARQL http://172.19.1.3:8890/sparql
ENV BASE_URL http://127.0.0.1:5000/NS/api/
ENV UNIPROT_SPARQL http://sparql.uniprot.org/sparql
# file transfer configs
ENV SCHEMAS_PTF ./prodigal_training_files
ENV SCHEMAS_ZIP ./compressed_schemas

# pre-computed stats for frontend
ENV PRE_COMPUTE ./pre-computed-data

# schema upload directory
ENV SCHEMA_UP ./schema_insertion_temp

# install system dependencies
RUN apt-get update \
    && apt-get install -y postgresql-client \
    && apt-get clean

# install python dependencies
RUN pip install --upgrade pip
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
