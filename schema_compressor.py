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
import shutil
import logging
import datetime as dt
from SPARQLWrapper import SPARQLWrapper

from config import Config
from app.utils import sparql_queries
from app.utils import auxiliary_functions as aux
from app.utils import PrepExternalSchema


local_sparql = os.environ.get('LOCAL_SPARQL')
virtuoso_graph = os.environ.get('DEFAULTHGRAPH')
logfile = 'schema_compression.log'
logging.basicConfig(filename=logfile, level=logging.INFO)


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


def compress_determiner(schemas, species_id, sp_name, compressed_schemas, to_compress):
    """
    """

    for schema in schemas:
        schema_name = schema[1]
        schema_uri = schema[0]
        schema_id = schema_uri.split('/')[-1]
        schema_prefix = '{0}_{1}'.format(species_id, schema_id)

        last_date, lock_state, schema_info = determine_date(schema_uri)
        if lock_state != 'Unlocked':
            logging.warning('{0} ({1}) is locked.'.format(schema_uri, schema_name))
            continue

        schema_date = last_date
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
                                schema_prefix, schema_name])
            logging.info('{0} ({1}) is novel schema to compress.'.format(schema_uri, schema_name))
            continue

        comp_date = comp_schema[0].split('_')[-1]
        comp_date = comp_date.split('.zip')[0]

        if comp_date != schema_date:
            to_compress.append([schema_uri, schema_date, schema_bsr,
                                schema_ml, schema_tt, schema_ptf,
                                schema_st, chewie_version, sp_name,
                                schema_prefix, schema_name])
            logging.info('{0} ({1}) compressed version is '
                         'outdated.'.format(schema_uri, schema_name))
        else:
            logging.info('{0} ({1}) is up-to-date.'.format(schema_uri, schema_name))

    return to_compress


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


def main():

    # get date
    start_date = dt.datetime.now()
    start_date_str = dt.datetime.strftime(start_date, '%Y-%m-%dT%H:%M:%S')
    logging.info('Started compressor at: {0}'.format(start_date_str))

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
    for species in species_list:
        sp_name = '_'.join(species_list[species].split(' '))

        sp_schemas = schemas[species]

        species_id = species.split('/')[-1]

        to_compress = compress_determiner(sp_schemas, species_id,
                                          sp_name, compressed_schemas,
                                          to_compress)

    if len(to_compress) == 0:
        logging.info('No schemas to update.\n\n')
        sys.exit(0)
    else:
        schemas = ['{0} ({1})'.format(s[0], s[-1]) for s in to_compress]
        logging.info('Schemas to compress: {0}'.format(';'.join(schemas)))

    # for each schema: get loci, download FASTA to temp folder, apply PrepExternalSchema and compress
    for schema in to_compress:

        schema_ptf_path = os.path.join(Config.SCHEMAS_PTF, schema[5])

        loci_list = schema_loci(schema[0])
        if len(loci_list) == 0:
            logging.info('Could not retrieve loci for {0} ({1}).'.format(schema[0], schema[-1]))
            continue

        # create temp folder
        temp_dir = os.path.join(Config.SCHEMAS_ZIP, 'temp')
        os.mkdir(temp_dir)

        temp_files = create_fasta(loci_list, schema, temp_dir)
        if temp_files[0] is not True:
            logging.warning('Could not retrieve sequences for locus {0} '
                            'from schema {1} {2}. Aborting schema '
                            'compression.'.format(temp_files[1], schema[0], schema[-1]))
            continue

        # run PrepExternalSchema
        logging.info('Adapting schema {0} ({1})'.format(schema[0], schema[-1]))
        output_directory = os.path.join(Config.SCHEMAS_ZIP, '{0}_{1}'.format(schema[-2], schema[1]))
        adapted = PrepExternalSchema.main(temp_dir, output_directory, 2,
                                          float(schema[2]), int(schema[3]),
                                          int(schema[4]), schema[5],
                                          None, os.path.join('/app', logfile))

        if adapted is not True:
            logging.warning('Could not adapt {0} ({1}).'.format(schema[0], schema[-1]))
            continue

        # copy training file to schema directory
        ptf_name = '{0}.trn'.format(schema[-3])
        shutil.copy(schema_ptf_path, os.path.join(output_directory, ptf_name))

        # write schema config file
        schema_config = aux.write_schema_config(schema[2], schema[5],
                                                                schema[4], schema[3],
                                                                schema[7], schema[6],
                                                                output_directory)

        # create hidden file with genes/loci list
        genes_list_file = aux.write_gene_list(output_directory)

        # compress schema
        shutil.make_archive(output_directory, 'zip', output_directory)

        # remove temp directories and files
        shutil.rmtree(temp_dir)
        shutil.rmtree(output_directory)

    end_date = dt.datetime.now()
    end_date_str = dt.datetime.strftime(end_date, '%Y-%m-%dT%H:%M:%S')
    logging.info('Finished compressor at: {0}\n\n'.format(end_date_str))


if __name__ == '__main__':

    main()
