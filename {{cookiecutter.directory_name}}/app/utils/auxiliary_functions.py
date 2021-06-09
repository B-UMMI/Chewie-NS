#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Purpose
-------
This module contains auxiliary functions used in the API.

Code documentation
------------------

"""


import os
import re
import csv
import time
import json
import shutil
import pickle
import hashlib
import requests
import itertools
import urllib.request
import multiprocessing
from flask import abort
from collections import Counter
from SPARQLWrapper import SPARQLWrapper, JSON
from urllib.parse import urlparse, urlencode, urlsplit, parse_qs

from Bio import SeqIO
from Bio.Seq import Seq
from Bio.Alphabet import generic_dna


UNIPROT_SERVER = SPARQLWrapper("http://sparql.uniprot.org/sparql")


def binary_file_hash(binary_file):
    """ Obtains the hash of binary file.

    Parameters
    ----------
    binary_file: str
        Path to the binary file.

    Returns
    -------
    file_hash: str
        Hash of the binary file.
    """

    with open(binary_file, 'rb') as bf:
        file_hash = hashlib.blake2b()
        file_text = bf.read()
        file_hash.update(file_text)
        file_hash = file_hash.hexdigest()

    return file_hash


def write_schema_config(blast_score_ratio, ptf_hash,
                        translation_table, minimum_sequence_length,
                        chewie_version, size_threshold, output_directory):
    """ Writes a pickle (binary) file with the schema configurations.

    Parameters
    ----------
    bsr: float
        Blast Score Ratio used to create the schema.
    prodigal_training_file: str
        Hash of the prodigal training file.
    translation_table: int
        Translation table used to create the schema.
    minimum_locus_length: int
        Minimum locus length allowed to create the schema.
    chewBBACA_version: str
        Version of chewBBACA used to create the schema.
    size_threshold: str

    Returns
    -------
    list
        List containing a bool confirming the creation of the
        configuration file and a str corresponding to the path
        of the configuration file.

    """

    size_threshold = None if size_threshold in [None, 'None'] else float(size_threshold)

    params = {}
    params['bsr'] = [float(blast_score_ratio)]
    params['prodigal_training_file'] = [ptf_hash]
    params['translation_table'] = [int(translation_table)]
    params['minimum_locus_length'] = [int(minimum_sequence_length)]
    params['chewBBACA_version'] = [chewie_version]
    params['size_threshold'] = [size_threshold]

    config_file = os.path.join(output_directory, '.schema_config')
    with open(config_file, 'wb') as cf:
        pickle.dump(params, cf)

    return [os.path.isfile(config_file), config_file]


def write_gene_list(schema_dir):
    """ Writes a pickle (binary) file containing a list of input genes.

    Parameters
    ----------
    schema_dir: str
        Path to the schema directory.

    Returns
    -------
    list
        List containing a bool confirming the creation of the
        gene list file and a str corresponding to the path
        of the gene list file.
    """

    schema_files = [file for file in os.listdir(
        schema_dir) if '.fasta' in file]
    schema_list_file = os.path.join(schema_dir, '.genes_list')
    with open(schema_list_file, 'wb') as sl:
        pickle.dump(schema_files, sl)

    return [os.path.isfile(schema_list_file), schema_list_file]


def is_fasta(filename):
    """ Checks if a file is a FASTA file.

        Parameters
        ----------
        filename: str
            The full path to the FASTA file.

        Returns
        -------
        bool
            True if FASTA file,
            False otherwise.
    """

    with open(filename, 'r') as handle:
        try:
            fasta = SeqIO.parse(handle, 'fasta')
        except:
            fasta = [False]

        # returns True if FASTA file, False otherwise
        return any(fasta)


def filter_files(files_list, suffixes):
    """ Checks if files names contain any suffix from a list of suffixes.

        Parameters
        ----------
        files_list: list
            a list with all files names.

        Returns
        -------
        suffixes: list
            a list with all suffixes to search for in
            the files names.
    """

    accepted = [file for file in files_list
                if any([True for suffix in suffixes if suffix in file])]

    return accepted


def filter_non_fasta(files_list):
    """ Creates a new list of files names/paths that only contains FASTA files.

        Parameters
        ----------
        files_list: list
            a list with files names/paths.

        Returns
        -------
        real_fasta: list
            a list with files names/paths that correspond
            to FASTA files.
    """

    real_fasta = [file for file in files_list if is_fasta(file) is True]

    return real_fasta


def gene_seqs_info(gene):
    """ Determines the total number of alleles and the mean length
        of allele sequences per gene.

        Parameters
        ----------
        genes_list: list
            a list with names/paths for FASTA
            files.

        Returns
        -------
        genes_info: list
            a list with a sublist for each input
            gene file. Each sublist contains a gene identifier, the
            total number of alleles for that gene and the mean length
            of allele sequences for that gene.
    """

    seq_generator = SeqIO.parse(gene, 'fasta', generic_dna)
    alleles_lengths = [len(allele) for allele in seq_generator]
    mean_length = sum(alleles_lengths)/len(alleles_lengths)
    total_seqs = len(alleles_lengths)
    genes_info = [gene, total_seqs, mean_length]

    return genes_info


def make_blast_db(input_fasta, output_path, db_type):
    """ Creates a BLAST database.

        Parameters
        ----------
        input_fasta: str
            path to the input file with sequences.
        output_path: str
            path to the output database.
        db_type: str
            type of the database, nucleotide (nuc) or
            protein (prot).

        Returns
        -------
        Creates a BLAST database with the input sequences.
    """

    makedb_cmd = ('makeblastdb -in {0} -out {1} -parse_seqids '
                  '-dbtype {2} > /dev/null'.format(input_fasta,
                                                   output_path,
                                                   db_type))
    os.system(makedb_cmd)


def determine_blast_task(proteins):
    """ Determine the type of task that should be used to run BLAST.

        Parameters
        ----------
        proteins: str
            path to a file with sequences.

        Returns
        -------
        blast_task: str
            a string that indicates the type of BLAST
            task to run.
    """

    blast_task = 'blastp'
    proteins_lengths = [len(p) for p in proteins]
    minimum_length = min(proteins_lengths)
    if minimum_length < 30:
        blast_task = 'blastp-short'

    return blast_task


def create_directory(directory_path):
    """ Creates a diretory if it does not exist.

        Parameters
        ----------
        directory_path: str
            Path to the directory

        Returns
        -------
        Creates a directory.

    """

    if not os.path.exists(directory_path):
        os.makedirs(directory_path)


def join_paths(parent_path, child_path):
    """ Joins a parent directory and a subdirectory.

        Parameters
        ----------
        parent_path: str
            Parent directory path
        child_path: str
            Subdirectory path

        Returns
        -------
        joined_paths: str
            The parent path joined with the
            subdirectory path.
    """

    joined_paths = os.path.join(parent_path, child_path)

    return joined_paths


def check_input_type(input_path, output_file):
    """ Checks if the input is a file or a directory.

        Parameters
        ----------
        folder_or_list: str
            the full path to the file or directory

        Returns
        -------
        list_files: str
            if folder_or_list is a path to a file,
        list_files: list
            if folder_or_list is a path to a directory,

        Raises
        ------
        Exception
            If none of the above is True.
    """

    # check if input argument is a file or a directory
    if os.path.isfile(input_path):
        list_files = input_path

    elif os.path.isdir(input_path):

        # we need to get only files with FASTA extension
        files = os.listdir(input_path)
        files = filter_files(files, ['.fasta', '.fna', '.ffn'])
        # get absolute paths
        files = [os.path.join(input_path, file) for file in files]
        # filter any directories that migh end with FASTA extension
        files = [file for file in files if os.path.isdir(file) is False]

        # only keep files whose content is typical of a FASTA file
        fasta_files = filter_non_fasta(files)

        # if there are FASTA files
        if len(fasta_files) > 0:
            # store full paths to FASTA files
            with open(output_file, 'w') as f:
                for file in fasta_files:
                    f.write(file + '\n')
        else:
            raise Exception('There were no FASTA files in the given '
                            'directory. Please provide a directory'
                            'with FASTA files or a file with the '
                            'list of full paths to the FASTA files.')

        list_files = output_file

    else:
        raise Exception('Input argument is not a valid directory or '
                        'file with a list of paths. Please provide a '
                        'valid input, either a folder with FASTA files '
                        'or a file with the list of full paths to FASTA '
                        'files (one per line).')

    return list_files


def flatten_list(list_to_flatten):
    """Flattens one level of a nested list

        Parameters
        ----------
        list_to_flatten: list

        Returns
        -------
        list
            Flattened list

        Example
        -------
        >>> flatten_list([[[1,2],[3,4]]])
        [[1, 2], [3, 4]]

    """

    return list(itertools.chain(*list_to_flatten))


def read_blast_tabular(blast_tabular_file):
    """ Read a file with BLAST results in tabular format

        Parameters
        ----------
        blast_tabular_file: str
            path to output file of BLAST.

        Returns
        -------
        blasting_results: list
            a list with a sublist per line
            in the input file.
    """

    with open(blast_tabular_file, 'r') as blastout:
        reader = csv.reader(blastout, delimiter='\t')
        blasting_results = [row for row in reader]

    return blasting_results


def fasta_lines(identifiers, sequences_dictionary):
    """ Creates list with line elements for a FASTA file based on the sequence
        identifiers passed.

        Parameters
        ----------
        identifiers: list
            a list with the identifiers of sequences that
            will be included in the list.
        sequences_dictionary: dict
            a dictionary with sequence identifeirs
            as keys and sequences as values.

        Returns
        -------
        seqs_lines: list
            a list with strings representing the header of
            the sequence and the sequence for each of the specified sequence
            identifiers.
    """

    seqs_lines = ['>{0}\n{1}\n'.format(seqid, sequences_dictionary[seqid])
                  for seqid in identifiers]

    return seqs_lines


def write_list(lines, output_file):
    """ Writes list elements to file.

        Parameters
        ----------
        lines: list
            list with the ordered lines that will be written
            to the output file.
        output_file: str
            name/path of the output file.

        Returns
        -------
        Writes contents of 'lines' argument into 'output_file'.
    """

    with open(output_file, 'w') as file:
        file.writelines(lines)


def determine_duplicated_prots(proteins):
    """ Creates a dictionary with protein sequences as keys and all sequence
        identifiers associated with that protein as values.

        Parameters
        ----------
        proteins: dict
            dictionary with protein sequence identifiers as
            keys and protein sequences as values.

        Returns
        -------
        equal_prots: dict
            dictionary with protein sequence as keys and
            sequence identifiers that are associated with each protein sequence
            as values.
    """

    equal_prots = {}
    for protid, protein in proteins.items():
        # if protein sequence was already added as key
        if protein in equal_prots:
            # append new protid
            equal_prots[protein].append(protid)
        # else add new protein sequence as key and protid
        # as value
        else:
            equal_prots[protein] = [protid]

    return equal_prots


def determine_longest(seqids, proteins):
    """ Determines which sequence is the longest among
        sequences with the specified identifiers.

        Parameters
        ----------
        seqids: list
        proteins: dict

        Returns
        -------
        chosen:
            Longest sequence

    """

    seqids_prots = [(seqid, proteins[seqid]) for seqid in seqids]
    sorted_prots = sorted(seqids_prots, key=lambda x: len(x[1]), reverse=True)
    chosen = sorted_prots[0][0]

    return chosen


def locus_mode(alleles):
    """ Determines the mode value from a set of sequence length values.

        Parameters
        ----------
        alleles: dict
            dictionary with alleles identifiers as keys
            and the allele length as value.

        Returns
        -------
        modes: list
            The most frequent length values. The distribution
            of length values for a locus might have more than one mode.
    """

    # determine frequency of each length value
    counts = Counter(alleles.values())
    # order by most common first
    most_common = counts.most_common()

    # get most common
    modes = [most_common[0][0]]
    # determine if there are more length values that are as common
    modes += [m[0] for m in most_common[1:] if m[1] == most_common[0][1]]

    return modes


def mode_filter(alleles, size_threshold):
    """ Determines the mode from a set of input sequences
        and identifies sequences that have a length value
        smaller or greater than the mode based on a threshold.

        Parameters
        ----------
            alleles: dict
            size_threshold: float

        Returns
        -------
        list
            A list with the following variables:
                - modes (list):
                - alm (list):
                - asm (list):
                - alleles_lengths (dict):
    """

    alm = []
    asm = []

    # determine length value of all sequences
    alleles_lengths = {seqid: len(seq) for seqid, seq in alleles.items()}

    # determine mode/s
    modes = locus_mode(alleles_lengths)
    # determine top and bot length value limits
    max_mode = max(modes)
    top_limit = max_mode + (max_mode*size_threshold)
    min_mode = min(modes)
    bot_limit = min_mode - (min_mode*size_threshold)

    # determine sequences that are below or above limits
    alm = [seqid for seqid, length in alleles_lengths.items()
           if length > top_limit]
    asm = [seqid for seqid, length in alleles_lengths.items()
           if length < bot_limit]

    return [modes, alm, asm, alleles_lengths]


def get_seqs_dicts(gene_file, gene_id, table_id, min_len, size_threshold):
    """ Creates a dictionary mapping seqids to DNA sequences and
        another dictionary mapping protids to protein sequences.

        Parameters
        ----------
        gene_file: str
            path/name of the FASTA file with
            DNA sequences.
        table_id: int
            translation table identifier.

        Returns
        -------
        list
            List with following elements:
                dna_seqs (dict): dictionary with sequence identifiers as keys
                and DNA sequences as values.
                prot_seqs (dict): dictionary with protein identifiers as keys
                and Protein sequences as values.
                invalid_alleles (list): list with sequence identifiers of
                alleles that are not valid because they could not be
                translated.
    """

    seqid = 1
    dna_seqs = {}
    prot_seqs = {}
    seqids_map = {}
    invalid_alleles = []
    seq_generator = SeqIO.parse(gene_file, 'fasta', generic_dna)
    translated_seqs = [(rec.id, translate_dna(
        str(rec.seq), table_id, min_len)) for rec in seq_generator]
    total_seqs = len(translated_seqs)

    for rec in translated_seqs:
        # if the allele identifier is just an integer
        # add gene identifier as prefix
        try:
            int_seqid = int(rec[0])
            new_seqid = '{0}_{1}'.format(gene_id, int_seqid)
        except Exception:
            new_seqid = rec[0]

        # if returned value is a list, translation was successful
        if isinstance(rec[1], list):
            # we need to assign simple integers as sequence identifiers
            # because BLAST will not work if sequence identifiers are
            # too long
            seqids_map[str(seqid)] = new_seqid
            dna_seqs[new_seqid] = rec[1][0][1]
            prot_seqs[str(seqid)] = str(rec[1][0][0])
            seqid += 1
        # if returned value is a string, translation failed and
        # string contains exceptions
        elif isinstance(rec[1], str):
            invalid_alleles.append([new_seqid, rec[1]])

    if size_threshold is not None and len(prot_seqs) > 0:
        # remove alleles based on length mode and size threshold
        modes, alm, asm, alleles_lengths = mode_filter(
            dna_seqs, size_threshold)
        excluded = set(asm + alm)

        dna_seqs = {seqid: seq for seqid, seq in dna_seqs.items()
                    if seqid not in excluded}
        prot_seqs = {seqid: seq for seqid, seq in prot_seqs.items()
                     if seqids_map[seqid] not in excluded}

        modes_concat = ':'.join(map(str, modes))
        st_percentage = int(size_threshold*100)
        invalid_alleles += [[s, 'allele greater than {0}% locus length mode '
                                '({1}>{2})'.format(st_percentage, alleles_lengths[s], modes_concat)] for s in alm]
        invalid_alleles += [[s, 'allele smaller than {0}% locus length mode '
                                '({1}<{2})'.format(st_percentage, alleles_lengths[s], modes_concat)] for s in asm]

    return [dna_seqs, prot_seqs,
            invalid_alleles, seqids_map, total_seqs]


def split_genes_by_core(inputs, threads, method):
    """ Splits list with loci inputs into several sublists based
        on the number of sequence per locus (seqcount), the mean
        length of the sequences in each locus or the product of
        both variables.

        Parameters
        ----------
        inputs: list
            list with information about the data of
            each locus that needs to be processed.
        threads: int
            the number of sublists with inputs that
            should be created, based on the number of CPU threads
            that will be used to process the inputs.
        method: str
            "seqcount" to split inputs into sublists
            with even number of sequences, "length" to split based
            on mean length of sequences and "seqcount+length" to
            split based on both criteria.

        Returns
        -------
        splitted_ids: list
            subslists with paths to loci, each
            sublist containing paths for a set of loci that should
            not differ much from other sublists based on the criterion
            used to separate the inputs.
    """

    # initialize list with sublists to store inputs
    splitted_ids = [[] for cpu in range(threads)]
    # initialize list with chosen criterion values
    # for each sublist of inputs
    splitted_values = [0 for cpu in range(threads)]
    i = 0
    for locus in inputs:
        if method == 'seqcount':
            splitted_values[i] += locus[1]
        elif method == 'length':
            splitted_values[i] += locus[2]
        elif method == 'seqcount+length':
            splitted_values[i] += locus[1] * locus[2]
        splitted_ids[i].append(locus[0])
        # at the end of each iteration, choose the sublist
        # with lowest criterion value
        i = splitted_values.index(min(splitted_values))

    return splitted_ids


def concatenate_list(str_list, join_char):
    """ Concatenates list elements with specified
        character between each original list element.

        Parameters
        ----------
        sequence_ids: list
            list with strings that will be concatenated.
        join_char: str
            character that will be used to join all list
            elements.

        Returns
        -------
        ids_str: str
            concatenation of all strings in the input list.
    """

    concat = join_char.join(str_list)

    return concat


def write_text_chunk(output_file, text):
    """ Write single string to file.

        Parameters
        ----------
        output_file: str
            path/name of the file that will store
            the input text.
        text: str
            single string to write to file.

        Returns
        -------
        Writes input text to output file.
    """

    with open(output_file, 'w') as out:
        out.write(text)


def reverse_complement(dna_sequence):
    """ Determines the reverse complement of given DNA strand.

        Parameters
        ----------
        strDNA: str
            string representing a DNA sequence.

        Returns
        -------
        revC_dna: str
            the reverse complement of the DNA sequence, without
            lowercase letters.

        Example
        -------
        >>> reverse_complement('ATCGgcaNn')
        'NNTGCCGAT'
    """

    base_complement = {'A': 'T', 'C': 'G', 'G': 'C', 'T': 'A',
                       'a': 'T', 'c': 'G', 'g': 'C', 't': 'A',
                       'n': 'N', 'N': 'N'}

    # convert string into list with each character as a separate element
    bases = list(dna_sequence)

    # determine complement strand
    bases = [base_complement[base] for base in bases]

    complement_strand = ''.join(bases)

    # reverse strand
    reverse_complement_strand = reverse_str(complement_strand)

    return reverse_complement_strand


def reverse_str(string):
    """ Reverse character order in input string.

        Parameters
        ----------
        string: str
            string to be reversed.

        Returns
        -------
        revstr: str
            reverse of input string.
    """

    revstr = string[::-1]

    return revstr


def translate_sequence(dna_str, table_id):
    """ Translate a DNA sequence using the BioPython package.

        Parameters
        ----------
        dna_str: str
            DNA sequence as string type.
        table_id: int
            translation table identifier.

        Returns
        -------
        protseq: str
            protein sequence created by translating
            the input DNA sequence.
    """

    myseq_obj = Seq(dna_str)
    # sequences must be a complete and valid CDS
    protseq = Seq.translate(myseq_obj, table=table_id, cds=True)

    return protseq


def translate_dna_aux(dna_sequence, method, table_id):
    """ Tries to translate an input DNA sequence in specified orientation
        and stores exceptions when the input sequence cannot be translated.

        Parameters
        ----------
        dna_sequence: str
            string representing a DNA sequence.
        method: str
            a string specifying the way the sequence will
            be oriented to attempt translation.
        table_id: int
            translation table identifier.

        Returns
        -------
        list
            List with following elements if translation is successful:
                protseq (str): string representing the translated DNA sequence.
                myseq (str): string representing the DNA sequence in the
                orientation used to translate it.
            Otherwise, returns string derived from captured exception.
    """

    myseq = dna_sequence
    # try to translate original sequence
    if method == 'original':
        try:
            protseq = translate_sequence(myseq, table_id)
        except Exception as argh:
            return argh
    # try to translate the reverse complement
    elif method == 'revcomp':
        try:
            myseq = reverse_complement(myseq)
            protseq = translate_sequence(myseq, table_id)
        except Exception as argh:
            return argh
    # try to translate the reverse
    elif method == 'rev':
        try:
            myseq = reverse_str(myseq)
            protseq = translate_sequence(myseq, table_id)
        except Exception as argh:
            return argh
    # try to translate the reverse reverse complement
    elif method == 'revrevcomp':
        try:
            myseq = reverse_str(myseq)
            myseq = reverse_complement(myseq)
            protseq = translate_sequence(myseq, table_id)
        except Exception as argh:
            return argh

    return [protseq, myseq]


def check_str_alphabet(string, alphabet):
    """ Determine if a string only has characters from specified
        alphabet.

        Parameters
        ----------
        string: str
            input string.
        alphabet: str
            string that has all characters from desired
            alphabet.

        Returns
        -------
        bool
            "True" if sequence only has characters from specified
            alphabet
        str
            "ambiguous or invalid characters" if
            it any of its characters is not in the alphabet.
    """

    valid_chars = alphabet
    if all(n in valid_chars for n in string) is True:
        return True
    else:
        return 'ambiguous or invalid characters'


def check_str_multiple(string, number):
    """ Determine if length of input string is multiple of
        a specified number.

        Parameters
        ----------
        string: str
            input string.
        number: int
            integer that will be used to check if sequence
            length is multiple of.

        Returns
        -------
        bool
            "True" if the length of the sequence is a multiple of the
            specified number
        str
            "sequence length is not a multiple of number"
            if condition is not satisfied.
    """

    if len(string) % number == 0:
        return True
    else:
        return 'sequence length is not a multiple of {0}'.format(number)


def translate_dna(dna_sequence, table_id, min_len):
    """ Checks if sequence is valid and attempts to translate it,
        calling several functions to ensure that the sequence only has
        'ACTG', is multiple of 3 and that it can be translated in any of 4
        different orientations. Stores exceptions so that it is possible to
        understand the sequence could not be translated.

        Parameters
        ----------
            dna_sequence: str
            table_id: str

        Returns
        -------
        list
            If the sequence can be translated,
            a list with following elements:
                sequence (list): a list with two elemets, the protein sequence
                and the DNA sequence in the correct orientation.
                coding_strand (str): the strand orientation that had could be
                translated.
        str
            Otherwise:
                exception_str (str): a string containing the exceptions that
                determined that the sequence could not be translated.
    """

    original_seq = dna_sequence.upper()
    exception_collector = []
    strands = ['sense', 'antisense', 'revsense', 'revantisense']
    translating_methods = ['original', 'revcomp', 'rev', 'revrevcomp']

    # check if the string is DNA, without ambiguous bases
    valid_dna = check_str_alphabet(original_seq, 'ACTG')
    if valid_dna is not True:
        return valid_dna

    # check if sequence is multiple of three
    valid_length = check_str_multiple(original_seq, 3)
    if valid_length is not True:
        return valid_length

    # check if sequence is not shorter than the accepted minimum length
    if len(original_seq) < min_len:
        return 'sequence shorter than {0} nucleotides'.format(min_len)

    # try to translate in 4 different orientations
    # or reach the conclusion that the sequence cannot be translated
    i = 0
    translated = False
    while translated is False:
        sequence, exception_collector = retranslate(original_seq,
                                                    translating_methods[i],
                                                    table_id, strands[i],
                                                    exception_collector)

        i += 1
        if i == len(strands) or isinstance(sequence, list) is True:
            translated = True

    coding_strand = strands[i-1]

    # if the sequence could be translated, return list with protein and DNA
    # sequence in correct orientation
    if isinstance(sequence, list):
        return [sequence, coding_strand]
    # if it could not be translated, return the string with all exception
    # that were collected
    else:
        exception_str = ','.join(exception_collector)
        return exception_str


def retranslate(sequence, method, table_id, strands, exception_collector):
    """ Sends sequence for translation and collects exceptions when
        the sequence cannot be translated.

        Parameters
        ----------
        sequence: str
            string representing a DNA sequence.
        method: str
            a string specifying the sequence orientation
            that should be used to attempt translation.
        table_id: int
            translation table identifier.
        strands: list
            list with 4 different orientations that can
            be checked.
        exception_collector: list
            list used to store all exceptions
            arising from translation attempts.

        Returns
        -------
        list
            A list with following elements, if the sequence can be translated:
                translated_seq (list): a list with the protein sequence and
                with the DNA sequence in the orientation used for translation.
                exception_collector (list): a list with the exceptions that are
                captured when the sequence could not be translated.
            Otherwise:
                translated_seq (str): a string with the exception/reason why
                the sequence could not be translated.
                exception_collector (list): list with all exception that have
                been captured during translation attempts of the current
                sequence.
    """

    translated_seq = translate_dna_aux(sequence, method, table_id)
    if not isinstance(translated_seq, list):
        exception_collector.append('{0}({1})'.format(strands,
                                                     translated_seq.args[0]))

    return [translated_seq, exception_collector]


def is_url(url):
    """ Checks if a url is valid.

        Parameters
        ----------
        url: str
            the url to be checked

        Returns
        -------
        bool
            True if url is valid, False otherwise.

    """

    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc, result.path])
    except:
        return False


def make_url(base_url, *res, **params):
    """ Creates a url.

        Parameters
        ----------
        base_url: str
            the base url.
        res: str
            endpoint(s) to add to the base url.
        params: str
            addtional parameters.

        Returns
        -------
        url: str
            url with the provided parameters.

        str
            "An invalid URL was provided." is
            returned if a an invalid url is
            provided.

    """

    url = base_url

    # Check if the url is valid
    if is_url(url):

        if url[-1] == "/":
            url = url[:-1]

        # Add the endpoints
        for r in res:
            url = f'{url}/{r}'

        # Add params if they are provided
        if params:
            url = f'{url}?{urlencode(params)}'

        return url

    else:
        return "An invalid URL was provided."


def progress_bar(process, total, tickval, ticknum, completed):
    """ A progress bar to track process execution.

        Parameters
        ----------
        process: process object
        total: int
        tickval: int
        ticknum: int
        completed: bool

        Returns
        -------
        completed: bool
            True if process is completed,
            False otherwise.
    """

    # check if process has finished
    if (process.ready()):
        # print full progress bar and satisfy stopping condition
        progress_bar = '[{0}] 100%'.format('='*ticknum)
        completed = True

    # check how many inputs have been processed
    remaining = process._number_left
    if remaining == total:
        # print empty progress bar
        progress_bar = '[{0}] 0%'.format(' '*ticknum)
    else:
        # print progress bar, incremented by 5%
        progress = int(100-(remaining/total)*100)
        progress_tick = progress//tickval
        progress_bar = '[{0}{1}] {2}%'.format('='*progress_tick,
                                              ' '*(ticknum-progress_tick),
                                              progress)

    print('\r', progress_bar, end='')
    time.sleep(0.5)

    return completed


def get_data(server, sparql_query):
    """ Gets data from Virtuoso.

        Parameters
        ----------
        server: str
            URL of the SPARQL server.
        sparql_query: str
            SPARQL query to perform.

        Returns
        -------
        result: str
            JSON response from the server.

    """

    tries = 0
    max_tries = 5
    success = False
    while success is False and tries < max_tries:
        try:
            server.setQuery(sparql_query)
            server.setReturnFormat(JSON)
            server.setTimeout(1000)
            result = server.query().convert()
            success = True
        except Exception as e:
            tries += 1
            result = e
            time.sleep(2)

    return result


def get_read_run_info_ena(ena_id):
    """ Gets information from ENA.

        Parameters
        ----------
        ena_id: str
            ID of the ENA record

        Returns
        -------
        read_run_info: bool

    """

    url = 'http://www.ebi.ac.uk/ena/data/warehouse/filereport?accession=' + \
        ena_id + 'AAA&result=read_run'

    read_run_info = False
    try:
        with urllib.request.urlopen(url) as url:
            read_run_info = url.read().splitlines()
            if len(read_run_info) <= 1:
                read_run_info = False
            else:
                read_run_info = True
    except Exception as error:
        print(error)

    return read_run_info


def get_read_run_info_sra(SRA_id):
    """ Gets information from SRA.

    Parameters
    ----------
    SRA_id: str
        ID of the SRA record

    Returns
    -------
    read_run_info: bool

    """

    url = 'https://trace.ncbi.nlm.nih.gov/Traces/sra/sra.cgi?save=efetch&db=sra&rettype=runinfo&term=%20'+SRA_id

    read_run_info = False
    try:
        with urllib.request.urlopen(url, timeout=2) as url:

            # if the SRA_id is not found ncbi is very generous and may give a tsunami of info, limit that to 30k bytes if that's the case
            # we wont consider that ID
            read_run_info = url.read(30000)
            try:
                read_run_info = read_run_info.splitlines()
            except:
                return read_run_info

            # check if the ERR is on the second element of the list returned
            # thanks NCBI for returning wtv if the SRA_id is "LALA" or whatever I put there
            # very cranky bypass of this, change in the future

            if SRA_id in read_run_info[1].decode("utf-8"):
                read_run_info = True
            else:
                read_run_info = False

    except Exception as error:
        print(error)

    return read_run_info


# dirty way to check the disease URI is real, no pun intended :)))
def check_disease_resource(URI):
    """ Check disease URI with disease ontology.

        Parameters
        ----------
        URI: str

        Returns
        -------
        diseaseFound: bool
    """
    try:

        print('http://www.ontobee.org/ontology/rdf/DOID?iri='+URI)
        r = requests.get(
            'http://www.ontobee.org/ontology/rdf/DOID?iri='+URI)
        print(r.status_code)
        diseaseFound = False
        if int(r.status_code) < 202:
            diseaseFound = True
    except Exception as e:
        print(e)
        diseaseFound = False
    return diseaseFound


def sanitize_input(mystring):
    """ Clean a string.

        Parameters
        ----------
        mystring: str

        Returns
        -------
        mystring: str
            Clean string.
    """

    print("sanitizing")

    mystring = mystring.replace("'", "")

    mystring = mystring.encode('ascii', 'ignore')
    mystring = mystring.decode("utf-8")

    mystring = mystring.replace("\\", "")

    return mystring


def send_data(sparql_query, url_send_local_virtuoso, virtuoso_user, virtuoso_pass):
    """ Sends data to Virtuoso.

        Parameters
        ----------
        sparql_query: str
            SPARQL query to perform.
        url_send_local_virtuoso: str
            URL of the SPARQL server.
        virtuoso_user: str
            Virtuoso username.
        virtuoso_pass: str
            Virtuoso password.

        Returns
        -------
        r: str
            Request response
    """

    tries = 0
    max_tries = 3
    success = False
    while success is False and tries < max_tries:
        url = url_send_local_virtuoso
        headers = {'content-type': 'application/sparql-query'}
        r = requests.post(url, data=sparql_query, headers=headers,
                          auth=requests.auth.HTTPBasicAuth(virtuoso_user, virtuoso_pass))

        if r.status_code > 201:
            tries += 1
        else:
            success = True

    return r


def send_big_query(server, sparql_query):
    """ Sends a big query to Virtuoso
    """
    try:
        server.setQuery(sparql_query)
        server.setReturnFormat(JSON)
        server.method = "POST"
        result = server.query().convert()

    except Exception as e:
        result = e

    return result


def check_len(arg):
    """ Check string length.

        Parameters
        ----------
        arg: str

        Returns
        -------
        bool
    """

    # if there is no arg, abort
    if len(arg) == 0 or len(arg) > 30000:
        return False
    else:
        return True


def check_prefix(prefix):
    """ Check prefix.

        Parameters
        ----------
        arg: str

        Returns
        -------
        bool
    """

    # if there is no arg, abort
    if prefix == None:
        return False
    elif len(prefix) < 4 or len(prefix) > 16:
        return False
    elif prefix == 'string':
        return False
    elif ' ' in prefix:
        return False
    else:
        return True


def uniprot_query(sequence):
    """ Constructs a SPARQL query to search for exact matches in the
        UniProt endpoint.

        Parameters
        ---------
        sequence: str
            the protein sequence that will be added
            to the query.

        Returns
        -------
        query: str
            the SPARQL query that will allow to search for
            exact matches in the UniProt database.
    """

    query = ('PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>  '
             'PREFIX up: <http://purl.uniprot.org/core/> '
             'select ?seq ?fname ?sname2 ?label  where {'
             '{?b a up:Simple_Sequence; rdf:value '
             '"'+sequence+'". ?seq up:sequence ?b. '
             'OPTIONAL{?seq up:submittedName ?sname. ?sname up:fullName ?sname2} '
             'OPTIONAL{?seq up:recommendedName ?rname.?rname up:fullName ?fname} }'
             'UNION{?seq a up:Sequence; rdf:value "'+sequence+'"; '
             'rdfs:label ?label. }}')

    return query


# change this function to make it more simple and clear!
def select_name(result):
    """ Extracts the annotation description from the result
        of a query to the UniProt SPARQL endpoint.

        Parameters
        ----------
        result: dict
            results from querying the UniProt SPARQL endpoint.

        Returns
        -------
        list
            A list with the following elements:
                - the annotation descrition;
                - the URI to the UniProt page for the protein;
                - a label that has descriptive value.
    """

    name = ''
    url = ''
    label = ''

    aux = result['results']['bindings']
    i = 1
    found = False
    total_res = len(aux)
    # only check results that are not empty
    if total_res > 0:
        while found is False:
            current_res = aux[i]
            res_keys = aux[i].keys()

            if 'fname' in res_keys:
                name = str(current_res['fname']['value'])
                found = True
            elif 'sname2' in res_keys:
                name = str(current_res['sname2']['value'])
                found = True
            elif 'label' in res_keys:
                name = str(current_res['label']['value'])
                found = True

            if 'label' in res_keys:
                label = str(current_res['label']['value'])
            else:
                label = name

            if 'uri' in res_keys:
                url = str(current_res['seq']['value'])
            elif 'seq' in res_keys:
                url = str(current_res['seq']['value'])

            if i == total_res:
                found = True

    return [name, url, label]
