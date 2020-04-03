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
import pickle
import shutil
import logging
import argparse
import datetime as dt
from SPARQLWrapper import SPARQLWrapper

from config import Config
from app.utils import sparql_queries
from app.utils import auxiliary_functions as aux


base_url = os.environ.get('BASE_URL')
local_sparql = os.environ.get('LOCAL_SPARQL')
virtuoso_graph = os.environ.get('DEFAULTHGRAPH')
virtuoso_user = os.environ.get('VIRTUOSO_USER')
virtuoso_pass = os.environ.get('VIRTUOSO_PASS')
logfile = 'schema_totals.log'
logging.basicConfig(filename=logfile, level=logging.INFO)


def create_file(filename, header):
	"""
	"""
	
	with open(filename, 'w') as json_outfile:
		json.dump(header, json_outfile)

	return os.path.isfile(filename)


def update_file(schema, file):
	"""
	"""

	schema_id = int(schema.split('/')[-1])
	current_file = file

	# read current file
	with open(current_file, 'r') as json_file:
		json_data = json.load(json_file)

	json_schemas = json_data['message']
	schemas_indexes = {int(s['schema']['value'].split('/')[-1]): i for i, s in enumerate(json_schemas)}
	# if the schema is in the json file
	if schema_id in schemas_indexes:
		current_schema = json_schemas[schemas_indexes[schema_id]]

		# get modification date in json file
		json_date = current_schema['last_modified']['value']

		# get schema info that is in Virtuoso
		result = aux.get_data(SPARQLWrapper(local_sparql),
							  sparql_queries.SELECT_SPECIES_SCHEMA.format(virtuoso_graph, schema))
		
		schema_info = result['results']['bindings']
		virtuoso_date = schema_info[0]['last_modified']['value']
		if json_date == virtuoso_date:
			logging.info('Information about number of loci and number of alleles for schema {0} is up-to-date.'.format(schema))

		elif json_date != virtuoso_date:
			result = aux.get_data(SPARQLWrapper(local_sparql),
                           		  (sparql_queries.COUNT_SINGLE_SCHEMA_LOCI_ALLELES.format(virtuoso_graph, schema)))

			result_data = result['results']['bindings'][0]
			result_data[0]['schema'] = {'value': schema}

			json_data['message'][schemas_indexes[schema_id]] = result_data
			with open(current_file, 'w') as json_outfile:
				json.dump(json_data, json_outfile)

			logging.info('Updated data for schema {0}'.format())
	# new schema that is not in the json file
	elif schema_id not in schemas_indexes:
		result = aux.get_data(SPARQLWrapper(local_sparql),
                          	  (sparql_queries.COUNT_SINGLE_SCHEMA_LOCI_ALLELES.format(virtuoso_graph, schema)))

		result_data = result['results']['bindings']
		result_data[0]['schema'] = {'value': schema}

		if len(result_data) > 0:
			json_data['message'].append(result_data[0])
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

    args = parser.parse_args()

    return [args.mode, args.species_id, args.schema_id]


def global_species():
	"""
	"""
	
	# get all species in the NS
	species_result = aux.get_data(SPARQLWrapper(local_sparql),
	                              sparql_queries.SELECT_SPECIES.format(virtuoso_graph, ' typon:name ?name. '))
	result_data = species_result['results']['bindings']

	ns_species = {s['species']['value']: s['name']['value'] for s in result_data}

	species_ids = [s.split('/')[-1] for s in ns_species]
	for i in species_ids:
		single_species(i)


def single_species(species_id):
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

	species_prefix = 'totals_{0}'.format(species_id)
	species_file = os.path.join(computed_dir, '{0}.json'.format(species_prefix))
	species_files = [f for f in computed_files if f.startswith(species_prefix)]

	if len(species_files) == 0:
		create_file(species_file, {'message': []})
	for schema in schemas:
		# check if schema is locked
		schema_lock = aux.get_data(SPARQLWrapper(local_sparql),
                               	   (sparql_queries.ASK_SCHEMA_LOCK.format(schema)))

		lock_status = schema_lock['boolean']
		if lock_status is True:
			update_file(schema, species_file)
		else:
			logging.warning('Schema {0} is locked. Aborting.'.format(schema))


def single_schema(species_id, schema_id):
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
		sys.exit(1)

	schema_uri = '{0}/schemas/{1}'.format(species_uri, schema_id)
	schema_info = aux.get_data(SPARQLWrapper(local_sparql),
                          (sparql_queries.SELECT_SPECIES_SCHEMA.format(virtuoso_graph, schema_uri)))

	schema_properties = schema_info['results']['bindings']
	if len(schema_properties) == 0:
		logging.warning('Could not find properties values for schema with identifier {0}. '
                        'Aborting.\n\n'.format(schema_id))
		sys.exit(1)

	# list files in folder
	computed_dir = Config.PRE_COMPUTE
	computed_files = os.listdir(computed_dir)

	# get files with species prefix
	species_prefix = 'totals_{0}'.format(species_id)
	species_files = [f for f in computed_files if f.startswith(species_prefix)]

	species_file = os.path.join(computed_dir, '{0}.json'.format(species_prefix))
	if len(species_files) == 0:
		create_file(species_file, {'message': []})

	update_file(schema_uri, species_file)


if __name__ == '__main__':

	args = parse_arguments()

	if args[0] == 'global_species':
		global_species()
	elif args[0] == 'single_species':
		single_species(args[1])
	elif args[0] == 'single_schema':
		single_schema(args[1], args[2])
