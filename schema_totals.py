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
import datetime as dt
from SPARQLWrapper import SPARQLWrapper

from config import Config
from app.utils import sparql_queries as sq
from app.utils import auxiliary_functions as aux


logfile = './log_files/schema_totals.log'
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


def fast_update(species_file, files_dir, schema_uri, schema_data,
	            virtuoso_graph, local_sparql, base_url):
	"""
	"""

	schema_id = int(schema_uri.split('/')[-1])
	current_file = species_file

	# read current file
	with open(current_file, 'r') as json_file:
		json_data = json.load(json_file)

	json_schemas = json_data['message']
	schemas_indexes = {int(s['uri'].split('/')[-1]): i for i, s in enumerate(json_schemas)}

	# if the schema is in the json file
	if schema_id in schemas_indexes:
		current_schema = json_schemas[schemas_indexes[schema_id]]

		# get modification date in json file
		json_date = current_schema['last_modified']

		# get schema info that is in Virtuoso
		virtuoso_date = schema_data['last_modified']
		if json_date == virtuoso_date:
			logging.info('Information about number of loci and number of alleles for schema {0} is up-to-date.'.format(schema_uri))

		elif json_date != virtuoso_date:
			length_files = [os.path.join(files_dir, file) for file in os.listdir(files_dir)]

			total_loci = len(length_files)

			total_alleles = 0
			for file in length_files:
				locus_id = os.path.basename(file).split('_')[-1]
				locus_uri = '{0}loci/{1}'.format(base_url, locus_id)
				with open(file, 'rb') as f:
					locus_data = pickle.load(f)
				
				total_alleles += len(locus_data[locus_uri])

			current_schema['last_modified'] = virtuoso_date
			current_schema['nr_loci'] = str(total_loci)
			current_schema['nr_alleles'] = str(total_alleles)

			json_data['message'][schemas_indexes[schema_id]] = current_schema
			with open(current_file, 'w') as json_outfile:
				json.dump(json_data, json_outfile)

			logging.info('Updated data for schema {0}'.format(schema_uri))
	# new schema that is not in the json file
	elif schema_id not in schemas_indexes:
		length_files = [os.path.join(files_dir, file) for file in os.listdir(files_dir)]

		total_loci = len(length_files)

		total_alleles = 0
		for file in length_files:
			locus_id = os.path.basename(file).split('_')[-1]
			locus_uri = '{0}loci/{1}'.format(base_url, locus_id)
			with open(file, 'rb') as f:
				locus_data = pickle.load(f)

			total_alleles += len(locus_data[locus_uri])

		# determine user that uploaded the file
		admin = aux.get_data(SPARQLWrapper(local_sparql),
		   				     sq.SELECT_SCHEMA_ADMIN.format(virtuoso_graph, schema_uri))

		admin = admin['results']['bindings'][0]['admin']['value']
		new_schema = schema_data
		new_schema['user'] = admin
		new_schema['uri'] = schema_uri
		new_schema['nr_loci'] = str(total_loci)
		new_schema['nr_alleles'] = str(total_alleles)
		del(new_schema['Schema_lock'])

		json_data['message'].append(new_schema)
		with open(current_file, 'w') as json_outfile:
			json.dump(json_data, json_outfile)	


def full_update(schema_uri, file, schema_data,
	            virtuoso_graph, local_sparql, base_url):
	"""
	"""

	schema_id = int(schema_uri.split('/')[-1])
	current_file = file

	# read current file
	with open(current_file, 'r') as json_file:
		json_data = json.load(json_file)

	json_schemas = json_data['message']
	schemas_indexes = {int(s['uri'].split('/')[-1]): i for i, s in enumerate(json_schemas)}
	# if the schema is in the json file
	if schema_id in schemas_indexes:
		current_schema = json_schemas[schemas_indexes[schema_id]]

		# get modification date in json file
		json_date = current_schema['last_modified']

		virtuoso_date = schema_data['last_modified']
		if json_date == virtuoso_date:
			logging.info('Information about number of loci and number of alleles for schema {0} is up-to-date.'.format(schema_uri))

		elif json_date != virtuoso_date:
			result = aux.get_data(SPARQLWrapper(local_sparql),
                           		  (sq.COUNT_SINGLE_SCHEMA_LOCI_ALLELES.format(virtuoso_graph, schema_uri)))

			result_data = result['results']['bindings'][0]
			current_schema['last_modified'] = virtuoso_date
			current_schema['nr_loci'] = result_data['nr_loci']['value']
			current_schema['nr_alleles'] = result_data['nr_alleles']['value']

			json_data['message'][schemas_indexes[schema_id]] = current_schema
			with open(current_file, 'w') as json_outfile:
				json.dump(json_data, json_outfile)

			logging.info('Updated data for schema {0}'.format(schema_uri))
	# new schema that is not in the json file
	elif schema_id not in schemas_indexes:
		result = aux.get_data(SPARQLWrapper(local_sparql),
                          	  (sq.COUNT_SINGLE_SCHEMA_LOCI_ALLELES.format(virtuoso_graph, schema_uri)))
		result_data = result['results']['bindings'][0]

		# determine user that uploaded the file
		admin = aux.get_data(SPARQLWrapper(local_sparql),
		   				     sq.SELECT_SCHEMA_ADMIN.format(virtuoso_graph, schema_uri))

		admin = admin['results']['bindings'][0]['admin']['value']
		new_schema = schema_data
		new_schema['user'] = admin
		new_schema['uri'] = schema_uri
		new_schema['nr_loci'] = result_data['nr_loci']['value']
		new_schema['nr_alleles'] = result_data['nr_alleles']['value']
		del(new_schema['Schema_lock'])

		json_data['message'].append(new_schema)
		with open(current_file, 'w') as json_outfile:
			json.dump(json_data, json_outfile)	


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

    args = parser.parse_args()

    return [args.mode, args.species_id, args.schema_id,
            args.virtuoso_graph, args.local_sparql,
            args.base_url]


def global_species(virtuoso_graph, local_sparql, base_url):
	"""
	"""

	# get all species in the NS
	species_result = aux.get_data(SPARQLWrapper(local_sparql),
	                              sq.SELECT_SPECIES.format(virtuoso_graph, ' typon:name ?name. '))
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
	                              sq.SELECT_SINGLE_SPECIES.format(virtuoso_graph, species_uri))
	result_data = species_result['results']['bindings']

	if len(result_data) == 0:
		logging.warning('Could not find species with identifier {0}. '
	                    'Aborting.\n\n'.format(species_id))

	# get all schemas for the species
	species_result = aux.get_data(SPARQLWrapper(local_sparql),
	                              sq.SELECT_SPECIES_SCHEMAS.format(virtuoso_graph, species_uri))
	result_data = species_result['results']['bindings']

	if len(result_data) == 0:
		logging.info('Species has no schemas.')

	schemas = [s['schemas']['value'] for s in result_data]
	# sort by integer identifier to be able to fetch schemas by index
	schemas = sorted(schemas, key=lambda x: int(x.split('/')[-1]))

	# list files in folder
	computed_dir = Config.PRE_COMPUTE
	computed_files = os.listdir(computed_dir)

	species_prefix = 'totals_{0}'.format(species_id)
	species_file = os.path.join(computed_dir, '{0}.json'.format(species_prefix))
	species_files = [f for f in computed_files if f.startswith(species_prefix)]

	if len(species_files) == 0:
		create_file(species_file, {'message': []})

	for schema in schemas:
		# check if schema is locked
		schema_lock = aux.get_data(SPARQLWrapper(local_sparql),
                               	   (sq.ASK_SCHEMA_LOCK.format(schema)))

		lock_status = schema_lock['boolean']
		if lock_status is True:
			# get schema info
			schema_info = aux.get_data(SPARQLWrapper(local_sparql),
		                          (sq.SELECT_SPECIES_SCHEMA.format(virtuoso_graph, schema)))

			schema_properties = schema_info['results']['bindings']
			if len(schema_properties) == 0:
				logging.warning('Could not find properties values for schema {0}. '
		                        'Aborting.\n\n'.format(schema))
				continue

			schema_properties = schema_properties[0]
			schema_properties = {k:schema_properties[k]['value'] for k in schema_properties}

			# check if folder with schema alleles lengths files exists
			schema_id = schema.split('/')[-1]
			lengths_dir = '{0}_{1}_lengths'.format(species_id, schema_id)

			if lengths_dir in computed_files:
				fast_update(species_file, lengths_dir, schema, schema_properties,
					        virtuoso_graph, local_sparql, base_url)
			else:
				full_update(schema, species_file, schema_properties,
					        virtuoso_graph, local_sparql, base_url)
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
                                  sq.SELECT_SINGLE_SPECIES.format(virtuoso_graph, species_uri))
	result_data = species_result['results']['bindings']

	if len(result_data) == 0:
		logging.warning('Could not find species with identifier {0}. '
						'Aborting.\n\n'.format(species_id))
		sys.exit(1)

	schema_uri = '{0}/schemas/{1}'.format(species_uri, schema_id)
	schema_info = aux.get_data(SPARQLWrapper(local_sparql),
                          (sq.SELECT_SPECIES_SCHEMA.format(virtuoso_graph, schema_uri)))

	schema_properties = schema_info['results']['bindings']
	if len(schema_properties) == 0:
		logging.warning('Could not find properties values for schema with identifier {0}. '
                        'Aborting.\n\n'.format(schema_id))
		sys.exit(1)

	schema_properties = schema_properties[0]
	schema_properties = {k:schema_properties[k]['value'] for k in schema_properties}

	# list files in folder
	computed_dir = Config.PRE_COMPUTE
	computed_files = os.listdir(computed_dir)

	# check if folder with schema alleles lengths files exists
	lengths_dir = '{0}_{1}_lengths'.format(species_id, schema_id)

	# get files with species prefix
	species_prefix = 'totals_{0}'.format(species_id)
	species_files = [f for f in computed_files if f.startswith(species_prefix)]

	species_file = os.path.join(computed_dir, '{0}.json'.format(species_prefix))
	if len(species_files) == 0:
		create_file(species_file, {'message': []})

	if lengths_dir in computed_files:
		lengths_dir = os.path.join(computed_dir, lengths_dir)
		fast_update(species_file, lengths_dir, schema_uri, schema_properties,
			        virtuoso_graph, local_sparql, base_url)
	else:
		full_update(schema_uri, species_file, schema_properties,
					virtuoso_graph, local_sparql, base_url)

	end = time.time()
	delta = end - start
	print(delta)


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
