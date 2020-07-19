#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""

"""


import os
import logging
import subprocess

from celery import Celery
from celery.schedules import crontab


app = Celery('periodic', broker=os.environ.get('CELERY_BROKER_URL'),
						  backend=os.environ.get('CELERY_RESULT_BACKEND'))


@app.task(queue='periodic_queue')
def periodic_compressor():
	"""
	"""

	result = subprocess.check_output(['python',
    	'schema_compressor.py',
    	'-m', 'global',
    	'--g', os.environ.get('DEFAULTHGRAPH'),
    	'--s', os.environ.get('LOCAL_SPARQL'),
    	'--b', os.environ.get('BASE_URL')])


# add "periodic_compressor" task to the beat schedule
app.conf.beat_schedule = {
    "compressor-task": {
        "task": "periodic_jobs.periodic_compressor",
        "schedule": crontab(hour=0, minute=0)
    }
}

