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
import logging
import argparse
import statistics
import datetime as dt
from collections import Counter
from SPARQLWrapper import SPARQLWrapper

from config import Config
from app.utils import sparql_queries
from app.utils import auxiliary_functions as aux


logfile = './log_files/schema_annotations.log'
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%Y-%m-%dT%H:%M:%S',
                    filename=logfile)


def create_file(filename, header):
	"""
	"""
	
	with open(filename, 'w') as json_outfile:
		json.dump(header, json_outfile)

	return os.path.isfile(filename)


def count_alleles(schema, virtuoso_graph, local_sparql):
	"""
	"""

	# get total number of alleles
	loci = aux.get_data(SPARQLWrapper(local_sparql),
				  		sparql_queries.COUNT_SCHEMA_ALLELES.format(virtuoso_graph, schema))

	loci = loci['results']['bindings']
	total_alleles = sum(map(int, [a['nr_allele']['value'] for a in loci]))
	
	return total_alleles


def alleles_lengths(total_alleles, schema, offset, limit,
	                virtuoso_graph, local_sparql):
	"""
	"""

	limit = limit
	offset = offset
	count = 0
	result = []
	while count != total_alleles:
		alleles = aux.get_data(SPARQLWrapper(local_sparql),
					  		   sparql_queries.SELECT_ALLELES_LENGTH.format(virtuoso_graph, schema, offset, limit))

		data = alleles['results']['bindings']

		result.extend(data)
		count += len(data)
		offset += limit

	return result


def loci_alleles_length(alleles):
	"""
	"""

	loci_data = {}
	for a in alleles:
		loci_data.setdefault(a['name']['value'], []).append(int(a['nucSeqLen']['value']))

	return loci_data

def loci_annotations(schema, virtuoso_graph, local_sparql):
	"""
	"""

	# get total number of alleles
	tries = 0
	bah = False
	while bah is False:
		loci = aux.get_data(SPARQLWrapper(local_sparql),
					  		sparql_queries.SELECT_SCHEMA_LOCI_ANNOTATIONS.format(virtuoso_graph, schema))

		try:
			annotations = loci['results']['bindings']
			bah = True
		except:
			print(sparql_queries.SELECT_SCHEMA_LOCI_ANNOTATIONS.format(virtuoso_graph, schema))
			logging.warning('Could not get annotations.')
			logging.warning(loci)
			tries += 1

		if tries == 5:
			sys.exit('This schema makes no sense!')

	annotations = [{'locus': l['locus']['value'],
					'name': l['name']['value'],
					'UniprotName': l['UniprotName']['value'],
					'UniprotURI': l['UniprotURI']['value'],
					'UserAnnotation': l['UserAnnotation']['value'],
					'CustomAnnotation': l['CustomAnnotation']['value']} for l in annotations]

	return annotations


def loci_stats(loci_data):
	"""
	"""

	total_alleles = {k: len(v) for k, v in loci_data.items()}
	modes = {k: Counter(v).most_common()[0][0] for k, v in loci_data.items()}

	return [total_alleles, modes]


def generate_info(schema, last_modified, virtuoso_graph, local_sparql):
	"""
	"""

	# get loci annotations
	annotations = loci_annotations(schema, virtuoso_graph, local_sparql)

	# get total number of alleles
	total_alleles = count_alleles(schema, virtuoso_graph, local_sparql)

	result = alleles_lengths(total_alleles, schema, 0, 10000,
		                     virtuoso_graph, local_sparql)

	loci_data = loci_alleles_length(result)

	total_alleles, modes = loci_stats(loci_data)

	for a in annotations:
		locus = a['name']
		a['mode'] = modes[locus]
		a['nr_alleles'] = total_alleles[locus]

	json_to_file = {'schema': schema,
					'last_modified': last_modified,
					'message': annotations}

	return json_to_file


def fast_update(schema, last_modified, file, lengths_dir,
	            virtuoso_graph, local_sparql):
	"""
	"""

	schema_id = int(schema.split('/')[-1])
	current_file = file

	# read current file
	with open(current_file, 'r') as json_file:
		json_data = json.load(json_file)

	loci_info = json_data['message']

	# get schema loci
	loci = aux.get_data(SPARQLWrapper(local_sparql),
						sparql_queries.SELECT_SCHEMA_LOCI.format(virtuoso_graph, schema))
	loci = loci['results']['bindings']
	loci_names = {l['locus']['value']: l['name']['value'] for l in loci}

	if len(loci_info) == 0:
		length_files = [os.path.join(lengths_dir, f) for f in os.listdir(lengths_dir)]

		loci_stats = {}
		for locus_file in length_files:
			with open(locus_file, 'rb') as lf:
				locus_data = pickle.load(lf)

			locus_uri = list(locus_data.keys())[0]
			locus_name = loci_names[locus_uri]
			alleles_lengths = [v for k, v in locus_data[locus_uri].items()]
			total_alleles = len(alleles_lengths)
			locus_mode = Counter(alleles_lengths).most_common()[0][0]
			loci_stats[locus_name] = [locus_mode, total_alleles]

		annotations = loci_annotations(schema, virtuoso_graph, local_sparql)
		for a in annotations:
			locus = a['name']
			a['mode'] = loci_stats[locus][0]
			a['nr_alleles'] = loci_stats[locus][1]

		json_to_file = {'schema': schema,
						'last_modified': last_modified,
						'message': annotations}

		with open(file, 'w') as json_outfile:
			json.dump(json_to_file, json_outfile)

	# if the schema is in the json file
	elif len(loci_info) > 0:
		# get modification date in json file
		json_date = json_data['last_modified']
		virtuoso_date = last_modified

		if json_date == virtuoso_date:
			logging.info('Information about loci annotations and length modes for schema {0} is up-to-date.'.format(schema))

		elif json_date != virtuoso_date:
			length_files = [os.path.join(lengths_dir, f) for f in os.listdir(lengths_dir)]

			loci_stats = {}
			for locus_file in length_files:
				with open(locus_file, 'rb') as lf:
					locus_data = pickle.load(lf)

				locus_uri = list(locus_data.keys())[0]
				locus_name = loci_names[locus_uri]
				alleles_lengths = [v for k, v in locus_data[locus_uri].items()]
				total_alleles = len(alleles_lengths)
				locus_mode = Counter(alleles_lengths).most_common()[0][0]
				loci_stats[locus_name] = [locus_mode, total_alleles]

			annotations = loci_annotations(schema, virtuoso_graph, local_sparql)
			for a in annotations:
				locus = a['name']
				a['mode'] = loci_stats[locus][0]
				a['nr_alleles'] = loci_stats[locus][1]

			json_to_file = {'schema': schema,
							'last_modified': last_modified,
							'message': annotations}

			with open(file, 'w') as json_outfile:
				json.dump(json_to_file, json_outfile)

			logging.info('Updated data for schema {0}'.format(schema))


def full_update(schema, last_modified, file, virtuoso_graph, local_sparql):
	"""
	"""

	schema_id = int(schema.split('/')[-1])
	current_file = file

	# read current file
	with open(current_file, 'r') as json_file:
		json_data = json.load(json_file)

	loci_info = json_data['message']

	if len(loci_info) == 0:
		json_to_file = generate_info(schema, last_modified,
			                         virtuoso_graph, local_sparql)
		with open(file, 'w') as json_outfile:
			json.dump(json_to_file, json_outfile)
		
	# if the schema is in the json file
	elif len(loci_info) > 0:
		# get modification date in json file
		json_date = json_data['last_modified']
		virtuoso_date = last_modified

		if json_date == virtuoso_date:
			logging.info('Information about number  for schema {0} is up-to-date.'.format(schema))

		elif json_date != virtuoso_date:
			json_to_file = generate_info(schema, last_modified,
				                         virtuoso_graph, local_sparql)
			with open(file, 'w') as json_outfile:
				json.dump(json_to_file, json_outfile)

			logging.info('Updated data for schema {0}'.format())


def parse_arguments():

    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument('-m', type=str,
                        dest='mode', required=True,
                        choices=['global_species', 'single_species', 'single_schema'],
                        help='')

    parser.add_argument('--sp', type=str, required=False,
                        default=None, dest='species_id',
                        help='')

    parser.add_argument('--sc', type=str, required=False,
    					default=None, dest='schema_id',
    					help='')

    parser.add_argument('--g', type=str, required=False,
                        dest='virtuoso_graph',
                        default=os.environ.get('DEFAULTHGRAPH'),
                        help='')

    parser.add_argument('--s', type=str,
                        dest='local_sparql', required=False,
                        default=os.environ.get('LOCAL_SPARQL'),
                        help='')

    parser.add_argument('--b', type=str,
                        dest='base_url', required=False,
                        default=os.environ.get('BASE_URL'),
                        help='')

    args = parser.parse_args()

    return [args.mode, args.species_id, args.schema_id,
            args.virtuoso_graph, args.local_sparql,
            args.base_url]


def global_species(virtuoso_graph, local_sparql, base_url):
	"""
	"""
	
	# get all species in the NS
	species_result = aux.get_data(SPARQLWrapper(local_sparql),
	                              sparql_queries.SELECT_SPECIES.format(virtuoso_graph, ' typon:name ?name. '))
	result_data = species_result['results']['bindings']

	ns_species = {s['species']['value']: s['name']['value'] for s in result_data}

	species_ids = [s.split('/')[-1] for s in ns_species]
	for i in species_ids:
		single_species(i, virtuoso_graph, local_sparql, base_url)


def single_species(species_id, virtuoso_graph, local_sparql, base_url):
	"""
	"""

	start_date = dt.datetime.now()
	start_date_str = dt.datetime.strftime(start_date, '%Y-%m-%dT%H:%M:%S')
	logging.info('Started determination of loci and alleles counts at: {0}'.format(start_date_str))

	# create species uri
	species_uri = '{0}species/{1}'.format(base_url, species_id)
	species_result = aux.get_data(SPARQLWrapper(local_sparql),
	                              sparql_queries.SELECT_SINGLE_SPECIES.format(virtuoso_graph, species_uri))
	result_data = species_result['results']['bindings']

	if len(result_data) == 0:
		logging.warning('Could not find species with identifier {0}. '
	                    'Aborting.\n\n'.format(species_id))

	# get all schemas for the species
	species_result = aux.get_data(SPARQLWrapper(local_sparql),
	                              sparql_queries.SELECT_SPECIES_SCHEMAS.format(virtuoso_graph, species_uri))
	result_data = species_result['results']['bindings']

	if len(result_data) == 0:
		logging.info('Species has no schemas.')

	schemas = [s['schemas']['value'] for s in result_data]
	# sort by integer identifier to be able to fetch schemas by index
	schemas = sorted(schemas, key=lambda x: int(x.split('/')[-1]))

	# list files in folder
	computed_dir = Config.PRE_COMPUTE
	computed_files = os.listdir(computed_dir)
	for schema in schemas:
		schema_id = schema.split('/')[-1]
		schema_prefix = 'annotations_{0}_{1}'.format(species_id, schema_id)
		schema_files = [f for f in computed_files if f == '{0}.json'.format(schema_prefix)]
		schema_file = os.path.join(computed_dir, '{0}.json'.format(schema_prefix))

		# check if schema is locked
		schema_lock = aux.get_data(SPARQLWrapper(local_sparql),
                               	   (sparql_queries.ASK_SCHEMA_LOCK.format(schema)))
		lock_status = schema_lock['boolean']
		if lock_status is True:
			schema_info = aux.get_data(SPARQLWrapper(local_sparql),
                          (sparql_queries.SELECT_SPECIES_SCHEMA.format(virtuoso_graph, schema)))

			schema_properties = schema_info['results']['bindings']
			if len(schema_properties) == 0:
				logging.warning('Could not find properties values for schema with identifier {0}. '
		                        'Aborting.\n\n'.format(schema_id))
				continue

			last_modified = schema_properties[0]['last_modified']['value']
			if len(schema_files) == 0:
				create_file(schema_file, {'message': []})

			lengths_dir = '{0}_{1}_lengths'.format(species_id, schema_id)
			if lengths_dir in computed_files:
				lengths_dir = os.path.join(computed_dir, lengths_dir)
				fast_update(schema, last_modified, schema_file, lengths_dir,
					        virtuoso_graph, local_sparql)
			else:
				full_update(schema, last_modified, schema_file,
					        virtuoso_graph, local_sparql)
		else:
			logging.warning('Schema {0} is locked. Aborting.'.format(schema))


def single_schema(species_id, schema_id, virtuoso_graph, local_sparql, base_url):
	"""
	"""

	start = time.time()
	start_date = dt.datetime.now()
	start_date_str = dt.datetime.strftime(start_date, '%Y-%m-%dT%H:%M:%S')
	logging.info('Started determination of loci and alleles counts at: {0}'.format(start_date_str))

	# create species uri
	species_uri = '{0}species/{1}'.format(base_url, species_id)
	species_result = aux.get_data(SPARQLWrapper(local_sparql),
                                  sparql_queries.SELECT_SINGLE_SPECIES.format(virtuoso_graph, species_uri))
	result_data = species_result['results']['bindings']

	if len(result_data) == 0:
		logging.warning('Could not find species with identifier {0}. '
						'Aborting.\n\n'.format(species_id))
		sys.exit(1)

	schema_uri = '{0}/schemas/{1}'.format(species_uri, schema_id)
	schema_info = aux.get_data(SPARQLWrapper(local_sparql),
                          (sparql_queries.SELECT_SPECIES_SCHEMA.format(virtuoso_graph, schema_uri)))

	schema_properties = schema_info['results']['bindings']
	if len(schema_properties) == 0:
		logging.warning('Could not find properties values for schema with identifier {0}. '
                        'Aborting.\n\n'.format(schema_id))
		sys.exit(1)

	last_modified = schema_properties[0]['last_modified']['value']

	# list files in folder
	computed_dir = Config.PRE_COMPUTE
	computed_files = os.listdir(computed_dir)

	# check if folder with schema alleles lengths files exists
	lengths_dir = '{0}_{1}_lengths'.format(species_id, schema_id)

	# get files with schema prefix
	schema_prefix = 'annotations_{0}_{1}'.format(species_id, schema_id)
	schema_files = [f for f in computed_files if f == '{0}.json'.format(schema_prefix)]
	schema_file = os.path.join(computed_dir, '{0}.json'.format(schema_prefix))

	if len(schema_files) == 0:
		create_file(schema_file, {'message': []})

	if lengths_dir in computed_files:
		lengths_dir = os.path.join(computed_dir, lengths_dir)
		fast_update(schema_uri, last_modified, schema_file, lengths_dir,
			        virtuoso_graph, local_sparql)
	else:
		full_update(schema_uri, last_modified, schema_file,
			        virtuoso_graph, local_sparql)

	end = time.time()
	delta = end - start
	print(delta/60)


if __name__ == '__main__':

	args = parse_arguments()

	if args[0] == 'global_species':
		global_species(args[3], args[4], args[5])
	elif args[0] == 'single_species':
		single_species(args[1], args[3], args[4],
			           args[5])
	elif args[0] == 'single_schema':
		single_schema(args[1], args[2], args[3],
			          args[4], args[5])
