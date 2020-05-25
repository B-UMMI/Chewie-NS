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
#import logging
import argparse
import requests
import threading
import statistics
import datetime as dt
import concurrent.futures
from collections import Counter
from SPARQLWrapper import SPARQLWrapper

from config import Config
from app.utils import sparql_queries as sq
from app.utils import auxiliary_functions as aux


base_url = os.environ.get('BASE_URL')
local_sparql = os.environ.get('LOCAL_SPARQL')
virtuoso_graph = os.environ.get('DEFAULTHGRAPH')
virtuoso_user = os.environ.get('VIRTUOSO_USER')
virtuoso_pass = os.environ.get('VIRTUOSO_PASS')
#logfile = './log_files/schema_alleles_inserter.log'
#logging.basicConfig(filename=logfile, level=logging.INFO)


thread_local = threading.local()


def change_date(schema_uri, date_type, date_value):
	"""
	"""

	deldate_query = (sq.DELETE_SCHEMA_DATE.format(virtuoso_graph,
															  schema_uri,
															  date_type))

	deldate_result = aux.send_data(deldate_query,
								   local_sparql,
								   virtuoso_user,
								   virtuoso_pass)

	insdate_query = (sq.INSERT_SCHEMA_DATE.format(virtuoso_graph,
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

	del_lock_query = (sq.DELETE_SCHEMA_LOCK.format(virtuoso_graph,
															   schema_uri))

	del_lock_result = aux.send_data(del_lock_query,
									local_sparql,
									virtuoso_user,
									virtuoso_pass)

	# insert new value
	add_lock_query = (sq.INSERT_SCHEMA_LOCK.format(virtuoso_graph,
															   schema_uri,
															   action))

	add_lock_result = aux.send_data(add_lock_query,
									local_sparql,
									virtuoso_user,
									virtuoso_pass)


def create_single_insert(alleles, species, locus_uri, user_uri):
	"""
	"""

	queries = []
	allele_id = 1
	for a in alleles:
		sequence = a
		# determine sequence hash
		sequence_hash = hashlib.sha256(sequence.encode('utf-8')).hexdigest()
		seq_uri = '{0}sequences/{1}'.format(base_url, sequence_hash)

		allele_uri = '{0}/alleles/{1}'.format(locus_uri, allele_id)

		insert_date = str(dt.datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f'))

		query = (sq.INSERT_ALLELE_NEW_SEQUENCE.format(virtuoso_graph, seq_uri,
													  sequence, allele_uri,
													  species, user_uri,
													  locus_uri, insert_date,
													  allele_id))
		queries.append(query)

		allele_id += 1

	return queries


def create_multiple_insert(alleles, species, locus_uri, user_uri):
	"""
	"""

	queries = []
	allele_id = 1
	allele_set = []
	max_alleles = 100
	for a in alleles:
		sequence = a
		# determine hash
		sequence_hash = hashlib.sha256(sequence.encode('utf-8')).hexdigest()
		seq_uri = '{0}sequences/{1}'.format(base_url, sequence_hash)

		allele_uri = '{0}/alleles/{1}'.format(locus_uri, allele_id)

		insert_date = str(dt.datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f'))

		allele_set.append('({0} {1} {2} {3}'
						  ' {4} {5} {6} {7})'.format('<{0}>'.format(seq_uri),
													 '"{0}"^^xsd:string'.format(sequence),
													 '<{0}>'.format(allele_uri),
													 '"{0}"^^xsd:string'.format(species),
													 '<{0}>'.format(user_uri),
													 '<{0}>'.format(locus_uri),
													 '"{0}"^^xsd:dateTime'.format(insert_date),
													 '"{0}"^^xsd:integer'.format(allele_id)))

		if len(allele_set) == max_alleles:
			query = (sq.MULTIPLE_INSERT_NEW_SEQUENCE.format(virtuoso_graph, ' '.join(allele_set)))
			queries.append(query)
			allele_set = []

		allele_id += 1

	if len(allele_set) > 0:
		query = (sq.MULTIPLE_INSERT_NEW_SEQUENCE.format(virtuoso_graph, ' '.join(allele_set)))
		queries.append(query)

	return queries


def create_queries(locus_file):
	"""
	"""

	with open(locus_file, 'rb') as f:
		locus_data = pickle.load(f)

	locus_url = locus_data[0]
	spec_name = locus_data[1]
	user_url = locus_data[2]
	alleles = locus_data[3]
	# compute mean length
	max_length = max([len(a) for a in alleles])

	if max_length < 7000:
		queries = create_multiple_insert(alleles, spec_name,
									   	 locus_url, user_url)
	else:
		queries = create_single_insert(alleles, spec_name,
									   locus_url, user_url)

	queries_file = '{0}_queries'.format(locus_file.split('alleles')[0])
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
		locus_data = pickle.load(f)

	responses = []
	session = get_session()
	headers = {'content-type': 'application/sparql-query'}
	for d in locus_data:
		tries = 0
		max_tries = 5
		valid = False
		while valid is False:
			with session.post(local_sparql, data=d, headers=headers, auth=requests.auth.HTTPBasicAuth(virtuoso_user, virtuoso_pass)) as response:
				if response.status_code > 201:
					tries += 1
					print('failed', response.status_code, tries)
					with open('errors.txt', 'a') as f:
						f.write(response.text)
					if tries < max_tries:
						time.sleep(1)
					else:
						valid = True
						responses.append(list(response))
				else:
					valid = True
					responses.append(list(response))

	return responses


def send_alleles(post_files):
	"""
	"""

	responses = []
	total = 0
	with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
		for res in executor.map(post_alleles, post_files):
			responses.append(res)
			total += 1

	return responses


def unzip(zip_file, dest_dir):
	"""
	"""

	with zipfile.ZipFile(zip_file) as zf:
		zipinfo = zf.infolist()
		locus_file = zipinfo[0].filename
		zf.extractall(dest_dir)

	return locus_file


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

	# schemas hashes are the filenames
	schema_file = os.path.join(temp_dir, '{0}_{1}_hashes'.format(species_id, schema_id))
	with open(schema_file, 'rb') as sh:
		schema_vals = pickle.load(sh)
		schema_hashes = schema_vals.keys()

	post_files = [os.path.join(temp_dir, file) for file in schema_hashes]
	if all([os.path.isfile(file) for file in post_files]) is False:
		sys.exit(1)

	# extract files
	schema_files = []
	for file in post_files:
		dest_dir = os.path.dirname(file)
		locus_file = unzip(file, dest_dir)
		locus_file = os.path.join(temp_dir, locus_file)
		schema_files.append(locus_file)

	# create SPARQL multiple INSERT queries
	queries_files = []
	with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
		for res in executor.map(create_queries, schema_files):
			queries_files.append(res)

	start = time.time()
	# insert data
	# sort reponses to include summary in log file
	post_results = send_alleles(queries_files)

	end = time.time()
	delta = end - start
	print('Insertion: {0}'.format(delta), flush=True)

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


if __name__ == '__main__':

    args = parse_arguments()

    insert_schema(args[0])
