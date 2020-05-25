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
import time
import pickle
import logging
import argparse
import requests
import threading
import concurrent.futures

from SPARQLWrapper import SPARQLWrapper

from app.utils import sparql_queries as sq
from app.utils import auxiliary_functions as aux


base_url = os.environ.get('BASE_URL')
local_sparql = os.environ.get('LOCAL_SPARQL')
virtuoso_graph = os.environ.get('DEFAULTHGRAPH')
virtuoso_user = os.environ.get('VIRTUOSO_USER')
virtuoso_pass = os.environ.get('VIRTUOSO_PASS')
logfile = './log_files/schema_loci_inserter.log'
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%Y-%m-%dT%H:%M:%S.%f',
                    filename=logfile)


thread_local = threading.local()


def get_session():
    if not hasattr(thread_local, 'session'):
        thread_local.session = requests.Session()
    return thread_local.session


def post_loci(query_data):
    """
    """

    locus_hash = query_data[0]
    query = query_data[1]

    session = get_session()
    headers = {'content-type': 'application/sparql-query'}
    tries = 0
    max_tries = 5
    valid = False
    while valid is False:
        with session.post(local_sparql, data=query, headers=headers, auth=requests.auth.HTTPBasicAuth(virtuoso_user, virtuoso_pass)) as response:
            if response.status_code > 201:
                tries += 1
                if tries < max_tries:
                    time.sleep(1)
                else:
                    valid = True
            else:
                valid = True

    return (locus_hash, response)


def send_queries(loci_queries):
    """
    """

    responses = {}
    total = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        for res in executor.map(post_loci, loci_queries):
            responses[res[0]] = res[1]
            total += 1

    return responses


def create_insert_queries(loci_data, schema_hashes):
    """
    """

    # create queries
    insert = 0
    insert_queries = []
    for l in loci_data:
        # determined if locus was already inserted
        inserted = schema_hashes[l[1]][1][0]
        if inserted is False:
            insert += 1
            original_name = '; typon:originalName "{0}"^^xsd:string.'.format(l[0]) \
                            if l[0] not in ['', 'string', False] else ' .'

            insert_query = (sq.INSERT_LOCUS.format(virtuoso_graph,
                                                   l[7], l[8], l[2],
                                                   l[3], l[4], l[5],
                                                   l[6], original_name))

            insert_queries.append((l[1], insert_query))

    return [insert_queries, insert]


def species_link_queries(loci_data, schema_hashes, species_uri):
    """
    """

    link = 0
    link_queries = []
    for l in loci_data:
        sp_link = schema_hashes[l[1]][1][1]
        if sp_link is False:
            link += 1
            link_query = (sq.INSERT_SPECIES_LOCUS.format(virtuoso_graph,
                                                         l[7], species_uri))

            link_queries.append((l[1], link_query))

    return [link_queries, link]


def schema_link_queries(loci_data, schema_hashes, schema_uri):
    """
    """

    link = 0
    link_queries = []
    schema_part_id = 1
    for l in loci_data:
        sc_link = schema_hashes[l[1]][1][2]
        if sc_link is False:
            link += 1
            # create URI for new schema part
            schema_part_url = '{0}/loci/{1}'.format(schema_uri, schema_part_id)

            # link locus to schema
            link_query = (sq.INSERT_SCHEMA_LOCUS.format(virtuoso_graph,
                                                        schema_part_url,
                                                        schema_part_id,
                                                        l[7],
                                                        schema_uri,
                                                        schema_part_url))

            link_queries.append((l[1], link_query))
            schema_part_id += 1

    return [link_queries, link]


def results_status(results):
    """
    """

    status = {}
    success = 0
    failed = 0
    for k in results:
        # change upload status
        status_code = results[k].status_code
        if status_code in [200, 201]:
            status[k] = True
            success += 1
        else:
            status[k] = False
            failed += 1

    return [status, success, failed]


def parse_arguments():

    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument('-i', type=str,
                        dest='input_file', required=True,
                        help='')

    args = parser.parse_args()

    return [args.input_file]


def main(temp_dir):
    """ Inserts loci data into Virtuoso's database.

        Gets loci data from file in temporary directory
        and inserts data into Virtuoso's database. Creates
        loci and associates loci with species and schema.

        Parameters
        ----------
        temp_dir : str
            Path to the temporary directory that has
            the files for schema insertion.

        Returns
        -------
        response_file : str
            Path to the file that contains th URIs and
            prefixes of the created loci.
    """

    start = time.time()

    # get species and schema identifiers
    species_id = os.path.basename(temp_dir).split('_')[0]
    schema_id = os.path.basename(temp_dir).split('_')[1]

    # create species and schema URIs
    species_uri = '{0}species/{1}'.format(base_url, species_id)
    schema_uri = '{0}/schemas/{1}'.format(species_uri, schema_id)

    logging.info('Starting loci insertion for '
                 'schema {0}'.format(schema_uri))

    # define path to file with loci data
    loci_file = os.path.join(temp_dir, '{0}_{1}_loci'.format(species_id,
                                                             schema_id))

    # read loci data
    if os.path.isfile(loci_file) is True:
        with open(loci_file, 'rb') as lf:
            loci_prefix, loci_data = pickle.load(lf)
            logging.info('Loci prefix is {0} and a total of {1} loci need '
                         'to be inserted.'.format(loci_prefix, len(loci_data)))
    else:
        logging.warning('Could not find file {0}. '
                        'Aborting\n\n'.format(loci_file))
        sys.exit(1)

    # determine total number of loci in the NS
    result = aux.get_data(SPARQLWrapper(local_sparql),
                          (sq.COUNT_TOTAL_LOCI.format(virtuoso_graph)))
    total_loci = int(result['results']['bindings'][0]['count']['value'])
    logging.info('Loci integer identifiers interval: [{0} .. {1}]'
                 ''.format(total_loci, total_loci+len(loci_data)))

    # response with locus URI, prefix and insertion status
    response = {}
    # locus file content hash mapping to locus URI
    hash_to_uri = {}
    # set starting integer identifier
    start_id = total_loci + 1
    # create loci URIs and map to original files
    for i, locus in enumerate(loci_data):
        locus_uri = '{0}loci/{1}'.format(base_url, start_id)
        locus_prefix = '{0}-{1}'.format(loci_prefix, '{:06d}'.format(start_id))
        locus.append(locus_uri)
        locus.append(locus_prefix)
        response[locus[1]] = [locus_uri]
        hash_to_uri[locus[1]] = locus_uri
        # increment for next locus
        start_id += 1

    # define path to file with schema upload status data
    hashes_file = os.path.join(temp_dir,
                               '{0}_{1}_hashes'.format(species_id, schema_id))

    # read schema upload status data
    if os.path.isfile(hashes_file) is True:
        with open(hashes_file, 'rb') as hf:
            schema_hashes = pickle.load(hf)
    else:
        logging.warning('Could not find schema upload status file. Aborting.')
        sys.exit(1)

    # insert loci
    insert_queries, insert = create_insert_queries(loci_data, schema_hashes)

    logging.info('{0} loci to insert out of {1} total loci '
                 'in schema.'.format(insert, len(loci_data)))

    # insert data to create loci
    if len(insert_queries) > 0:
        loci_insertion = send_queries(insert_queries)
        insert_status, success, failed = results_status(loci_insertion)

        for h, v in insert_status.items():
            if v is True:
                schema_hashes[h][1][0] = hash_to_uri[h]
                response[h].append(v)
            elif v is False:
                response[h].append(v)

        logging.info('Successfully inserted {0} loci. '
                     'Failed {1}'.format(success, failed))
        # halt process if it could not insert all loci
        if failed > 0:
            logging.warning('Could not insert all loci. Aborting.')
            sys.exit(1)

    # link loci to species
    sp_queries, link = species_link_queries(loci_data,
                                            schema_hashes,
                                            species_uri)

    logging.info('{0} loci to link to species out of {1} total loci '
                 'in schema.'.format(link, len(loci_data)))

    if len(sp_queries) > 0:
        species_links = send_queries(sp_queries)
        link_status, success, failed = results_status(species_links)

        for h, v in link_status.items():
            if v is True:
                schema_hashes[h][1][1] = True
                response[h].append(v)
            elif v is False:
                response[h].append(v)

        logging.info('Successfully linked {0} loci to species. '
                     'Failed {1}'.format(success, failed))

    # link loci to schema
    sc_queries, link = schema_link_queries(loci_data,
                                           schema_hashes,
                                           schema_uri)

    logging.info('{0} loci to link to schema out of {1} total loci '
                 'in schema.'.format(link, len(loci_data)))

    if len(sc_queries) > 0:
        schema_links = send_queries(sc_queries)
        link_status, success, failed = results_status(schema_links)

        for h, v in link_status.items():
            if v is True:
                schema_hashes[h][1][2] = True
                response[h].append(v)
            elif v is False:
                response[h].append(v)

        logging.info('Successfully linked {0} loci to schema. '
                     'Failed {1}'.format(success, failed))

    # save updated schema hashes
    with open(hashes_file, 'wb') as hf:
        pickle.dump(schema_hashes, hf)

    # write response to file
    response_file = os.path.join(temp_dir,
                                 '{0}_{1}_loci_response'.format(species_id,
                                                                schema_id))
    with open(response_file, 'wb') as rf:
        pickle.dump(response, rf)

    # remove temp file
    os.remove(loci_file)

    end = time.time()
    delta = end - start

    return response_file


if __name__ == '__main__':

    args = parse_arguments()

    main(args[0])
