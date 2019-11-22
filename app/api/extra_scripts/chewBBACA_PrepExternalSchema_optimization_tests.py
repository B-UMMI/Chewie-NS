#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AUTHOR

    Rafael Mamede
    github: @rfm-targa

DESCRIPTION

    This script enables the adaptation of external schemas so that
    the loci and alleles present in those schemas can be used with
    chewBBACA if they pass certain criteria necessary to be considered
    valid and used with chewBBACA processes.


"""

import os
import csv
import time
import shutil
import argparse
import itertools
import multiprocessing

from Bio import SeqIO
from Bio.Seq import Seq
from Bio.Alphabet import generic_dna


def read_blast_tabular(blast_tabular_file):
    """ Read a file with BLAST results in tabular format

        Args:
            blast_tabular_file (str): path to output file of BLAST.

        Returns:
            blasting_results (list): a list with a sublist per line
            in the input file.
    """

    with open(blast_tabular_file, 'r') as blastout:
        blasting_results = []
        reader = csv.reader(blastout, delimiter='\t')
        for row in reader:
            blasting_results.append(row)

    return blasting_results


def fasta_lines(identifiers, sequences_dictionary):
    """ Creates list with line elements for a FASTA file based on the sequence
        identifiers passed.

        Args:
            identifiers (list): a list with the identifiers of sequences that
            will be included in the list.
            sequences_dictionary (dict): a dictionary with sequence identifeirs
            as keys and sequences as values.

        Returns:
            seqs_lines (list): a list with strings representing the header of
            the sequence and the sequence for each of the specified sequence
            identifiers.
    """

    seqs_lines = []
    for seqid in identifiers:
        # create sequence header typical of FASTA file
        header = '>{0}\n'.format(seqid)
        sequence = '{0}\n'.format(sequences_dictionary[seqid])
        # append sequence header and sequence sequentially
        seqs_lines.append(header)
        seqs_lines.append(sequence)

    return seqs_lines


def write_list(lines, output_file):
    """ Writes list elements to file.

        Args:
            lines (list): list with the ordered lines that will be written
            to the output file.
            output_file (str): name/path of the output file.

        Returns:
            Writes contents of 'lines' argument into 'output_file'.
    """

    with open(output_file, 'w') as file:
        file.writelines(lines)


def determine_duplicated_prots(proteins):
    """ Creates a dictionary with protein sequences as keys and all sequence
        identifiers associated with that protein as values.

        Args:
            proteins (dict): dictionary with protein sequence identifiers as
            keys and protein sequences as values.

        Returns:
            equal_prots (dict): dictionary with protein sequence as keys and
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
    """

    # initialize variable to store length of longest
    # sequence found during iterations
    longest = 0
    # initilalize variable to store seqid of longest
    chosen = None
    for seqid in seqids:
        seq_len = len(proteins[seqid])
        # only switch sequence if it is longer
        if seq_len > longest:
            longest = seq_len
            chosen = seqid

    return chosen


def get_seqs_dicts(gene_file, table_id):
    """ Creates a dictionary mapping seqids to DNA sequences and
        another dictionary mapping protids to protein sequences.

        Args:
            gene_file (str): path/name of the FASTA file with
            DNA sequences.
            table_id (int): translation table identifier.

        Returns:
            List with following elements:
                dna_seqs (dict): dictionary with sequence identifiers as keys
                and DNA sequences as values.
                prot_seqs (dict): dictionary with protein identifiers as keys
                and Protein sequences as values.
                invalid_alleles (list): list with sequence identifiers of
                alleles that are not valid because they could not be
                translated.
    """

    dna_seqs = {}
    prot_seqs = {}
    invalid_alleles = []
    for allele in SeqIO.parse(gene_file, 'fasta', generic_dna):
        # try to translate each sequence in the file
        translated_seq = translate_dna(str(allele.seq), table_id)
        # if returned value is a list, translation was successful
        if isinstance(translated_seq, list):
            dna_seqs[allele.id] = translated_seq[0][1]
            prot_seqs[allele.id] = str(translated_seq[0][0])
        # if returned value is a string, translation failed and
        # string contains exceptions
        elif isinstance(translated_seq, str):
            invalid_alleles.append([allele.id, translated_seq])

    return [dna_seqs, prot_seqs, invalid_alleles]


def reverse_complement(dna_sequence):
    """ Determines the reverse complement of given DNA strand.

        Args:
            strDNA (str): string representing a DNA sequence.

        Returns:
            revC_dna (str): the reverse complement of the DNA sequence, without
            lowercase letters.

        Example:
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

        Args:
            string (str): string to be reversed.

        Returns:
            revstr (str): reverse of input string.
    """

    revstr = string[::-1]

    return revstr


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


def translate_dna_aux(dna_sequence, method, table_id):
    """ Tries to translate an input DNA sequence in specified orientation
        and stores exceptions when the input sequence cannot be translated.

        Args:
            dna_sequence (str): string representing a DNA sequence.
            method (str): a string specifying the way the sequence will
            be oriented to attempt translation.
            table_id (int): translation table identifier.

        Returns:
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

        Args:
            string (str): input string.
            alphabet (str): string that has all characters from desired
            alphabet.

        Returns:
            "True" if sequence only has characters from specified
            alphabet and string "ambiguous or invalid characters" if
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

        Args:
            string (str): input string.
            number (int): integer that will be used to check if sequence
            length is multiple of.

        Returns:
            "True" if the length of the sequence is a multiple of the
            specified number and "sequence length is not a multiple of number"
            if condition is not satisfied.
    """

    if len(string) % number == 0:
        return True
    else:
        return 'sequence length is not a multiple of {0}'.format(number)


def translate_dna(dna_sequence, table_id):
    """ Checks if sequence is valid and attempts to translate it,
        calling several functions to ensure that the sequence only has
        'ACTG', is multiple of 3 and that it can be translated in any of 4
        different orientations. Stores exceptions so that it is possible to
        understand the sequence could not be translated.

        Args:
            dna_sequence (str):
            table_id (int):

        Returns:
            If the sequence can be translated,
            a list with following elements:
                sequence (list): a list with two elemets, the protein sequence
                and the DNA sequence in the correct orientation.
                coding_strand (str): the strand orientation that had could be
                translated.
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

        Args:
            sequence (str): string representing a DNA sequence.
            method (str): a string specifying the sequence orientation
            that should be used to attempt translation.
            table_id (int): translation table identifier.
            strands (list): list with 4 different orientations that can
            be checked.
            exception_collector (list): list used to store all exceptions
            arising from translation attempts.

        Returns:
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


def split_genes_by_core(inputs, threads, method):
    """ Splits list with loci inputs into several sublists based
        on the number of sequence per locus (seqcount), the mean
        length of the sequences in each locus or the product of
        both variables.

        Args:
            inputs (list): list with information about the data of
            each locus that needs to be processed.
            threads (int): the number of sublists with inputs that
            should be created, based on the number of CPU threads
            that will be used to process the inputs.
            method (str): "seqcount" to split inputs into sublists
            with even number of sequences, "length" to split based
            on mean length of sequences and "seqcount+length" to
            split based on both criteria.

        Returns:
            splitted_ids (list): subslists with paths to loci, each
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

        Args:
            sequence_ids (list): list with strings that will be concatenated.
            join_char (str): character that will be used to join all list
            elements.

        Returns:
            ids_str (str): concatenation of all strings in the input list.
    """

    concat = join_char.join(str_list)

    return concat


def write_text_chunk(output_file, text):
    """ Write single string to file.

        Args:
            output_file (str): path/name of the file that will store
            the input text.
            text (str): single string to write to file.

        Returns:
            Writes input text to output file.
    """

    with open(output_file, 'w') as out:
        out.write(text)


def determine_high_low_bsr(blast_results, representatives, representatives_scores,
                           min_bsr, max_bsr):
    """ Determines the BLAST hits that have a BSR below a minimum threshold
        and the BLAST hits that have a BSR above a maximum threshold.

        Args:
            blast_results (list): a list with sublists, each sublist contains
            information about a BLAST hit.
            representatives (list): list with sequence identifiers of
            representative sequences.
            representatives_scores (dict): dictionary with self BLAST raw score
            for every representative.
            min_bsr (float): minimum BSR value accepted to consider a sequence
            as a possible new representative.
            max_bsr (float): maximum BSR value accepted to consider a sequence
            as a possible new representative.
        Returns:
            List with following elements:
                high_bsr (list): list with all sequence identifiers of subject
                sequences that had hits with a BSR higher than the maximum
                defined threshold.
                low_bsr (list): list with all sequence identifiers of subject
                sequences that had hits with a BSR lower than the minimum
                defined threshold.
    """

    high_bsr = []
    low_bsr = []
    hotspot_bsr = []
    for result in blast_results:
        # check if BLAST hit is not between the same sequence
        # and if the subject is not a representative
        if result[0] != result[1] and result[1] not in representatives:
            query_score = representatives_scores[result[0]]
            hit_score = result[2]
            # calculate BSR
            bsr = float(hit_score) / float(query_score)

            if bsr >= max_bsr:
                if result[1] not in high_bsr:
                    high_bsr.append(result[1])
            elif bsr < min_bsr:
                if result[1] not in low_bsr:
                    low_bsr.append(result[1])
            elif bsr >= 0.6 and bsr < 0.7:
                if result[1] not in hotspot_bsr:
                    hotspot_bsr.append(result[1])

    return [high_bsr, low_bsr, hotspot_bsr]


def is_fasta(filename):
    """ Check if file is a FASTA file.

        Args:
            filename (str): name/path for the file to be checked.

        Returns:
            True if file is a FASTA file, False otherwise.
    """

    with open(filename, 'r') as handle:
        fasta = SeqIO.parse(handle, 'fasta')

        return any(fasta)


def filter_files(files_list, suffixes):
    """ Checks if files names contain any suffix from a list of suffixes.

        Args:
            files_list (list): a list with all files names.
        Returns:
            suffixes (list): a list with all suffixes to search for in
            the files names.
    """

    accepted = [file for file in files_list
                if any([True for suffix in suffixes if suffix in file])]

    return accepted


def filter_non_fasta(files_list):
    """ Creates a new list of files names/paths that only contains FASTA files.

        Args:
            files_list (list): a list with files names/paths.
        Returns:
            real_fasta (list): a list with files names/paths that correspond
            to FASTA files.
    """

    real_fasta = [file for file in files_list if is_fasta(file) is True]

    return real_fasta


def gene_seqs_info(genes_list):
    """ Determines the total number of alleles and the mean length
        of allele sequences per gene.

        Args:
            genes_list (list): a list with names/paths for FASTA
            files.
        Returns:
            genes_info (list): a list with a sublist for each input
            gene file. Each sublist contains a gene identifier, the
            total number of alleles for that gene and the mean length
            of allele sequences for that gene.
    """

    genes_info = []
    for gene in genes_list:
        seq_generator = SeqIO.parse(gene, 'fasta', generic_dna)
        alleles_lengths = [len(allele) for allele in seq_generator]
        mean_length = sum(alleles_lengths)/len(alleles_lengths)
        total_seqs = len(alleles_lengths)
        genes_info.append([gene, total_seqs, mean_length])

    return genes_info


def adapt_external_schema(genes_list):
    """
    """

    # divide input list into variables
    genes = genes_list[:-3]
    schema_path = genes_list[-3]
    schema_short_path = genes_list[-2]
    bsr = genes_list[-1]
    invalid_alleles = []
    invalid_genes = []
    table_id = 11
    for gene in genes:

        representatives = []

        # get gene basename and identifier
        gene_basename = os.path.basename(gene)
        gene_id = gene_basename.split('.f')[0]

        # create paths to gene files in new schema
        gene_file = os.path.join(schema_path, '{0}{1}'.format(gene_id, '.fasta'))
        gene_short_file = os.path.join(schema_short_path, '{0}{1}'.format(gene_id,
                                                                          '_short.fasta'))

        # create path to temp working directory for current gene
        gene_temp_dir = os.path.join(schema_path, '{0}{1}'.format(gene_id, '_temp'))

        # create temp directory for the current gene
        if not os.path.exists(gene_temp_dir):
            os.makedirs(gene_temp_dir)

        # get dictionaries mapping gene identifiers to DNA sequences
        # and Protein sequences
        gene_seqs, prot_seqs, gene_invalid = get_seqs_dicts(gene, table_id)
        invalid_alleles.extend(gene_invalid)

        # if locus has no valid CDS sequences,
        # continue to next locus
        if len(prot_seqs) == 0:
            shutil.rmtree(gene_temp_dir)
            invalid_genes.append(gene_id)
            continue

        # create dictionary to store protein sequences and sequence
        # identifiers with the same protein sequence
        equal_prots = determine_duplicated_prots(prot_seqs)

        # get only one identifier per protein
        ids_to_blast = []
        for protein, protids in equal_prots.items():
            ids_to_blast.append(protids[0])

        # get longest sequence as first representative
        longest = determine_longest(ids_to_blast, prot_seqs)
        representatives.append(longest)

        # create FASTA file with distinct protein sequences
        # create with only one representative per protein
        protein_file = os.path.join(gene_temp_dir, '{0}_protein.fasta'.format(gene_id))
        protein_lines = fasta_lines(ids_to_blast, prot_seqs)
        write_list(protein_lines, protein_file)

        # create blastdb with all distinct proteins
        blastp_db = os.path.join(gene_temp_dir, gene_id)
        makedb_cmd = 'makeblastdb -in {0} -out {1} -parse_seqids -dbtype prot > /dev/null'.format(protein_file, blastp_db)
        os.system(makedb_cmd)
        
        # determine if sequences are shorter than 30aa and choose
        # appropriate blastp task
        blastp_task = 'blastp'
        for allele in SeqIO.parse(protein_file, 'fasta', generic_dna):
            if len(str(allele.seq)) < 30:
                blastp_task = 'blastp-short'
        
        # BLAST representative against all proteins, determine if any hit
        # can be a candidate and keep applying the same process until only
        # the representatives remain in the ids_to_blast list
        while len(ids_to_blast) > len(representatives):

            # create FASTA file with representative sequences
            rep_file = os.path.join(gene_temp_dir, '{0}_rep_protein.fasta'.format(gene_id))
            rep_protein_lines = fasta_lines(representatives, prot_seqs)
            write_list(rep_protein_lines, rep_file)

            # create file with seqids to BLAST against
            ids_str = concatenate_list(ids_to_blast, '\n')
            ids_file = os.path.join(gene_temp_dir, '{0}_ids.txt'.format(gene_id))
            write_text_chunk(ids_file, ids_str)

            # BLAST representatives against all sequences that still have no representative
            blast_output = os.path.join(gene_temp_dir, '{0}_blast_out.tsv'.format(gene_id))
            # set max_target_seqs to huge number because BLAST only returns 500 hits by default
            blast_command = ('blastp -task {0} -db {1} -query {2} -out {3} -outfmt "6 qseqid sseqid score" '
                             '-max_hsps 1 -num_threads {4} -max_target_seqs 100000 '
                             '-seqidlist {5}'.format(blastp_task, blastp_db, rep_file, blast_output, 1, ids_file))

            os.system(blast_command)

            # get path to file with BLAST results
            blastout_file = filter_files(os.listdir(gene_temp_dir), ['blast_out.tsv'])[0]
            blastout_file = os.path.join(gene_temp_dir, blastout_file)

            # import BLAST results
            blast_results = read_blast_tabular(blastout_file)

            # get self-score for representatives
            rep_self_scores = {res[1]: res[2] for res in blast_results if res[0] == res[1]}

            # find representative candidates
            hitting_high, hitting_low, hotspots = determine_high_low_bsr(blast_results, representatives,
                                                               rep_self_scores, bsr, bsr+0.1)

            # determine alleles that only had hits with low BSR
            hitting_low = list(set(hitting_low) - set(hitting_high))

            # remove seqids that had high BSR hits because
            # those alleles are already represented
            hitting_high = list(set(hitting_high))
            ids_to_blast = [seqid for seqid in ids_to_blast
                            if seqid not in hitting_high]

            # determine candidates, alleles that only had hit with BSR
            # between 0.6 and 0.7
            rep_candidates = hotspots
            # remove representatives
            rep_candidates = [seqid for seqid in rep_candidates
                              if seqid not in representatives]

            # with more than one sequence as candidate, select longest
            if len(rep_candidates) > 1:

                # determine length of all candidates
                candidates_len = [(seqid, len(prot_seqs[seqid]))
                                  for seqid in rep_candidates]

                # order representative candidates by length descending order
                candidates_len = sorted(candidates_len, key=lambda x: x[1], reverse=True)

                # keep longest and remove the rest
                ex_candidates = [t[0] for t in candidates_len[1:]]
                for seqid in ex_candidates:
                    ids_to_blast.remove(seqid)

                # longest allele is the new representative
                representatives.append(candidates_len[0][0])

            # if tere is only one candidate, keet that
            elif len(rep_candidates) == 1:

                representatives.append(rep_candidates[0])

            # if no hit qualifies and there are still sequences without representative
            elif len(rep_candidates) == 0 and len(ids_to_blast) > len(representatives):

                # determine length of remaining sequences
                # (representatives not included)
                candidates_len = [(seqid, len(prot_seqs[seqid]))
                                  for seqid in ids_to_blast
                                  if seqid not in representatives]

                # sort by descending length
                candidates_len = sorted(candidates_len, key=lambda x: x[1], reverse=True)

                # longest of remaining sequences is new representative
                representatives.append(candidates_len[0][0])

            # remove files created for current gene iteration
            os.remove(rep_file)
            os.remove(blast_output)
            os.remove(ids_file)

        # write schema file with all alleles
        gene_lines = fasta_lines(list(gene_seqs.keys()), gene_seqs)
        write_list(gene_lines, gene_file)

        # write schema file with representatives
        gene_rep_lines = fasta_lines(representatives, gene_seqs)
        write_list(gene_rep_lines, gene_short_file)

        shutil.rmtree(gene_temp_dir)

    return [invalid_alleles, invalid_genes]


def main(external_schema, output_schema, cpu_threads, bsr):

    start = time.time()

    print('\nAdapting schema in the following directory:\n{0}'.format(os.path.abspath(external_schema)))
    print('Number of threads: {0}'.format(cpu_threads))
    print('BLAST Score Ratio: {0}\n'.format(bsr))

    genes_list = []

    # list FASTA files in input directory and determine absolute path for each
    genes_list = os.listdir(external_schema)

    # filter files based on suffix
    file_suffixes = ['.fasta', '.fna', '.ffn']
    genes_list = filter_files(genes_list, file_suffixes)

    # get absolute path for every file
    for f in range(len(genes_list)):
        genes_list[f] = os.path.join(external_schema, genes_list[f])

    # filter files based on contents, must be FASTA with sequences
    genes_list = filter_non_fasta(genes_list)

    # count number of sequences and mean length per gene
    genes_info = gene_seqs_info(genes_list)

    # split files according to number of sequences and sequence mean length
    # in each file to pass even groups of sequences to all cores
    even_genes_groups = split_genes_by_core(genes_info, cpu_threads*4, 'seqcount')
    # with few inputs, some sublists might be empty
    even_genes_groups = [i for i in even_genes_groups if len(i) > 0]

    # define output paths
    schema_path = os.path.abspath(output_schema)
    schema_short_path = os.path.join(schema_path, 'short')

    # create output directories
    if not os.path.exists(schema_path):
        os.mkdir(schema_path)
        
    if not os.path.exists(schema_short_path):
        os.mkdir(schema_short_path)

    # append output paths and bsr value to each input
    for i in range(len(even_genes_groups)):
        even_genes_groups[i].append(schema_path)
        even_genes_groups[i].append(schema_short_path)
        even_genes_groups[i].append(bsr)

    invalid_data = []
    # process inputs in parallel
    genes_pools = multiprocessing.Pool(processes=cpu_threads)

    rawr = genes_pools.map_async(adapt_external_schema, even_genes_groups,
                                 callback=invalid_data.extend)

    # adapt progress bar so that it does not change size with different number of cores???
    # start and update progress bar
    tickval = (100 // (cpu_threads*4)) + 1
    ticknum = 100//tickval
    completed = False
    while completed is False:

        # check if process has finished
        if (rawr.ready()):
            # print full progress bar and satisfy stopping condition
            progress_bar = '[{0}] 100%'.format('='*ticknum)
            completed = True

        # check how many inputs have been processed
        remaining = rawr._number_left
        if remaining == len(even_genes_groups):
            # print empty progress bar
            progress_bar = '[{0}] 0%'.format(' '*ticknum)
        else:
            # print progress bar, incremented by 5%
            progress = int(100-(remaining/len(even_genes_groups))*100)
            progress_tick = progress//tickval
            progress_bar = '[{0}{1}] {2}%'.format('='*progress_tick, ' '*(ticknum-progress_tick), progress)

        print('\r', progress_bar, end='')
        time.sleep(0.5)

    rawr.wait()

    # define paths and write files with list of invalid alleles and invalid genes
    output_schema_basename = os.path.basename(output_schema)
    schema_parent_directory = os.path.dirname(schema_path)

    # write file with alleles that were determined to be invalid
    invalid_alleles = [sub[0] for sub in invalid_data]
    invalid_alleles = list(itertools.chain.from_iterable(invalid_alleles))
    invalid_alleles_file = '{0}/{1}_{2}'.format(schema_parent_directory,
                                                output_schema_basename,
                                                'invalid_alleles.txt')

    with open(invalid_alleles_file, 'w') as inv:
        lines = []
        for allele in invalid_alleles:
            seqid = allele[0]
            error = allele[1]
            line = '{0}: {1}\n'.format(seqid, error)
            lines.append(line)

        inv.writelines(lines)
        
    # write file with identifiers of genes that had no valid alleles
    invalid_genes = [sub[1] for sub in invalid_data]
    invalid_genes = list(itertools.chain.from_iterable(invalid_genes))
    invalid_genes_file = '{0}/{1}_{2}'.format(schema_parent_directory,
                                              output_schema_basename,
                                              'invalid_genes.txt')

    with open(invalid_genes_file, 'w') as inv:
        invalid_geqids = '\n'.join(invalid_genes)
        inv.write(invalid_geqids)

    print('\n\nSuccessfully adapted {0}/{1} genes present in the '
          'external schema.'.format(len(genes_list)-len(invalid_genes), len(genes_list)))

    end = time.time()
    delta = end - start
    minutes = int(delta // 60)
    seconds = int(delta % 60)
    print('Done! Took {0}m{1}s.'.format(minutes, seconds))


def parse_arguments():

    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument('-i', '--input_schema', type=str, required=True, dest='input_schema',
                        help='External schema to adapt. Must be a directory with a FASTA file'
                             'per gene to adapt.')

    parser.add_argument('-o', '--output_directory', type=str, required=True, dest='output_directory',
                        help='The directory where the output files will be saved (will create the directory if '
                             'it does not exist).')

    parser.add_argument('-t', '--threads', type=int, required=False, dest='threads',
                        default=1, help='The number of processes to start. The input data will be divided into sublists '
                                        'in order to reduce core idling and execution time (default=1).')

    parser.add_argument('-bsr', '--blast_score_ratio', type=float, required=False, dest='blast_score_ratio',
                        default=0.6, help='The BLAST Score Ratio value that will be used to adapt the external '
                                          'schema (default=0.6).')

    args = parser.parse_args()

    return [args.input_schema, args.output_directory,
            args.threads, args.blast_score_ratio]


if __name__ == '__main__':

    args = parse_arguments()
    main(args[0], args[1], args[2], args[3])
