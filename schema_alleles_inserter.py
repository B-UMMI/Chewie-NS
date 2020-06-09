#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Purpose
-------

This module adds alleles to loci during the schema uploading
process. After the complete set of alleles has been uploaded
to the Chewie-NS, this module continues the schema upload
process. After inserting all alleles, the process will also
create the first compressed version of the schema, generate
the pre-computed files for the Frontend and unlock the schema
to make it fully available.

Expected input
--------------

The process expects the following variables whether through command line
execution or invocation of the :py:func:`main` function:

- ``-i``, ``input_dir`` : Temporary directory that receives the data
  necessary for schema insertion. It must contain the ZIP archives
  with the data to insert alleles.

Code documentation
------------------
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
from itertools import repeat
from collections import Counter
from SPARQLWrapper import SPARQLWrapper

from config import Config
from app.utils import sparql_queries as sq
from app.utils import auxiliary_functions as aux


logfile = './log_files/schema_alleles_inserter.log'
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%Y-%m-%dT%H:%M:%S',
                    filename=logfile)


thread_local = threading.local()


def change_date(schema_uri, date_type, date_value, virtuoso_graph, local_sparql, virtuoso_user, virtuoso_pass):
    """ Changes the last modification date or date of insertion
        of a schema.

        Parameters
        ----------
        schema_uri : str
            The URI of the schema in the Chewie-NS.
        date_type : str
            The type of the date to change, 'dateEntered' or
            'last_modified'.
        date_value : str
            The new date, in the format YYYY-MM-DDTHH:MM:SS.f.

        Returns
        -------
        True if the action is performed successfully,
        False and request response object otherwise.
    """

    deldate_query = (sq.DELETE_SCHEMA_DATE.format(virtuoso_graph,
                                                  schema_uri,
                                                  date_type))

    deldate_result = aux.send_data(deldate_query,
								   local_sparql,
								   virtuoso_user,
								   virtuoso_pass)

    del_status = deldate_result.status_code
    if del_status > 201:
        return [False, deldate_result.content]
    else:
        insdate_query = (sq.INSERT_SCHEMA_DATE.format(virtuoso_graph,
													  schema_uri,
													  date_type,
													  date_value))

        insdate_result = aux.send_data(insdate_query,
									   local_sparql,
									   virtuoso_user,
									   virtuoso_pass)
        ins_status = insdate_result.status_code
        if ins_status > 201:
            return [False, insdate_result.content]
        else:
            return True


def change_lock(schema_uri, action, virtuoso_graph, local_sparql, virtuoso_user, virtuoso_pass):
    """ Changes the locking state of a schema in the Chewie-NS.

        Parameters
        ----------
        schema_uri : str
            The URI of the schema in the Chewie-NS.
        action : str
            'LOCKED' if the schema should be locked or
            'Unlocked' if it should be unlocked.

        Returns
        -------
        True if the action is performed successfully,
        False and request response otherwise.
    """

    del_lock_query = (sq.DELETE_SCHEMA_LOCK.format(virtuoso_graph,
                                                   schema_uri))

    del_lock_result = aux.send_data(del_lock_query,
                                    local_sparql,
                                    virtuoso_user,
                                    virtuoso_pass)

    del_status = del_lock_result.status_code
    if del_status > 201:
        return [False, del_lock_result.content]
    else:
        # insert new locking value
        add_lock_query = (sq.INSERT_SCHEMA_LOCK.format(virtuoso_graph,
                                                       schema_uri,
                                                       action))

        add_lock_result = aux.send_data(add_lock_query,
                                        local_sparql,
                                        virtuoso_user,
                                        virtuoso_pass)
        add_status = add_lock_result.status_code
        if add_status > 201:
            return [False, add_lock_result.content]
        else:
            return True


def create_single_insert(alleles, species, locus_uri, user_uri, base_url, virtuoso_graph):
	""" Creates SPARQL queries that allow the insertion of a single allele.

		Parameters
		----------
		alleles : tup
		    A tuple with alleles DNA sequences.
		species : str
            Scientific name of the species the alleles
            were identified in.
        locus_uri : str
            URI of the locus in the Chewie-NS.
        user_uri : str
            URI of the user that sent the data to the Chewie-NS.

		Returns
		-------
		queries : list
		    A list with two elements: the locus URI and
		    a sublist with the single-insert queries to
		    insert alleles.
	"""

	queries = [locus_uri, []]
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
		queries[1].append(query)

		allele_id += 1

	return queries


def create_multiple_insert(alleles, species, locus_uri, user_uri, base_url, virtuoso_graph):
	""" Creates SPARQL queries that alow the insertion of multiple alleles.

        Parameters
        ----------
        alleles : tup
		    A tuple with alleles DNA sequences.
        species : str
			Scientific name of the species the alleles
            were identified in.
        locus_uri : str
			URI of the locus in the Chewie-NS.
        user_uri : str
			URI of the user that sent the data to the Chewie-NS.

        Returns
        -------
        queries : list
			A list with two elements: the locus URI and
		    a sublist with the multi-insert queries to
		    insert alleles.
	"""

	queries = [locus_uri, []]
	allele_id = 1
	allele_set = []
	max_alleles = 100
	for i, a in enumerate(alleles):
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

		if len(allele_set) == max_alleles or i == (len(alleles)-1):
			query = (sq.MULTIPLE_INSERT_NEW_SEQUENCE.format(virtuoso_graph, ' '.join(allele_set)))
			queries[1].append(query)
			allele_set = []

		allele_id += 1

	return queries


def create_queries(locus_file, base_url, virtuoso_graph):
	""" Creates SPARQL queries to insert alleles.

		Parameters
		----------
		locus_file : str
		    Path to the file with the data necessary
		    to create the SPARQL queries. The file is
		    a pickled file with a list that contains the
		    following elements:

		    - The locus URI in the Chewie-NS.
		    - The scientific name the locus/alleles were
		      identified in.
		    - The URI of the user that sent the data to
		      the Chewie-NS.
		    - A tuple with the alleles that belong to the
		      locus.

		Returns
		-------
		queries_file : str
		    Path to the file with the queries that were
		    created to insert the alleles into the Chewie-NS.
	"""

	with open(locus_file, 'rb') as f:
		locus_data = pickle.load(f)

	locus_url = locus_data[0]
	spec_name = locus_data[1]
	user_url = locus_data[2]
	alleles = locus_data[3]
	# compute mean length
	max_length = max([len(a) for a in alleles])

	# multi-insert queries that contain alleles with more than ~8000 bps
	# might not be inserted
	if max_length < 4000:
		queries = create_multiple_insert(alleles, spec_name,
									   	 locus_url, user_url,
									   	 base_url, virtuoso_graph)
	else:
		queries = create_single_insert(alleles, spec_name,
									   locus_url, user_url,
									   base_url, virtuoso_graph)

	queries_file = '{0}_queries'.format(locus_file.split('alleles')[0])
	with open(queries_file, 'wb') as qf:
		pickle.dump(queries, qf)

	return queries_file


def get_session():
    """ Creates a Session object for a thread.

        Creating a Session object allows the 
        persistance of certain parameters across
        requests. It is best to create one Session
        object per thread to ensure that the process
        is threadsafe. Using a Session object will
        make the process faster when compared to
        simply using the get() or post() methods
        from the requests package.

        Returns
        -------
        A Session object.
    """

    if not hasattr(thread_local, "session"):
        thread_local.session = requests.Session()

    return thread_local.session


def post_alleles(input_file, local_sparql, virtuoso_user, virtuoso_pass):
	""" Sends POST requests to insert alleles of a locus
	    into the Chewie-NS.

        Parameters
        ----------
        input_file : str
            Path to a pickled file with SPARQL queries to
            insert alleles into the Chewie-NS.

        Returns
        -------
        responses : list
		    A list with the response objects for all queries
		    that were sent to Virtuoso's SPARQL endpoint in
		    order to insert alleles.
    """

	with open(input_file, 'rb') as f:
		locus_data = pickle.load(f)
		locus = locus_data[0]
		queries = locus_data[1]

	responses = [locus, []]
	session = get_session()
	headers = {'content-type': 'application/sparql-query'}
	for q in queries:
		tries = 0
		max_tries = 5
		max_wait = 5
		valid = False
		while valid is False and tries < max_tries:
			with session.post(local_sparql, data=q, headers=headers,
				              auth=requests.auth.HTTPBasicAuth(virtuoso_user, virtuoso_pass)) as response:
				status_code = response.status_code
				if status_code > 201:
					tries += 1
					logging.warning('Could not insert query for locus {0}'
						            '\nResponse:\n{1}\n'.format(locus, response.text))
					# wait some time, a 404 error can occur when Virtuoso
					# performs checkpoint() and waiting coupled with retries
					# will help resume POST after checkpoint ends
					time.sleep(max_wait)
					max_wait += max_wait
				else:
					valid = True
		responses[1].append(response)
		if status_code > 201:
			logging.warning('Could not execute query for locus {0}'
				            '\nQuery:\n{1}\n'.format(locus, q))

	return responses


def send_alleles(post_files, local_sparql, virtuoso_user, virtuoso_pass):
	""" Sends POST requests to insert alleles of a set of loci.

		Parameters
		----------
		post_files : list
		    A list with paths to pickled files with SPARQL
		    queries.

		Return
		------
		responses : dict
		    A dictionary with loci 
	"""

	responses = {}
	total = 0
	with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
		for res in executor.map(post_alleles, post_files, repeat(local_sparql), repeat(virtuoso_user), repeat(virtuoso_pass)):
			responses[res[0]] = res[1]
			total += 1

	return responses


def unzip(zip_file, dest_dir):
	""" Unzips a ZIP archive.

		Parameters
		----------
		zip_file : str
		    Path to the ZIP archive to be
		    extracted.
		dest_dir : str
		    Path to where ZIP contents will
		    be extracted.

		Returns
		-------
		locus_file : str
		    Path to extracted file.
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
                        dest='input_dir', required=True,
                        help='Temporary directory that '
                             'receives the data necessary '
                             'for schema insertion. It must '
                             'contain the ZIP archives with the '
                             'data to insert alleles.')

    parser.add_argument('--g', type=str,
                        dest='virtuoso_graph',
                        default=os.environ.get('DEFAULTHGRAPH'),
                        help='')

    parser.add_argument('--s', type=str,
                        dest='local_sparql',
                        default=os.environ.get('LOCAL_SPARQL'),
                        help='')

    parser.add_argument('--b', type=str,
                        dest='base_url',
                        default=os.environ.get('BASE_URL'),
                        help='')

    parser.add_argument('--u', type=str,
                        dest='virtuoso_user',
                        default=os.environ.get('VIRTUOSO_USER'),
                        help='')

    parser.add_argument('--p', type=str,
                        dest='virtuoso_pass',
                        default=os.environ.get('VIRTUOSO_PASS'),
                        help='')

    args = parser.parse_args()

    return [args.input_dir, args.virtuoso_graph,
            args.local_sparql, args.base_url,
            args.virtuoso_user, args.virtuoso_pass]


def main(temp_dir, graph, sparql, base_url, user, password):

	start = time.time()

	# get species and schema identifiers
	species_id = os.path.basename(temp_dir).split('_')[0]
	schema_id = os.path.basename(temp_dir).split('_')[1]

	# create schema URI
	schema_uri = '{0}species/{1}/schemas/{2}'.format(base_url, species_id, schema_id)

	logging.info('Started alleles insertion for schema {0}'.format(schema_uri))

	# schemas hashes are the filenames
	schema_file = os.path.join(temp_dir, '{0}_{1}_hashes'.format(species_id, schema_id))
	with open(schema_file, 'rb') as sh:
		schema_vals = pickle.load(sh)
		schema_hashes = schema_vals.keys()

	post_files = [os.path.join(temp_dir, file) for file in schema_hashes]
	if all([os.path.isfile(file) for file in post_files]) is False:
		logging.warning('Missing files with data for alleles insertion.\n\n')
		sys.exit(1)

	# extract files
	schema_files = []
	dest_dir = os.path.dirname(post_files[0])
	for file in post_files:
		locus_file = unzip(file, dest_dir)
		locus_file = os.path.join(temp_dir, locus_file)
		schema_files.append(locus_file)

	# create SPARQL multiple INSERT queries
	queries_files = []
	with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
		for res in executor.map(create_queries, schema_files, repeat(base_url), repeat(graph)):
			queries_files.append(res)

	start = time.time()
	# insert data
	# sort reponses to include summary in log file
	post_results = send_alleles(queries_files, sparql, user, password)

	end = time.time()
	delta = end - start
	print('Insertion: {0}'.format(delta), flush=True)

	# change dateEntered and last_modified dates
	insert_date = str(dt.datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f'))
	insert_res = change_date(schema_uri, 'dateEntered', insert_date,
		                     graph, sparql, user, password)
	modification_res = change_date(schema_uri, 'last_modified', insert_date,
		                           graph, sparql, user, password)

	# after inserting create compressed version
	os.system('python schema_compressor.py -m single '
		      '--sp {0} --sc {1} --g {2} --s {3} '
		      '--b {4} --u {5} --p {6}'.format(species_id, schema_id,
		      	               				   graph, sparql, base_url,
		      	               				   user, password))

	# create pre-computed frontend files
	os.system('python schema_totals.py -m single_schema '
		      '--sp {0} --sc {1} --g {2} --s {3} --b {4}'
		      ''.format(species_id, schema_id, graph, sparql, base_url))
	os.system('python loci_totals.py -m single_schema '
		      '--sp {0} --sc {1} --g {2} --s {3} --b {4}'
		      ''.format(species_id, schema_id, graph, sparql, base_url))
	os.system('python loci_mode.py -m single_schema '
		      '--sp {0} --sc {1} --g {2} --s {3} --b {4}'
		      ''.format(species_id, schema_id, graph, sparql, base_url))
	os.system('python annotations.py -m single_schema '
		      '--sp {0} --sc {1} --g {2} --s {3} --b {4}'
		      ''.format(species_id, schema_id, graph, sparql, base_url))

	# unlock schema
	unlocked = change_lock(schema_uri, 'Unlocked',
		                   graph, sparql, user, password)
	if isinstance(unlocked, list) is True:
		logging.warning('Could not unlock schema. Response:'
			            '\n{0}\n\n'.format(unlocked[1]))

	# remove temp directory
	shutil.rmtree(temp_dir)


if __name__ == '__main__':

    args = parse_arguments()

    main(args[0], args[1], args[2],
         args[3], args[4], args[5])
