import datetime as dt
import os

from app.api.dependencies import auxiliary_functions as aux
from app.api.dependencies import sparql_queries as sq
from app.core.celery_app import celery_app

# from aiosparql.client import SPARQLClient, SPARQLRequestFailed

from SPARQLWrapper import SPARQLWrapper


@celery_app.task(acks_late=True)
def example_task2(word: str) -> str:
    print(f"test task 2 returns {word}")
    return f"test task 2 returns {word}"
