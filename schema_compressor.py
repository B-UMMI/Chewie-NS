#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Purpose
-------

This module is used by the Chewie-NS to generate compressed
versions of schemas.

It has two execution modes: single and global. The former
enables the compression of a single schema and the latter
enables the compression of all schemas in the Chewie-NS.
Both modes verify if there is a compressed version for each
schema and if it is necessary to update it based on the last
modification date of the schema.

Expected input
--------------

It is necessary to specify the execution mode through the
following argument:

- ``-m``, ``mode`` :

    - e.g.: ``single`` or ``global``

The ``single`` mode also receives the identifier of a species
and the identifier of a schema for that species:

- ``--sp``, ``species_id`` :

    - e.g.: ``1``

- ``--sc``, ``schema_id`` :

    - e.g.: ``4``

Code documentation
------------------
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
from app.utils import sparql_queries as sq
from app.utils import auxiliary_functions as aux
from app.utils import PrepExternalSchema


logfile = './log_files/schema_compression.log'
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%Y-%m-%dT%H:%M:%S',
                    filename=logfile)


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
        False otherwise.
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


def get_species(local_sparql, virtuoso_graph):
    """ Gets the list of species in the Chewie-NS.

        This function has no arguments but expects
        that the SPARQL endpoint and default Virtuoso
        Graph be set as OS environment variables.

        Returns
        -------
        species_list : dict
        A dictionary with species URIs as keys and species
        names as values. None if species has no schemas.
    """

    # get the list of species in NS
    species_result = aux.get_data(SPARQLWrapper(local_sparql),
                                  (sq.SELECT_SPECIES.format(virtuoso_graph,
                                                            ' typon:name ?name. ')))

    species = species_result['results']['bindings']
    if len(species) == 0:
        species_list = None
    else:
        species_list = {s['species']['value']: s['name']['value']
                        for s in species}

    return species_list


def species_schemas(species_uri, schemas, local_sparql, virtuoso_graph):
    """ Gets the list of schemas for a species.

        Parameters
        ----------
        species_uri : str
            The URI of the species in the Chewie-NS.
        schemas : dict
            An empty dictionary to store schemas' data.

        Returns
        -------
        A list with the following variables:

        - status (int): status code of the response.
        - schemas (dict): A dictionary with the species
          URI as key and a list of tuples as value.
          Each tuple has a schema URI and the name of
          that schema.
    """

    result = aux.get_data(SPARQLWrapper(local_sparql),
                          (sq.SELECT_SPECIES_SCHEMAS.format(virtuoso_graph,
                                                            species_uri)))

    try:
        ns_schemas = result['results']['bindings']
        if len(ns_schemas) > 0:
            for schema in ns_schemas:
                schemas.setdefault(species_uri, []).append((schema['schemas']['value'],
                                                            schema['name']['value']))
    except Exception:
        logging.warning('Could not retrieve schemas for '
                        '{0}. Exception:\n{1}'.format(species_uri, result))

    return schemas


def determine_date(schema_uri, local_sparql, virtuoso_graph):
    """ Gets the last modification date for a schema.

        Parameters
        ----------
        schema_uri : str
            The URI of the schema in the Chewie-NS.

        Returns
        -------
        A list with the following variables:

        - last_date (str): The last modification date in
          the format YYYY-MM-DDTHH:MM:SS.f.
        - lock_state (str): Locking state of the schema.
        - schema_info (dict): A dictionary with schema
          properties values.
    """

    # get schema last modification date
    date_result = aux.get_data(SPARQLWrapper(local_sparql),
                               (sq.SELECT_SPECIES_SCHEMA.format(virtuoso_graph, schema_uri)))

    schema_info = date_result['results']['bindings'][0]

    lock_state = schema_info['Schema_lock']['value']
    last_date = schema_info['last_modified']['value']

    return [last_date, lock_state, schema_info]


def compress_determiner(schemas, species_id, sp_name, compressed_schemas,
                        to_compress, old_zips, local_sparql, virtuoso_graph):
    """ Determines if it is necessary to generate compressed
        versions of schemas.

        Parameters
        ----------
        schemas : list
            List with sublists, each sublist has the name and
            the URI for a schema of the species.
        species_id : str
            Identifier of the species in the Chewie-NS.
        sp_name : str
            Scientific name of the species.
        compressed_schemas : list
            List with all the compressed schema versions that are
            currently available.
        to_compress : list
            A list to store data about schemas that
            need to be compressed.
        old_zips : dict
            A dictionary to store the ZIP filenames of
            the outdated compressed versions.

        Returns
        -------
        A list with the following variables:
        to_compress : list
            A list with one sublist per schema that needs to
            be compressed. Each sublist has the following variables:

            - schema_uri (str): the URI of the schema in the Chewie-NS.
            - schema_date (str): last modification date of the schema.
            - schema_bsr (str): BLAST Score Ratio value used to create the
              schema and perform allele calling.
            - schema_ml (str): minimum sequence length value.
            - schema_tt (str): genetic code used to predict and translate
              coding sequences.
            - schema_ptf (str): BLAKE2 hash of the Prodigal training file
              associated with the schema.
            - schema_st (str): sequence size variation percentage
              threshold.
            - chewie_version (str): version of the chewBBACA suite
              used to create the schema and perform allele calling.
            - sp_name (str): name of the schema's species.
            - schema_prefix (str): filename prefix of the compressed
              version of the schema.
            - schema_name (str): name of the schema.
            - schema_lock (str): locking state of the schema.

        old_zips : dict
            A dictionary with schema URIs as keys and
            ZIP filenames of the compressed versions
            that are outdated or None if there is no
            compressed version.
    """

    for schema in schemas:
        schema_name = schema[1]
        schema_uri = schema[0]
        schema_id = schema_uri.split('/')[-1]
        schema_prefix = '{0}_{1}'.format(species_id, schema_id)

        last_date, lock_state, schema_info = determine_date(schema_uri, local_sparql, virtuoso_graph)

        schema_date = last_date
        schema_lock = lock_state
        schema_bsr = schema_info['bsr']['value']
        schema_ml = schema_info['minimum_locus_length']['value']
        schema_tt = schema_info['translation_table']['value']
        schema_ptf = schema_info['prodigal_training_file']['value']
        schema_st = schema_info['size_threshold']['value']
        chewie_version = schema_info['chewBBACA_version']['value']

        # get all compressed versions that have the schema prefix
        comp_schema = [f for f in compressed_schemas if f.startswith(schema_prefix)]
        # there is no compressed version
        if len(comp_schema) == 0:
            to_compress.append([schema_uri, schema_date, schema_bsr,
                                schema_ml, schema_tt, schema_ptf,
                                schema_st, chewie_version, sp_name,
                                schema_prefix, schema_name, schema_lock])
            logging.info('{0} ({1}) is novel schema to compress.'.format(schema_uri, schema_name))
            old_zips[schema_uri] = None
        # there is a compressed version
        elif len(comp_schema) == 1:
            comp_date = comp_schema[0].split('_')[-1]
            comp_date = comp_date.split('.zip')[0]

            # check if schema has been altered since compression date
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


def schema_loci(schema_uri, local_sparql, virtuoso_graph):
    """ Gets the list of loci for a schema.

        Parameters
        ----------
        schema_uri : str
            The URI of the schema in the Chewie-NS.

        Returns
        -------
        loci_list : list of tup
            A list with tuples. Each tuple has two
            elements, a locus name and a locus URI.
    """

    # get loci
    loci_result = aux.get_data(SPARQLWrapper(local_sparql),
                               (sq.SELECT_SCHEMA_LOCI.format(virtuoso_graph, schema_uri)))

    # check if schema has loci
    loci_list = loci_result['results']['bindings']
    if loci_list != []:
        loci_list = [(l['name']['value'], l['locus']['value']) for l in loci_list]

    return loci_list


def fasta_sequences(locus, date, local_sparql, virtuoso_graph):
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
                                (sq.SELECT_LOCUS_FASTA_BY_DATE.format(virtuoso_graph, locus, date)))

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
                              (sq.SELECT_LOCUS_SEQS_BY_DATE.format(virtuoso_graph, locus, date)))
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


def create_fasta(loci_list, date, temp_dir, local_sparql, virtuoso_graph):
    """ Creates FASTA files for the loci of a schema.

        Parameters
        ----------
        loci_list : list of tup
            A list with tuples, one tuple per locus.
            Each tuple has two elements: the locus name
            and the locus URI.
        date : str
            Last modification date of the schema. The
            function will get all sequences that were
            inserted before this date.
        temp_dir : str
            The path to the directory where the FASTA files
            will be created.

        Returns
        -------
        temp_files : list
            List of paths to the FASTA files that were created.
    """

    # download FASTA sequences and save in temp directory
    temp_files = []
    for locus in loci_list:
        locus_name = locus[0]
        locus_uri = locus[1]
        sequences = fasta_sequences(locus_uri, date, local_sparql, virtuoso_graph)
        if sequences is False:
            logging.warning('Cannot continue compression '
                            'process for schema. Could not '
                            'retrieve sequences for one or more loci.')
            return False

        fasta_seqs = [(f['allele_id']['value'], f['nucSeq']['value']) for f in sequences]

        fasta_lines = ['>{0}_{1}\n{2}'.format(locus_name, s[0], s[1]) for s in fasta_seqs]

        fasta_text = '\n'.join(fasta_lines)

        temp_file = '{0}/{1}.fasta'.format(temp_dir, locus_name)
        temp_files.append(temp_file)

        with open(temp_file, 'w') as f:
            f.write(fasta_text)

    return temp_files


def compress_schema(schema, old_zip, local_sparql, virtuoso_graph):
    """ Generates a compressed version of a schema that is in
        the Chewie-NS.

        Parameters
        ----------
        schema : list
            One of the sublists with data about a schema returned
            by the :py:func:`compress_determiner` function.
        old_zip : str
            Path to the outdated compressed version of the schema
            (None if there is no compressed version).

        Returns
        -------
        0 if the compression process completed successfully,
        1 otherwise.
    """

    schema_ptf_path = os.path.join(Config.SCHEMAS_PTF, schema[5])
    if os.path.isfile(schema_ptf_path) is False:
        logging.warning('Could not find training file for schema {0} ({1}).'
                        ' Aborting schema compression.'.format(schema[0], schema[-2]))
        return 1

    loci_list = schema_loci(schema[0], local_sparql, virtuoso_graph)
    if len(loci_list) == 0:
        logging.info('Could not retrieve loci for {0} ({1}).'.format(schema[0], schema[-2]))
        return 1

    # create temp folder
    temp_dir = os.path.join(Config.SCHEMAS_ZIP, '{0}_temp'.format(schema[-3]))
    os.mkdir(temp_dir)

    logging.info('Downloading Fasta files for schema {0} ({1})'.format(schema[0], schema[-2]))
    temp_files = create_fasta(loci_list, schema[1], temp_dir, local_sparql, virtuoso_graph)
    if temp_files is False:
        shutil.rmtree(temp_dir)
        return 1

    # run PrepExternalSchema
    logging.info('Adapting schema {0} ({1})'.format(schema[0], schema[-2]))
    output_directory = os.path.join(Config.SCHEMAS_ZIP, '{0}_{1}'.format(schema[-3], schema[1]))
    adapted = PrepExternalSchema.main(temp_dir, output_directory, 6,
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
                        help='Execution mode. The "single" mode '
                             'compresses a single schema and the '
                             '"global" mode compresses all schemas '
                             'in the Chewie-NS. A compressed version '
                             'of a schema will only be generated if '
                             'there is no compressed version or the '
                             'curretn one is outdated.')

    parser.add_argument('--sp', type=str, default=None,
                        dest='species_id', required=False,
                        help='The identifier of the species in the '
                             'Chewie-NS (only relevant for the "single" '
                             'mode).')

    parser.add_argument('--sc', type=str, default=None,
                        dest='schema_id', required=False,
                        help='The identifier of the schema in the '
                             'Chewie-NS (only relevant for the "global" '
                             'mode).')

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

    return [args.mode, args.species_id, args.schema_id,
            args.virtuoso_graph, args.local_sparql, args.base_url,
            args.virtuoso_graph, args.virtuoso_pass]


def global_compressor(graph, sparql, base_url):
    """ Determines which schemas need to be compressed and generates
        compressed versions of those schemas.
    """

    # get date
    start_date = dt.datetime.now()
    start_date_str = dt.datetime.strftime(start_date, '%Y-%m-%dT%H:%M:%S')
    logging.info('Started global compressor at: {0}'.format(start_date_str))

    species_list = get_species(sparql, graph)
    if species_list is None:
        logging.warning('Could not retrieve any species from the NS.\n\n')
        sys.exit(0)
    else:
        logging.info('Species in NS: {0}'.format(','.join(list(species_list.values()))))

    # get all schemas for all species
    schemas = {}
    for species in species_list:
        schemas = species_schemas(species, schemas, sparql, graph)
        if len(schemas) > 0:
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
                                                    to_compress, old_zips,
                                                    sparql, graph)

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

        response = compress_schema(schema, old_zips[schema[0]], sparql, graph)
        if response == 0:
            logging.info('Successfully compressed schema {0} '
                         '({1})'.format(schema[0], schema[-2]))
        else:
            logging.info('Could not compress schema {0} '
                         '({1})'.format(schema[0], schema[-2]))

    end_date = dt.datetime.now()
    end_date_str = dt.datetime.strftime(end_date, '%Y-%m-%dT%H:%M:%S')
    logging.info('Finished global compressor at: {0}\n\n'.format(end_date_str))


def single_compressor(species_id, schema_id, graph, sparql, base_url, user, password):
    """ Determines if a schema needs to be compressed and
        generates a compressed version if needed.
    """

    logging.info('Started single compressor for schema {0} '
                 'of species {1}'.format(schema_id, species_id))

    # check if species exists
    species_uri = '{0}species/{1}'.format(base_url, species_id)
    species_result = aux.get_data(SPARQLWrapper(sparql),
                                  sq.SELECT_SINGLE_SPECIES.format(graph, species_uri))
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
    schema_info = aux.get_data(SPARQLWrapper(sparql),
                               (sq.SELECT_SPECIES_SCHEMA.format(graph, schema_uri)))

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
                                               to_compress, old_zips,
                                               sparql, graph)

    if len(to_compress) == 0:
        logging.info('Aborting schema compression.\n\n')
        sys.exit(0)
    else:
        schemas = ['{0} ({1})'.format(s[0], s[-2]) for s in to_compress]
        logging.info('Schema to compress: {0}'.format(';'.join(schemas)))

    # check if schema is locked
    schema_lock = aux.get_data(SPARQLWrapper(sparql),
                               (sq.ASK_SCHEMA_LOCK.format(schema_uri)))

    lock_status = schema_lock['boolean']
    if lock_status is True:
        # lock schema
        locked = change_lock(schema_uri, 'LOCKED', graph,
                             sparql, user, password)
        if isinstance(locked, list) is True:
            logging.warning('Could not lock schema {0}. Response:'
                            '\n{1}\n\n'.format(schema_uri, locked[1]))
            sys.exit(1)

    single_schema_name = to_compress[0][-2]
    if old_zip[schema_uri] is not None:
        old_zip[schema_uri] = os.path.join(Config.SCHEMAS_ZIP, old_zip[schema_uri])

    # adapt and compress schema
    response = compress_schema(to_compress[0], old_zip[schema_uri], sparql, graph)
    if response == 0:
        logging.info('Successfully compressed schema {0} '
                     '({1})'.format(schema_uri, single_schema_name))
    else:
        logging.info('Could not compress schema {0} '
                     '({1})'.format(schema_uri, single_schema_name))

    # unlock schema
    unlocked = change_lock(schema_uri, 'Unlocked', graph,
                           sparql, user, password)
    if isinstance(unlocked, list) is True:
        logging.warning('Could not unlock schema at the end of compression process.')

        logging.info('Finished single compressor for schema {0} '
                     'of species {1}'.format(schema_id, species_id))


if __name__ == '__main__':

    args = parse_arguments()

    if args[0] == 'global':
        global_compressor(args[3], args[4], args[5])
    elif args[0] == 'single':
        single_compressor(args[1], args[2], args[3],
                          args[4], args[5], args[6],
                          args[7])
