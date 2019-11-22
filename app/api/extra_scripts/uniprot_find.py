#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AUTHOR

    Rafael Mamede
    github: @rfm-targa

DESCRIPTION



"""

import os
import csv
import time
import gzip
import shutil
import argparse
import urllib.request
import concurrent.futures
from collections import defaultdict

from Bio import SeqIO
from Bio.Seq import Seq
from SPARQLWrapper import SPARQLWrapper, JSON


virtuoso_server = SPARQLWrapper('http://sparql.uniprot.org/sparql')


def translate_sequence(dna_str, table_id):
    """ Translate a DNA sequence using the BioPython package.

        Args:
            dna_str (str): DNA sequence as string type.
            table_id (int): translation table identifier.

        Returns:
            protseq (str): protein sequence created by translating
            the input DNA sequence.
    """

    myseq_obj = Seq(dna_str)
    protseq = Seq.translate(myseq_obj, table=table_id, cds=True)

    return protseq

# check if this function works well with many False cases
def is_fasta(filename):
    """ Checks if a file is a FASTA file.
        Args:
            filename (str): the full path to the FASTA file
        Returns:
            True if FASTA file,
            False otherwise
    """

    try:
        with open(filename, 'r') as handle:
            fasta = SeqIO.parse(handle, 'fasta')

            # returns True if FASTA file, False otherwise
            return any(fasta)

    except UnicodeDecodeError:
        return False


def check_if_list_or_folder(folder_or_list):
    """ Checks if the input is a file or a directory.
        Args:
            folder_or_list (str): the full path to the file or directory
        Returns:
            list_files (str) if folder_or_list is a path to a file,
            list_files (list) if folder_or_list is a path to a directory,
            Raises Exception otherwise
    """

    # check if input argument is a file or a directory
    if os.path.isfile(folder_or_list):
        list_files = folder_or_list

    elif os.path.isdir(folder_or_list):

        fasta_files = []

        for genome in os.listdir(folder_or_list):

            genepath = os.path.join(folder_or_list, genome)

            # do not continue if genepath is a dir
            if os.path.isdir(genepath):
                continue

            # check if file is a FASTA file
            if is_fasta(genepath):
                fasta_files.append(os.path.abspath(genepath))

        # if there are FASTA files
        list_files = 'genes_list.txt'
        if fasta_files:
            # store full paths to FASTA files
            with open(list_files, 'w') as f:
                for genome in fasta_files:
                    f.write(genome + '\n')
        else:
            raise Exception('There were no FASTA files in the given directory. Please provide a directory \
                            with FASTA files or a file with the list of full paths to the FASTA files.')

    else:
        raise Exception('Input argument is not a valid directory or file with a list of paths. \
                        Please provide a valid input, either a folder with FASTA files or a file with \
                        the list of full paths to FASTA files (one per line).')

    return list_files


def select_name(result):
    """
    """

    try:
        aux = result["results"]["bindings"]
        for elem in aux:
            if 'fname' in elem.keys():
                name = str(elem['fname']['value'])
            elif 'fname2' in elem.keys():
                name = str(elem['fname2']['value'])
            elif 'fname3' in elem.keys():
                name = str(elem['fname3']['value'])

            url = str(elem['seq']['value'])

        return [name, url]

    except Exception:
        
        return ['', '']

#sparql_queries = ('GCA-001592385-protein883_protein', queries['GCA-001592385-protein883_protein'])
def get_data(sparql_queries):
    """
    """

    locus = sparql_queries[0]
    queries = sparql_queries[1]
    virtuoso_server.setReturnFormat(JSON)
    virtuoso_server.setTimeout(10)

    url = ''
    name = ''
    prev_name = ''
    found = False
    unpreferred_names = ['Uncharacterized protein', 'hypothetical protein', 'DUF']

    # implement more than 1 retry!!!
    alleles = len(queries)
    a = 0
    while found is False:
        virtuoso_server.setQuery(queries[a])
        try:
            result = virtuoso_server.query().convert()

            name, url = select_name(result)

            if prev_name == '' and not any([n in name for n in unpreferred_names]):
                prev_name = name
                found = True

        except:
            #print("A request to uniprot timed out, trying new request")
            time.sleep(5)
            result = virtuoso_server.query().convert()
            name, url = select_name(result)
            if prev_name == '' and not any([n in name for n in unpreferred_names]):
                prev_name = name
                found = True

        a += 1
        if a == alleles:
            found = True

    return (locus, prev_name, url)


def uniprot_query(sequence):
    """
    """
    
#    query = ('PREFIX rdf:<http://www.w3.org/1999/02/22-rdf-syntax-ns#>  '
#                'PREFIX up: <http://purl.uniprot.org/core/> '
#                'PREFIX rdfs:<http://www.w3.org/2000/01/rdf-schema#> '
#                'select ?seq ?label ?sname where { ?b a up:Simple_Sequence; '
#                'rdf:value "' + sequence + '". ?seq up:sequence ?b. '
#                'OPTIONAL {?seq rdfs:label ?label.} '
#                'OPTIONAL {?seq up:submittedName ?rname2. ?rname2 up:fullName ?sname.}}LIMIT 20')
    
    
    query = ('PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>  '
             'PREFIX up: <http://purl.uniprot.org/core/> '
             'select ?seq ?fname ?fname2 ?fname3  where {'
             '{?b a up:Simple_Sequence; rdf:value '
             '"'+sequence+'". ?seq up:sequence ?b. '
             'OPTIONAL{?seq up:submittedName ?sname. ?sname up:fullName ?fname2} '
             'OPTIONAL{?seq up:recommendedName ?rname.?rname up:fullName ?fname} }'
             'UNION{?seq a up:Sequence; rdf:value "'+sequence+'"; '
             'rdfs:label ?fname3. }}')

    return query


schema_directory = '/home/pcerqueira/Lab_Software/refactored_ns/ns_security/extra_scripts/yersinia_test_schema/result_schema'
parent_dir = os.path.dirname(schema_directory)
protein_table = '/home/pcerqueira/Lab_Software/refactored_ns/ns_security/extra_scripts/yersinia_test_schema/proteinID_Genome.tsv'
cpu_count = 6

def main(schema_directory, protein_table, cpu_count):

    gene_files = check_if_list_or_folder(schema_directory)

    with open(gene_files, 'r') as f:
        genes_list = f.readlines()
        genes_list = [file.strip() for file in genes_list]

    if protein_table:
        dictaux = defaultdict(list)
        with open(protein_table) as csvfile:
            reader = csv.reader(csvfile, delimiter='\t')
            headers = next(reader)
            for row in reader:
                dictaux[row[0]+row[-1]] = [str(e) for e in row]
    else:
        pass

    print('Processing the fastas')

    # translate all proteins
    # and save into files
    protein_files = []
    for file in genes_list:
        prots = []
        locus_id = os.path.basename(file)
        locus_id = locus_id.split('.fasta')[0]
        for record in SeqIO.parse(file, 'fasta'):
            protid = record.id
            protein = translate_sequence(str(record.seq), 11)
            prots.append((protid, protein))
        
        protein_lines = []
        for prot in prots:
            header = '>{0}\n'.format(prot[0])
            sequence = '{0}\n'.format(prot[1])
            protein_lines.append(header)
            protein_lines.append(sequence)
        
        protein_lines = ''.join(protein_lines)
        protein_file = '{0}/{1}{2}'.format(parent_dir, locus_id, '_protein.fasta')
        with open(protein_file, 'w') as pf:
            pf.write(protein_lines)
        protein_files.append(protein_file)
        
    # construct queries
    # create generators with queries
    queries = {}
    for file in protein_files:
        file_id = os.path.basename(file).split('.fasta')[0]
        queries[file_id] = []
        for record in SeqIO.parse(file, 'fasta'):
            queries[file_id].append(uniprot_query(str(record.seq)))

    # multithreading test
    start = time.time()
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=30) as executor:
        # Start the load operations and mark each future with its URL
        for res in executor.map(get_data, list(queries.items())):
            results.append(res)
    end = time.time()
    delta = end - start

    genes_ids = []
    protein_names = []
    uniprot_urls = []
    for res in results:
        genes_ids.extend(os.path.basename(file).split('.')[0] for file in res[0])
        protein_names.extend(res[1])
        uniprot_urls.extend(res[2])

    null = 0
    valid = 0
    hypothetical = 0
    uncharacterized = 0
    protein_lines = []
    for n in range(len(genes_ids)):
        
        name = protein_names[n]
        gene_id = genes_ids[n]
        print('{0}: {1}'.format(gene_id, name))

        if 'Uncharacterized protein' in name:
            uncharacterized += 1
            valid += 1
        elif 'hypothetical' in name:
            hypothetical += 1
            valid += 1
        elif name == '':
            null += 1
        else:
            valid += 1

        protid = aux[-1].replace(".fasta", "")
        aux2 = aux[0].split("/")[-1].replace("-", "_")
        dictaux[aux2+protid].append(str(name))
        dictaux[aux2+protid].append(str(url))
        dictaux[aux2+protid].insert(0, os.path.basename(gene))
        selected_prots.append(aux2+protid)

    newProfileStr = "Fasta\t"+('\t'.join(map(str, headers)))+"\tname\turl\n"
    for key in set(sorted(selected_prots, key=str)):
        newProfileStr += ('\t'.join(map(str, dictaux[key])))+"\n"

    print("Found : " +str(got)+ ", "+str(len(uncharacterized))+" of them uncharacterized/hypothetical. Nothing found on :"+str(len(notgot)))
    with open("new_protids.tsv", "w") as f:
        f.write(newProfileStr)

    print("Done")


def parse_arguments():

    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument('-i', type=str, required=True, dest='input_files',
                        help='')

    parser.add_argument('-t', type=str, required=True, dest='protein_table',
                        help='')

    parser.add_argument('--cpu', type=int, required=False, dest='core_count',
                        default=1, help='')

    args = parser.parse_args()

    return [args.input_files, args.protein_table, args.core_count]


if __name__ == '__main__':

    args = parse_arguments()
    main(args[0], args[1], args[2])
