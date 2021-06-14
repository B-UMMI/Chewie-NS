#!/bin/bash

# Build and run containers
docker-compose up -d --build

# Hack to wait for postgres container to be up before running alembic migrations
sleep 5;

# Run migrations
docker-compose run --rm backend alembic upgrade head

docker-compose exec backend alembic revision --autogenerate -m "Add columns username, name, organization, is_contributor and can_sync to User model."

docker-compose run --rm backend alembic upgrade head

# Create initial data
docker-compose run --rm backend python3 app/initial_data.py
