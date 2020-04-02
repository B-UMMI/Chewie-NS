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
import pickle
import shutil
import logging
import argparse
import datetime as dt
from SPARQLWrapper import SPARQLWrapper

from config import Config
from app.utils import sparql_queries
from app.utils import auxiliary_functions as aux
from app.utils import PrepExternalSchema


base_url = os.environ.get('BASE_URL')
local_sparql = os.environ.get('LOCAL_SPARQL')
virtuoso_graph = os.environ.get('DEFAULTHGRAPH')
virtuoso_user = os.environ.get('VIRTUOSO_USER')
virtuoso_pass = os.environ.get('VIRTUOSO_PASS')
logfile = 'schema_compression.log'
logging.basicConfig(filename=logfile, level=logging.INFO)


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


def get_species():
    """
    """

    # get the list of species in NS
    species_result = aux.get_data(SPARQLWrapper(local_sparql),
                                  (sparql_queries.SELECT_SPECIES.format(virtuoso_graph,
                                                                        ' typon:name ?name. ')))

    species = species_result['results']['bindings']
    if len(species) == 0:
        species_list = None
    else:
        species_list = {s['species']['value']: s['name']['value'] for s in species}

    return species_list


def species_schemas(species_uri, schemas):
    """
    """

    result = aux.get_data(SPARQLWrapper(local_sparql),
                          (sparql_queries.SELECT_SPECIES_SCHEMAS.format(virtuoso_graph,
                                                                        species_uri)))
    ns_schemas = result['results']['bindings']
    if len(ns_schemas) == 0:
        result = None
    else:
        for schema in ns_schemas:
            schemas.setdefault(species_uri, []).append((schema['schemas']['value'],
                                                        schema['name']['value']))

    return [result, schemas]


def determine_date(schema_uri):
    """
    """

    # get schema last modification date
    date_result = aux.get_data(SPARQLWrapper(local_sparql),
                               (sparql_queries.SELECT_SPECIES_SCHEMA.format(virtuoso_graph, schema_uri)))

    schema_info = date_result['results']['bindings'][0]

    lock_state = schema_info['Schema_lock']['value']
    last_date = schema_info['last_modified']['value']

    return [last_date, lock_state, schema_info]


def compress_determiner(schemas, species_id, sp_name, compressed_schemas, to_compress, old_zips):
    """
    """

    for schema in schemas:
        schema_name = schema[1]
        schema_uri = schema[0]
        schema_id = schema_uri.split('/')[-1]
        schema_prefix = '{0}_{1}'.format(species_id, schema_id)

        last_date, lock_state, schema_info = determine_date(schema_uri)

        schema_date = last_date
        schema_lock = lock_state
        schema_bsr = schema_info['bsr']['value']
        schema_ml = schema_info['minimum_locus_length']['value']
        schema_tt = schema_info['translation_table']['value']
        schema_ptf = schema_info['prodigal_training_file']['value']
        schema_st = schema_info['size_threshold']['value']
        chewie_version = schema_info['chewBBACA_version']['value']

        comp_schema = [f for f in compressed_schemas if f.startswith(schema_prefix)]
        if len(comp_schema) == 0:
            to_compress.append([schema_uri, schema_date, schema_bsr,
                                schema_ml, schema_tt, schema_ptf,
                                schema_st, chewie_version, sp_name,
                                schema_prefix, schema_name, schema_lock])
            logging.info('{0} ({1}) is novel schema to compress.'.format(schema_uri, schema_name))
            old_zips[schema_uri] = None

        elif len(comp_schema) == 1:
            comp_date = comp_schema[0].split('_')[-1]
            comp_date = comp_date.split('.zip')[0]

            if comp_date != schema_date:
                to_compress.append([schema_uri, schema_date, schema_bsr,
                                    schema_ml, schema_tt, schema_ptf,
                                    schema_st, chewie_version, sp_name,
                                    schema_prefix, schema_name, schema_lock])
                logging.info('{0} ({1}) compressed version is '
                             'outdated.'.format(schema_uri, schema_name))
                old_zips[schema_uri] = comp_schema[0]
            else:
                logging.info('{0} ({1}) is up-to-date.'.format(schema_uri, schema_name))

        elif len(comp_schema) > 1:
            logging.warning('{0} ({1}) is already being compressed.'.format(schema_uri, schema_name))

    return [to_compress, old_zips]


def schema_loci(schema_uri):
    """
    """

    # get loci
    loci_result = aux.get_data(SPARQLWrapper(local_sparql),
                               (sparql_queries.SELECT_SCHEMA_LOCI.format(virtuoso_graph, schema_uri)))

    # check if schema has loci
    loci_list = loci_result['results']['bindings']
    if loci_list != []:
        loci_list = [(l['name']['value'], l['locus']['value']) for l in loci_list]

    return loci_list


def fasta_sequences(locus, date):
    """
    """
    
    # will get to maximum row! Write code to get alleles one by one
    fasta_result = aux.get_data(SPARQLWrapper(local_sparql),
                                (sparql_queries.SELECT_LOCUS_FASTA_BY_DATE.format(virtuoso_graph, locus, date)))

    if 'Max row length is exceeded when trying to store a string of' in str(fasta_result):

        fasta_result = aux.get_data(SPARQLWrapper(local_sparql),
                                    (sparql_queries.SELECT_LOCUS_SEQS_BY_DATE.format(virtuoso_graph, locus, date)))

        fasta_list = fasta_result['results']['bindings']
        for s in range(len(fasta_list)):
            # get the sequence corresponding to the hash
            result2 = aux.get_data(SPARQLWrapper(local_sparql),
                                  (sparql_queries.SELECT_SEQ_FASTA.format(virtuoso_graph, fasta_list[s]['sequence']['value'])))
            fasta_list[s]['nucSeq'] = result2['results']['bindings'][0]['nucSeq']
    else:
        fasta_list = fasta_result['results']['bindings']
    
    return fasta_list


def create_fasta(loci_list, schema, temp_dir):
    """
    """

    # download FASTA sequences and save in temp directory
    for locus in loci_list:
        locus_name = locus[0]
        locus_uri = locus[1]
        sequences = fasta_sequences(locus_uri, schema[1])

        if len(sequences) > 0:

            fasta_seqs = [(f['allele_id']['value'], f['nucSeq']['value']) for f in sequences]

            temp_file = '{0}/{1}.fasta'.format(temp_dir, locus_name)

            fasta_lines = ['>{0}_{1}\n{2}'.format(locus_name, s[0], s[1]) for s in fasta_seqs]

            fasta_text = '\n'.join(fasta_lines)

            with open(temp_file, 'w') as f:
                f.write(fasta_text)
        else:
            return [False, locus_uri]

    return [True]


def compress_schema(schema, old_zip):
    """
    """

    schema_ptf_path = os.path.join(Config.SCHEMAS_PTF, schema[5])
    if os.path.isfile(schema_ptf_path) is False:
        logging.warning('Could not find training file for schema {0} ({1}).'
                        ' Aborting schema compression.'.format(schema[0], schema[-2]))
        return 1

    loci_list = schema_loci(schema[0])
    if len(loci_list) == 0:
        logging.info('Could not retrieve loci for {0} ({1}).'.format(schema[0], schema[-2]))
        return 1

    # create temp folder
    temp_dir = os.path.join(Config.SCHEMAS_ZIP, '{0}_temp'.format(schema[-3]))
    os.mkdir(temp_dir)

    logging.info('Downloading Fasta files for schema {0} ({1})'.format(schema[0], schema[-2]))
    temp_files = create_fasta(loci_list, schema, temp_dir)
    if temp_files[0] is not True:
        logging.warning('Could not retrieve sequences for locus {0} '
                        'from schema {1} {2}. Aborting schema '
                        'compression.'.format(temp_files[1], schema[0], schema[-2]))
        shutil.rmtree(temp_dir)
        return 1

    # run PrepExternalSchema
    logging.info('Adapting schema {0} ({1})'.format(schema[0], schema[-2]))
    output_directory = os.path.join(Config.SCHEMAS_ZIP, '{0}_{1}'.format(schema[-3], schema[1]))
    adapted = PrepExternalSchema.main(temp_dir, output_directory, 2,
                                      float(schema[2]), int(schema[3]),
                                      int(schema[4]), schema[5],
                                      None, os.path.join('/app', logfile))

    if adapted is True:
        # copy training file to schema directory
        ptf_basename = '{0}.trn'.format(schema[-4])
        ptf_file = os.path.join(output_directory, ptf_basename)
        shutil.copy(schema_ptf_path, ptf_file)

        # write schema config file
        schema_config = aux.write_schema_config(schema[2], schema[5],
                                                schema[4], schema[3],
                                                schema[7], schema[6],
                                                output_directory)

        # write config file with schema last modification date
        ns_config = os.path.join(output_directory, '.ns_config')
        with open(ns_config, 'wb') as nc:
            ns_info = [schema[1], schema[0]]
            pickle.dump(ns_info, nc)

        # create hidden file with genes/loci list
        genes_list_file = aux.write_gene_list(output_directory)

        # remove old zip archive
        if old_zip is not None:
            os.remove(old_zip)

        # compress new version
        shutil.make_archive(output_directory, 'zip', output_directory)

    elif adapted is not True:
        logging.warning('Could not adapt {0} ({1}).'.format(schema[0], schema[-2]))

    # remove temp directories and files
    shutil.rmtree(temp_dir)
    shutil.rmtree(output_directory)

    return 0 if adapted is True else 1


def parse_arguments():

    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument('-m', type=str,
                        dest='mode', required=True,
                        choices=['global', 'single'],
                        help='')

    parser.add_argument('--sp', type=str, default=None,
                        dest='species_id', required=False,
                        help='')

    parser.add_argument('--sc', type=str, default=None,
                        dest='schema_id', required=False,
                        help='')

    args = parser.parse_args()

    return [args.mode, args.species_id, args.schema_id]


def global_compressor():
    """
    """

    # get date
    start_date = dt.datetime.now()
    start_date_str = dt.datetime.strftime(start_date, '%Y-%m-%dT%H:%M:%S')
    logging.info('Started global compressor at: {0}'.format(start_date_str))

    species_list = get_species()
    if species_list is None:
        logging.warning('Could not retrieve any species from the NS.\n\n')
        sys.exit(0)
    else:
        logging.info('Species in NS: {0}'.format(','.join(list(species_list.values()))))

    # get all schemas for all species
    schemas = {}
    for species in species_list:
        result, schemas = species_schemas(species, schemas)
        if result is None:
            logging.warning('Could not find any schemas for species '
                            '{0} ({1})'.format(species, species_list[species]))
        else:
            current_schemas = schemas[species]
            current_schemas_strs = ['{0}, {1}'.format(s[0], s[1]) for s in current_schemas]
            logging.info('Found {0} schemas for {1} ({2}): {3}'.format(len(current_schemas),
                                                                       species,
                                                                       species_list[species],
                                                                       ';'.join(current_schemas_strs)))

    if len(schemas) == 0:
        logging.warning('Could not find schemas for any species.\n\n')
        sys.exit(0)

    # list compressed schemas
    compressed_schemas = os.listdir(Config.SCHEMAS_ZIP)

    # iterate over each species schemas
    # decide which schemas to compress
    to_compress = []
    old_zips = {}
    for species in schemas:
        sp_name = '_'.join(species_list[species].split(' '))

        sp_schemas = schemas[species]

        species_id = species.split('/')[-1]

        to_compress, old_zips = compress_determiner(sp_schemas, species_id,
                                                              sp_name, compressed_schemas,
                                                              to_compress, old_zips)

    # exclude locked schemas
    locked = []
    for s in to_compress:
        if s[-1] != 'Unlocked':
            logging.warning('{0} ({1}) is locked.'.format(s[0], s[-2]))
            locked.append(s[0])
            del(old_zips[s[0]])

    to_compress = [s for s in to_compress if s[0] not in locked]
    old_zips = {f: os.path.join(Config.SCHEMAS_ZIP, z) if z is not None else None for f, z in old_zips.items()}

    if len(to_compress) == 0:
        logging.info('No schemas to update.\n\n')
        sys.exit(0)
    else:
        schemas = ['{0} ({1})'.format(s[0], s[-2]) for s in to_compress]
        logging.info('Schemas to compress: {0}'.format(';'.join(schemas)))

    # for each schema: get loci, download FASTA to temp folder, apply PrepExternalSchema and compress
    for schema in to_compress:

        response = compress_schema(schema, old_zips[schema[0]])
        if response == 0:
            logging.info('Successfully compressed schema {0} '
                         '({1})'.format(schema[0], schema[-2]))
        else:
            logging.info('Could not compress schema {0} '
                         '({1})'.format(schema[0], schema[-2]))

    end_date = dt.datetime.now()
    end_date_str = dt.datetime.strftime(end_date, '%Y-%m-%dT%H:%M:%S')
    logging.info('Finished global compressor at: {0}\n\n'.format(end_date_str))


def single_compressor(species_id, schema_id):
    """
    """

    start_date = dt.datetime.now()
    start_date_str = dt.datetime.strftime(start_date, '%Y-%m-%dT%H:%M:%S')
    logging.info('Started single compressor at: {0}'.format(start_date_str))

    # check if species exists
    species_uri = '{0}species/{1}'.format(base_url, species_id)
    species_result = aux.get_data(SPARQLWrapper(local_sparql),
                                        sparql_queries.SELECT_SINGLE_SPECIES.format(virtuoso_graph, species_uri))
    result_data = species_result['results']['bindings']

    if len(result_data) == 0:
        logging.warning('Could not find species with identifier {0}. '
                        'Aborting schema compression.\n\n'.format(species_id))
        sys.exit(1)

    sp_name = result_data[0]['name']['value']
    sp_name = '_'.join(sp_name.split(' '))

    # get schema info
    # construct schema URI
    schema_uri = '{0}/schemas/{1}'.format(species_uri, schema_id)
    schema_info = aux.get_data(SPARQLWrapper(local_sparql),
                          (sparql_queries.SELECT_SPECIES_SCHEMA.format(virtuoso_graph, schema_uri)))

    schema_properties = schema_info['results']['bindings']
    if len(schema_properties) == 0:
        logging.warning('Could not find properties values for schema with identifier {0}. '
                        'Aborting schema compression.\n\n'.format(schema_id))
        sys.exit(1)

    schema_name = schema_properties[0]['name']['value']
    schemas = [(schema_uri, schema_name)]
    # list compressed schemas
    compressed_schemas = os.listdir(Config.SCHEMAS_ZIP)
    to_compress = []
    old_zips = {}
    to_compress, old_zip = compress_determiner(schemas, species_id,
                                                        sp_name, compressed_schemas,
                                                        to_compress, old_zips)

    if len(to_compress) == 0:
        logging.info('Aborting schema compression.\n\n')
        sys.exit(0)
    else:
        schemas = ['{0} ({1})'.format(s[0], s[-2]) for s in to_compress]
        logging.info('Schema to compress: {0}'.format(';'.join(schemas)))

    # check if schema is locked
    schema_lock = aux.get_data(SPARQLWrapper(local_sparql),
                               (sparql_queries.ASK_SCHEMA_LOCK.format(schema_uri)))

    lock_status = schema_lock['boolean']
    if lock_status is True:
        # lock schema
        change_lock(schema_uri, 'LOCKED')

    single_schema_name = to_compress[0][-2]
    if old_zip[schema_uri] is not None:
        old_zip[schema_uri] = os.path.join(Config.SCHEMAS_ZIP, old_zip[schema_uri])

    # adapt and compress schema
    response = compress_schema(to_compress[0], old_zip[schema_uri])
    if response == 0:
        logging.info('Successfully compressed schema {0} '
                     '({1})'.format(schema_uri, single_schema_name))
    else:
        logging.info('Could not compress schema {0} '
                     '({1})'.format(schema_uri, single_schema_name))

    # unlock schema
    change_lock(schema_uri, 'Unlocked')

    end_date = dt.datetime.now()
    end_date_str = dt.datetime.strftime(end_date, '%Y-%m-%dT%H:%M:%S')
    logging.info('Finished single compressor at: {0}\n\n'.format(end_date_str))


if __name__ == '__main__':

    args = parse_arguments()

    if args[0] == 'global':
        global_compressor()
    elif args[0] == 'single':
        single_compressor(args[1], args[2])
