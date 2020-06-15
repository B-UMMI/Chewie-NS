#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Purpose
-------

This module creates new loci in the Chewie-NS and associates those
loci with their species and schema. The module attributes loci
identifiers sequentially and ensures that identifiers are not repeated
to avoid overlaps/conflicts.

Expected input
--------------

The process expects the following variable wheter through command line
execution or invocation of the :py:func:`main` function:

- ``-i``, ``input_dir`` : Temporary directory that receives the
  data necessary for schema insertion (the basename has the
  species and schema identifiers).

    - e.g.: ``./schema_insertion_temp/1_1``

Code documentation
------------------
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
from itertools import repeat

from SPARQLWrapper import SPARQLWrapper

from app.utils import sparql_queries as sq
from app.utils import auxiliary_functions as aux


logfile = './log_files/schema_loci_inserter.log'
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%Y-%m-%dT%H:%M:%S',
                    filename=logfile)


thread_local = threading.local()


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

    if not hasattr(thread_local, 'session'):
        thread_local.session = requests.Session()

    return thread_local.session


def post_loci(query_data, local_sparql, virtuoso_user, virtuoso_pass):
    """ Performs a POST request to insert a new locus or link
        a locus to its species or schema.

        Parameters
        ----------
        query_data : tup
            A tuple with three elements: the locus hash, the locus
            URI and the SPARQL query that will be executed by
            Virtuoso's SPARQL endpoint.

        Returns
        -------
        A tuple with the locus hash and the status code of the
        POST request.
    """

    locus_hash = query_data[0]
    locus_uri = query_data[1]
    query = query_data[2]

    session = get_session()
    headers = {'content-type': 'application/sparql-query'}
    tries = 0
    max_tries = 5
    valid = False
    while valid is False and tries < max_tries:
        with session.post(local_sparql, data=query, headers=headers,
                          auth=requests.auth.HTTPBasicAuth(virtuoso_user, virtuoso_pass)) as response:
            status_code = response.status_code
            if status_code > 201:
                tries += 1
                logging.warning('Could not insert data for locus {0}\n'
                                'Response content:\n{1}\nRetrying ({2})'
                                '...\n'.format(locus_uri, response.content, tries))
            else:
                valid = True

    return (locus_hash, status_code)


def send_queries(loci_queries, local_sparql, virtuoso_user, virtuoso_pass):
    """ Sends a set of requests to Virtuoso's SPARQL endpoint.

        Parameters
        ----------
        loci_queries : list of tup
            A list with a tuple per loci to insert or associate
            with the species or schema. Each tuple has three
            elements: the locus hash, the locus URI and the
            SPARQL query that will be used to insert the data
            into Virtuoso's database.

        Returns
        -------
        responses : dict
            A dictionary with loci hashes as keys and response
            status codes as values.
    """

    responses = {}
    total = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        for res in executor.map(post_loci, loci_queries, repeat(local_sparql),
                                repeat(virtuoso_user), repeat(virtuoso_pass)):
            responses[res[0]] = res[1]
            total += 1

    return responses


def assign_identifiers(loci_data, schema_hashes, loci_prefix, start_id, base_url):
    """ Assigns identifiers to loci.

        Parameters
        ----------
        loci_data : list of list
            A list with one sublist per locus. Each
            sublist has seven elements: the locus
            original name, the locus hash, the UniProt
            annotation name, the UniProt annotation URI,
            the UniProt annotation label, the User
            annotation and a Custom annotation.
        schema_hashes : dict
            A dictionary with loci hashes as keys and lists
            as values. Each list has two elements: a bool
            that indicates if the alleles for that locus
            have been uploaded and a sublist with three
            bool elements that indicate if the locus has
            been inserted, linked to the species and linked
            to the schema.
        loci_prefix : str
            The prefix to include in the name of
            all loci.
        start_id : int
            The starting identifier for new loci.

        Returns
        -------
        A list with the following elements:

        - response (dict): a dictionary with loci
          hashes as keys and lists with loci URIs as values.
        - hash_to_uri (dict): a dictionary with loci hashes
          as keys and loci URIs as values.
        - loci_data (list): the input ``loci_data`` with
          the locus URI and locus prefix appended to each
          sublist.
    """

    # response with locus URI
    response = {}
    # locus file content hash mapping to locus URI
    hash_to_uri = {}

    # create loci URIs and map to original files
    for i, locus in enumerate(loci_data):
        inserted = schema_hashes[locus[1]][1][0]
        # locus is new
        if inserted is False:
            locus_uri = '{0}loci/{1}'.format(base_url, start_id)
            locus_prefix = '{0}-{1}'.format(loci_prefix, '{:06d}'.format(start_id))
            # increment for next locus
            start_id += 1
        # locus was previously inserted, do not assign new identifier
        else:
            locus_uri = inserted
            locus_prefix = '{0}-{1}'.format(loci_prefix, '{:06d}'.format(locus_uri.split('/')[-1]))

        locus.append(locus_uri)
        locus.append(locus_prefix)
        response[locus[1]] = [locus_uri]
        hash_to_uri[locus[1]] = locus_uri

    return [response, hash_to_uri, loci_data]


def create_insert_queries(loci_data, schema_hashes, virtuoso_graph):
    """ Creates SPARQL queries to insert loci into the Chewie-NS.

        Parameters
        ----------
        loci_data : list of list
            A list with one sublist per locus. It needs
            to have the same structure as the variable with
            same name returned by the :py:func:`assign_identifiers`
            function.
        schema_hashes : dict
            A dictionary with loci hashes as keys and lists
            as values. Each list has two elements: a bool
            that indicates if the alleles for that locus
            have been uploaded and a sublist with three
            bool elements that indicate if the locus has
            been inserted, linked to the species and linked
            to the schema.

        Returns
        -------
        A list with two elements:

        - insert_queries (list): list with the SPARQL
          queries to insert the loci.
        - insert (int): the number of loci that need
          to be inserted (function determines if a locus
          has already been inserted).
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

            # remove escape bars
            insert_query = insert_query.replace('\\', ' ')
            insert_queries.append((l[1], l[7], insert_query))

    return [insert_queries, insert]


def species_link_queries(loci_data, schema_hashes, species_uri, virtuoso_graph):
    """ Creates SPARQL queries to loci loci to a species.

        Parameters
        ----------
        loci_data : list
            A list with one sublist per locus. It needs
            to have the same structure as the variable with
            same name returned by the :py:func:`assign_identifiers`
            function.
        schema_hashes : dict
            A dictionary with loci hashes as keys and lists
            as values. Each list has two elements: a bool
            that indicates if the alleles for that locus
            have been uploaded and a sublist with three
            bool elements that indicate if the locus has
            been inserted, linked to the species and linked
            to the schema.
        species_uri : str
            The species URI in the Chewie-NS.

        Returns
        -------
        A list with two elements:

        - link_queries (list): list with the SPARQL
          queries to link loci to species.
        - link (int): number of loci that need to be
          linked to the species.
    """

    link = 0
    link_queries = []
    for l in loci_data:
        sp_link = schema_hashes[l[1]][1][1]
        if sp_link is False:
            link += 1
            link_query = (sq.INSERT_SPECIES_LOCUS.format(virtuoso_graph,
                                                         l[7], species_uri))

            link_queries.append((l[1], l[7], link_query))

    return [link_queries, link]


def schema_link_queries(loci_data, schema_hashes, schema_uri, virtuoso_graph):
    """ Creates SPARQL queries to loci loci to a schema.

        Parameters
        ----------
        loci_data : list
            A list with one sublist per locus. It needs
            to have the same structure as the variable with
            same name returned by the :py:func:`assign_identifiers`
            function.
        schema_hashes : dict
            A dictionary with loci hashes as keys and lists
            as values. Each list has two elements: a bool
            that indicates if the alleles for that locus
            have been uploaded and a sublist with three
            bool elements that indicate if the locus has
            been inserted, linked to the species and linked
            to the schema.
        schema_uri : str
            The schema URI in the Chewie-NS.

        Returns
        -------
        A list with two elements:

        - link_queries (list): list with the SPARQL
          queries to link loci to schema.
        - link (int): number of loci that need to be
          linked to the schema.
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

            link_queries.append((l[1], l[7], link_query))
            schema_part_id += 1

    return [link_queries, link]


def results_status(results):
    """ Determines if queries were executed successfully
        based on status codes.

        Parameters
        ----------
        results : dict
            A dictionary with loci hashes as keys and
            status codes as values.

        Returns
        -------
        A list with three elements:

        - status (dict): a dictionary with loci hashes
          as keys and True/False as values.
        - success (int): number of queries that were
          successfully executed.
        - failed (int): number of queries that were not
          successfully executed.
    """

    status = {}
    success = 0
    failed = 0
    for k in results:
        # change upload status
        status_code = results[k]
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
                        dest='input_dir', required=True,
                        help='Temporary directory that '
                             'receives the data necessary '
                             'for schema insertion.')

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

    # get species and schema identifiers
    species_id = os.path.basename(temp_dir).split('_')[0]
    schema_id = os.path.basename(temp_dir).split('_')[1]

    # create species and schema URIs
    species_uri = '{0}species/{1}'.format(base_url, species_id)
    schema_uri = '{0}/schemas/{1}'.format(species_uri, schema_id)

    logging.info('Started loci insertion for '
                 'schema {0}'.format(schema_uri))

    # define path to file with loci data
    loci_file = os.path.join(temp_dir, '{0}_{1}_loci'.format(species_id,
                                                             schema_id))

    # read loci data
    if os.path.isfile(loci_file) is True:
        with open(loci_file, 'rb') as lf:
            loci_prefix, loci_data = pickle.load(lf)
            logging.info('Loci prefix is {0}.'.format(loci_prefix))
    else:
        logging.warning('Could not find file {0}. '
                        'Aborting\n\n'.format(loci_file))
        sys.exit(1)

    # determine total number of loci in the NS
    # result = aux.get_data(SPARQLWrapper(local_sparql),
    #                       (sq.COUNT_TOTAL_LOCI.format(virtuoso_graph)))
    result = aux.get_data(SPARQLWrapper(sparql),
                          (sq.COUNT_TOTAL_LOCI.format(graph)))

    total_loci = int(result['results']['bindings'][0]['count']['value'])

    # define path to file with schema upload status data
    hashes_file = os.path.join(temp_dir,
                               '{0}_{1}_hashes'.format(species_id, schema_id))

    # read schema upload status data
    if os.path.isfile(hashes_file) is True:
        with open(hashes_file, 'rb') as hf:
            schema_hashes = pickle.load(hf)
    else:
        logging.warning('Could not find schema upload status file. Aborting.\n\n')
        sys.exit(1)

    # assign identifiers to new loci based on the total number of loci in the Chewie-NS
    start_id = total_loci + 1
    response, hash_to_uri, loci_data, = assign_identifiers(loci_data, schema_hashes,
                                                           loci_prefix, start_id,
                                                           base_url)

    # insert loci
    insert_queries, insert = create_insert_queries(loci_data, schema_hashes, graph)
    logging.info('{0} loci to insert out of {1} total loci '
                 'in schema.'.format(insert, len(loci_data)))
    logging.info('Loci integer identifiers interval: [{0} .. {1}]'
                 ''.format(total_loci+1, total_loci+insert))

    # insert data to create loci
    if len(insert_queries) > 0:
        loci_insertion = send_queries(insert_queries, sparql, user, password)
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
            logging.warning('Could not insert all loci. Aborting.\n\n')
            sys.exit(1)

    # link loci to species
    sp_queries, link = species_link_queries(loci_data,
                                            schema_hashes,
                                            species_uri,
                                            graph)

    logging.info('{0} loci to link to species out of {1} total loci '
                 'in schema.'.format(link, len(loci_data)))

    if len(sp_queries) > 0:
        species_links = send_queries(sp_queries, sparql, user, password)
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
                                           schema_uri,
                                           graph)

    logging.info('{0} loci to link to schema out of {1} total loci '
                 'in schema.'.format(link, len(loci_data)))

    if len(sc_queries) > 0:
        schema_links = send_queries(sc_queries, sparql, user, password)
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

    logging.info('Finished loci insertion for '
                 'schema {0}\n\n'.format(schema_uri))

    return response_file


if __name__ == '__main__':

    args = parse_arguments()

    main(args[0], args[1], args[2],
         args[3], args[4], args[5])
