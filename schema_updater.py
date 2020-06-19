#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Purpose
-------


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


logfile = './log_files/schema_updater.log'
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%Y-%m-%dT%H:%M:%S',
                    filename=logfile)


thread_local = threading.local()


def fasta_sequences(locus, local_sparql, virtuoso_graph):
    """ Get the DNA sequences of all alleles of a locus.

        Parameters
        ----------
        locus : str
            The URI of the locus in the Chewie-NS.
        date : str
            Last modification date of the schema in
            the format YYYY-MM-DDTHH:MM:SS.f.

        Returns
        -------
        fasta_seqs : list of dict
            A list with one dictionary per allele.
            Each dictionary has the identifier and the DNA
            sequence of an allele.
    """

    # setting [SPARQL] ResultSetMaxRows = 400000 in virtuoso.ini
    # is important to return all sequences at once
    fasta_result = aux.get_data(SPARQLWrapper(local_sparql),
                                (sq.SELECT_LOCUS_FASTA.format(virtuoso_graph, locus)))

    # virtuoso returned an error because request length exceeded maximum value of Temp Col
    # get each allele separately
    try:
        fasta_seqs = fasta_result['results']['bindings']
    # virtuoso returned an error
    # probably because sequence/request length exceeded maximum value
    except:
        logging.warning('Could not retrieve FASTA records for locus {0}\n'
                        'Response content:\n{1}\nTrying to get each sequence '
                        'separately...\n'.format(locus, fasta_result))
        # get each allele separately
        result = aux.get_data(SPARQLWrapper(local_sparql),
                              (sq.SELECT_LOCUS_SEQS.format(virtuoso_graph, locus)))
        try:
            fasta_seqs = result['results']['bindings']
            if len(fasta_seqs) == 0:
                logging.warning('Locus {0} has 0 sequences.'.format(locus))
                return False
        except:
            logging.warning('Could not retrieve sequences hashes '
                            'for locus {0}.'.format(locus))
            return False

        total = 0
        hashes = []
        for s in range(len(fasta_seqs)):
            # get the sequence corresponding to the hash
            result2 = aux.get_data(SPARQLWrapper(local_sparql),
                                   (sq.SELECT_SEQ_FASTA.format(virtuoso_graph, fasta_seqs[s]['sequence']['value'])))
            hashes.append(fasta_seqs[s]['sequence']['value'])

            fasta_seqs[s]['nucSeq'] = result2['results']['bindings'][0]['nucSeq']
            total += 1

    return fasta_seqs


def change_date(schema_uri, date_type, date_value, virtuoso_graph, local_sparql, virtuoso_user, virtuoso_pass):
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


def change_lock(schema_uri, action, virtuoso_graph, local_sparql, virtuoso_user, virtuoso_pass):
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


def create_single_insert(alleles, species, locus_uri, user_uri, start_id, base_url, virtuoso_graph, attributed):
	"""
	"""

	queries = []
	allele_id = start_id
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
		attributed[sequence_hash] = allele_id

		allele_id += 1

	return [queries, attributed]


def create_multiple_insert(alleles, species, locus_uri, user_uri, start_id, base_url, virtuoso_graph, attributed):
	"""
	"""

	queries = []
	allele_id = start_id
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
		attributed[sequence_hash] = allele_id

		if len(allele_set) == max_alleles or i == (len(alleles)-1):
			query = (sq.MULTIPLE_INSERT_NEW_SEQUENCE.format(virtuoso_graph, ' '.join(allele_set)))
			queries.append(query)
			allele_set = []

		allele_id += 1

	return [queries, attributed]


def create_queries(locus_file, virtuoso_graph, local_sparql, base_url):
	"""
	"""

	# get sequences sent by user
	with open(locus_file, 'rb') as f:
		locus_data = pickle.load(f)

	locus_url = locus_data[0]
	locus_id = locus_url.split('/')[-1]

	# get sequences in the NS
	sequences = fasta_sequences(locus_url, local_sparql, virtuoso_graph)
	ns_seqs = fasta_seqs = {f['nucSeq']['value']: f['allele_id']['value'] for f in sequences}

	# count number of alleles for locus
	count_query = (sq.COUNT_LOCUS_ALLELES.format(virtuoso_graph,
											  	 locus_url))

	count_res = aux.get_data(SPARQLWrapper(local_sparql),
                                  		   count_query)

	start_id = int(count_res['results']['bindings'][0]['count']['value']) + 1

	spec_name = locus_data[1]
	user_url = locus_data[2]
	alleles = locus_data[3]
	novel = [a for a in alleles if a not in ns_seqs]
	repeated = {hashlib.sha256(a.encode('utf-8')).hexdigest(): ns_seqs[a] for a in alleles if a in ns_seqs}
	
	attributed = {}
	if len(novel) > 0:
		max_length = max([len(a) for a in novel])
		if max_length < 7000:
			queries, attributed = create_multiple_insert(novel, spec_name, locus_url,
				                                         user_url, start_id, base_url,
				                                         virtuoso_graph, attributed)
		else:
			queries, attributed = create_single_insert(novel, spec_name, locus_url,
				                                       user_url, start_id, base_url,
				                                       virtuoso_graph, attributed)

		queries_file = '{0}_queries'.format(locus_file.split('alleles')[0])
		with open(queries_file, 'wb') as qf:
			pickle.dump(queries, qf)

		return [queries_file, locus_id, repeated, attributed]
	else:
		return [None, locus_id, repeated, attributed]


def get_session():
    if not hasattr(thread_local, "session"):
        thread_local.session = requests.Session()
    return thread_local.session


def post_alleles(input_file, local_sparql, virtuoso_user, virtuoso_pass):
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


def send_alleles(post_files, local_sparql, virtuoso_user, virtuoso_pass):
	"""
	"""

	responses = []
	total = 0
	with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
		for res in executor.map(post_alleles, post_files, repeat(local_sparql), repeat(virtuoso_user), repeat(virtuoso_pass)):
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
                        dest='input_dir', required=True,
                        help='Temporary directory that '
                             'receives the data necessary '
                             'for schema insertion. It must '
                             'contain the ZIP archives with the '
                             'data to insert alleles.')

    parser.add_argument('--g', type=str,
                        dest='virtuoso_graph', required=True,
                        default=os.environ.get('DEFAULTHGRAPH'),
                        help='')

    parser.add_argument('--s', type=str,
                        dest='local_sparql', required=True,
                        default=os.environ.get('LOCAL_SPARQL'),
                        help='')

    parser.add_argument('--b', type=str,
                        dest='base_url', required=True,
                        default=os.environ.get('BASE_URL'),
                        help='')

    parser.add_argument('--u', type=str,
                        dest='virtuoso_user', required=True,
                        default=os.environ.get('VIRTUOSO_USER'),
                        help='')

    parser.add_argument('--p', type=str,
                        dest='virtuoso_pass', required=True,
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

	post_files = [os.path.join(temp_dir, file) for file in os.listdir(temp_dir)]

	# extract files
	schema_files = []
	for file in post_files:
		dest_dir = os.path.dirname(file)
		locus_file = unzip(file, dest_dir)
		locus_file = os.path.join(temp_dir, locus_file)
		schema_files.append(locus_file)

	# create SPARQL multiple INSERT queries
	identifiers = {}
	queries_files = []
	with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
		for res in executor.map(create_queries, schema_files, repeat(graph), repeat(sparql), repeat(base_url)):
			if res[0] is not None:
				queries_files.append(res[0])
			identifiers[res[1]] = [res[2], res[3]]

	start = time.time()
	# insert data
	# sort reponses to include summary in log file
	post_results = send_alleles(queries_files, sparql, user, password)

	# create file with identifiers
	identifiers_file = os.path.join(temp_dir, 'identifiers')
	with open(identifiers_file, 'wb') as rf:
		pickle.dump(identifiers, rf)

	end = time.time()
	delta = end - start
	print('Insertion: {0}'.format(delta), flush=True)

	# change dateEntered and last_modified dates
	modification_date = str(dt.datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f'))
	change_date(schema_uri, 'last_modified', modification_date,
		                     graph, sparql, user, password)

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
	change_lock(schema_uri, 'Unlocked',
		        graph, sparql, user, password)

	# remove temp directory
	#shutil.rmtree(temp_dir)


if __name__ == '__main__':

    args = parse_arguments()

    main(args[0], args[1], args[2],
         args[3], args[4], args[5])
