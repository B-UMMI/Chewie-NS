#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AUTHOR

    Pedro Cerqueira
    github: @pedrorvc

    Rafael Mamede
    github: @rfm-targa

DESCRIPTION

"""


import os
import sys
import json
import time
import pickle
import shutil
import zipfile
import hashlib
import logging
import argparse
import requests
import threading
import statistics
import datetime as dt
import concurrent.futures
from collections import Counter
from SPARQLWrapper import SPARQLWrapper

from config import Config
from app.utils import sparql_queries
from app.utils import auxiliary_functions as aux


base_url = os.environ.get('BASE_URL')
local_sparql = os.environ.get('LOCAL_SPARQL')
virtuoso_graph = os.environ.get('DEFAULTHGRAPH')
virtuoso_user = os.environ.get('VIRTUOSO_USER')
virtuoso_pass = os.environ.get('VIRTUOSO_PASS')


thread_local = threading.local()


def change_date(schema_uri, date_type, date_value):
	"""
	"""

	deldate_query = (sparql_queries.DELETE_SCHEMA_DATE.format(virtuoso_graph,
															  schema_uri,
															  date_type))

	deldate_result = aux.send_data(deldate_query,
								   local_sparql,
								   virtuoso_user,
								   virtuoso_pass)

	insdate_query = (sparql_queries.INSERT_SCHEMA_DATE.format(virtuoso_graph,
															  schema_uri,
															  date_type,
															  date_value))

	insdate_result = aux.send_data(insdate_query,
								   local_sparql,
								   virtuoso_user,
								   virtuoso_pass)


def change_lock(schema_uri, action):
	"""
	"""

	del_lock_query = (sparql_queries.DELETE_SCHEMA_LOCK.format(virtuoso_graph,
															   schema_uri))

	del_lock_result = aux.send_data(del_lock_query,
									local_sparql,
									virtuoso_user,
									virtuoso_pass)

	# insert new value
	add_lock_query = (sparql_queries.INSERT_SCHEMA_LOCK.format(virtuoso_graph,
															   schema_uri,
															   action))

	add_lock_result = aux.send_data(add_lock_query,
									local_sparql,
									virtuoso_user,
									virtuoso_pass)


def create_queries(locus_file):
	"""
	"""

	with open(locus_file, 'rb') as f:
		locus_data = pickle.load(f)

	queries_file = '{0}queries'.format(locus_file.split('alleles')[0])

	locus_url = locus_data[0]
	spec_name = locus_data[1]
	user_url = locus_data[2]
	alleles = locus_data[3]

	queries = []
	allele_id = 1
	for a in alleles:
		sequence = a
		# determine hash
		sequence_hash = hashlib.sha256(sequence.encode('utf-8')).hexdigest()
		seq_url = '{0}sequences/{1}'.format(base_url, sequence_hash)

		allele_url = '{0}/alleles/{1}'.format(locus_url, allele_id)

		# determine already is in the NS
		#hash_presence = aux.get_data(SPARQLWrapper(local_sparql),
	    #                             (sparql_queries.ASK_SEQUENCE_HASH.format(seq_url)))

		#if hash_presence['boolean'] is False:
		query = (sparql_queries.INSERT_ALLELE_NEW_SEQUENCE.format(virtuoso_graph,
                                                                  seq_url,
                                                                  sequence,
                                                                  allele_url,
                                                                  spec_name,
                                                                  user_url,
                                                                  locus_url,
                                                                  str(dt.datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')),
                                                                  allele_id
                                                                  ))
		# elif hash_presence['boolean'] is True:
		# 	query = (sparql_queries.INSERT_ALLELE_LINK_SEQUENCE.format(virtuoso_graph,
	 #                                                                   allele_url,
	 #                                                                   spec_name,
	 #                                                                   user_url,
	 #                                                                   locus_url,
	 #                                                                   str(dt.datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')),
	 #                                                                   allele_id,
	 #                                                                   seq_url
	 #                                                                   ))

		queries.append(query)
		allele_id += 1

	with open(queries_file, 'wb') as qf:
		pickle.dump(queries, qf)

	return queries_file


def get_session():
    if not hasattr(thread_local, "session"):
        thread_local.session = requests.Session()
    return thread_local.session


def post_alleles(input_file):
    """
    """

    with open(input_file, 'rb') as f:
        data = pickle.load(f)

    responses = []
    session = get_session()
    headers = {'content-type': 'application/sparql-query'}
    for d in data:
        with session.post(local_sparql, data=d, headers=headers, auth=requests.auth.HTTPBasicAuth(virtuoso_user, virtuoso_pass)) as response:
            responses.append(list(response))

    return responses


def send_alleles(post_files):

    responses = []
    total = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        for res in executor.map(post_alleles, post_files):
            total += 1
            print('\r', total, end='', flush=True)
            responses.append(res)

    return responses


def unzip(zip_file, dest_dir):
	"""
	"""

	with zipfile.ZipFile(zip_file) as zf:
		zf.extractall(dest_dir)


def parse_arguments():

    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument('-i', type=str,
                        dest='input_files', required=True,
                        help='')

    args = parser.parse_args()

    return [args.input_files]


def insert_schema(temp_dir):
	"""
	"""

	start = time.time()

	# get species and schema identifiers
	species_id = os.path.basename(temp_dir).split('_')[0]
	schema_id = os.path.basename(temp_dir).split('_')[1]

	# create schema URI
	schema_uri = '{0}species/{1}/schemas/{2}'.format(base_url, species_id, schema_id)

	# list archives in temp dir
	post_files = [os.path.join(temp_dir, file) for file in os.listdir(temp_dir)]

	# extract files
	schema_files = []
	for file in post_files:
		dest_dir = os.path.dirname(file)
		unzip(file, dest_dir)
		schema_files.append(file.split('.zip')[0])

	# create SPARQL queries
	queries_files = []
	with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
		for res in executor.map(create_queries, schema_files):
			queries_files.append(res)

	# insert data
	post_results = send_alleles(queries_files)

	# change dateEntered and last_modified dates
	insert_date = str(dt.datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f'))
	change_date(schema_uri, 'dateEntered', insert_date)
	change_date(schema_uri, 'last_modified', insert_date)

	# after inserting create compressed version
	os.system('python schema_compressor.py -m single --sp {0} --sc {1}'.format(species_id, schema_id))

	# create pre-computed frontend files
	os.system('python schema_totals.py -m single_schema --sp {0} --sc {1}'.format(species_id, schema_id))
	os.system('python loci_totals.py -m single_schema --sp {0} --sc {1}'.format(species_id, schema_id))
	os.system('python loci_mode.py -m single_schema --sp {0} --sc {1}'.format(species_id, schema_id))
	os.system('python annotations.py -m single_schema --sp {0} --sc {1}'.format(species_id, schema_id))

	# unlock schema
	change_lock(schema_uri, 'Unlocked')

	# remove temp directory
	shutil.rmtree(temp_dir)

	end = time.time()
	delta = end - start
	print(delta/60, flush=True)


if __name__ == '__main__':

    args = parse_arguments()

    insert_schema(args[0])
