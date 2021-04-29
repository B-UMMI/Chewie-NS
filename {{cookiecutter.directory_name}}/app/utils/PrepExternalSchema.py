#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Purpose
-------
This module enables the adaptation of external schemas so that the loci and
alleles present in those schemas can be used with chewBBACA. During the
process, alleles that do not correspond to a complete CDS or that cannot be
translated are discarded from the final schema. One or more alleles of each
gene/locus will be chosen as representatives and included in the 'short'
directory.

Code documentation
------------------
"""

import os
import sys
import time
import shutil
import logging
import argparse
import traceback
import itertools
import multiprocessing

from Bio import SeqIO
from Bio.Seq import Seq
from Bio.Alphabet import generic_dna

from app.utils import auxiliary_functions as aux


def bsr_categorizer(blast_results, representatives,
                    representatives_scores, min_bsr, max_bsr):
    """ Determines the BLAST hits that have a BSR below a minimum threshold
        and the BLAST hits that have a BSR above a maximum threshold.

        Parameters
        ----------
        blast_results: list
            a list with sublists, each sublist contains
            information about a BLAST hit.
        representatives: list
            list with sequence identifiers of
            representative sequences.
        representatives_scores: dict
            dictionary with self BLAST raw score
            for every representative.
        min_bsr: float
            minimum BSR value accepted to consider a sequence
            as a possible new representative.
        max_bsr: float
            maximum BSR value accepted to consider a sequence
            as a possible new representative.

        Returns
        -------
        list
            List with following elements:
                high_bsr (list): list with all sequence identifiers of subject
                sequences that had hits with a BSR higher than the maximum
                defined threshold.
                low_bsr (list): list with all sequence identifiers of subject
                sequences that had hits with a BSR lower than the minimum
                defined threshold.
    """

    high_bsr = []
    hotspot_bsr = []
    low_bsr = []

    high_reps = {}
    hot_reps = {}
    low_reps = {}

    filtered_results = [res for res in blast_results
                        if res[0] != res[1] and res[1] not in representatives]
    bsr_values = [float(res[2])/float(representatives_scores[res[0]])
                  for res in filtered_results]

    high_bsr = [res[1] for ind, res in enumerate(filtered_results)
                if bsr_values[ind] >= max_bsr]
    low_bsr = [res[1] for ind, res in enumerate(filtered_results)
               if bsr_values[ind] < min_bsr]
    hotspot_bsr = [res[1] for ind, res in enumerate(filtered_results)
                   if bsr_values[ind] >= min_bsr and bsr_values[ind] < max_bsr]

    for ind, res in enumerate(filtered_results):
        if bsr_values[ind] >= min_bsr:
            high_reps.setdefault(res[0], []).append(res[1])
        if bsr_values[ind] < min_bsr:
            low_reps.setdefault(res[0], []).append(res[1])
        if bsr_values[ind] >= min_bsr and bsr_values[ind] < max_bsr:
            hot_reps.setdefault(res[0], []).append(res[1])

    # determine representatives that only led to low BSR
    low_reps = list(set(low_reps) - set(high_reps))

    return [high_bsr, low_bsr, hotspot_bsr, high_reps, low_reps, hot_reps]


def select_candidate(candidates, proteins, seqids,
                     representatives, final_representatives):
    """ Chooses a new representative sequence.

        Parameters
        ----------
        candidates: list
            list with the sequence identifiers
            of all candidates.
        proteins: dict
            a dictionary with protein identifiers
            as keys and protein sequences as values.
        seqids: list
            a list with the sequence identifiers that
            still have no representative (representatives identifiers
            are included because they have to be BLASTed in order to
            determine their self score).
        representatives: list
            the sequence identifiers of all
            representatives.

        Returns
        -------
        representatives: list
            the set of all representatives,
            including the new repsentative that was chosen by the function.
    """

    # with more than one sequence as candidate, select longest
    if len(candidates) > 1:

        # determine length of all candidates
        candidates_len = [(seqid, len(proteins[seqid]))
                          for seqid in candidates]

        # order representative candidates by length descending order
        candidates_len = sorted(candidates_len, key=lambda x: x[1],
                                reverse=True)

        # longest allele is the new representative
        representatives.append(candidates_len[0][0])
        final_representatives.append(candidates_len[0][0])

    # if tere is only one candidate, keep that
    elif len(candidates) == 1:

        representatives.append(candidates[0])
        final_representatives.append(candidates[0])

    # if no hit qualifies and there are still sequences
    # without representative
    elif len(candidates) == 0 and \
            len(seqids) > len(representatives):

        # determine length of remaining sequences
        # (representatives not included)
        candidates_len = [(seqid, len(proteins[seqid]))
                          for seqid in seqids
                          if seqid not in representatives]

        # sort by descending length
        candidates_len = sorted(candidates_len, key=lambda x: x[1],
                                reverse=True)

        # longest of remaining sequences is new representative
        representatives.append(candidates_len[0][0])
        final_representatives.append(candidates_len[0][0])

    return [representatives, final_representatives]


def adapt_loci(genes_list):
    """ Adapts a set of genes/loci from as external schema to be
        used with chewBBACA. Removes invalid alleles and selects
        representative alleles to include in the "short" directory.

        Parameters
        ----------
        genes_list: list
            a list with the paths for the files
            to be processed, the path to the schema directory, the path
            to the "short" directory and the BLAST Score Ratio value.

        Returns
        -------
        invalid_alleles: list
            list with the identifiers of the alleles
            that were determined to be invalid.
        invalid_genes: list
            list with the identifiers of the genes
            that had no valid alleles.
            After determining representatives for a gene/locus, writes the
            schema files.
    """

    # divide input list into variables
    summary_stats = []
    invalid_genes = []
    invalid_alleles = []
    genes = genes_list[:-6]
    schema_path = genes_list[-6]
    schema_short_path = genes_list[-5]
    bsr = genes_list[-4]
    min_len = genes_list[-3]
    table_id = genes_list[-2]
    size_threshold = genes_list[-1]
    for gene in genes:

        representatives = []
        final_representatives = []

        # get gene basename and identifier
        gene_basename = os.path.basename(gene)
        gene_id = gene_basename.split('.f')[0]

        # create paths to gene files in new schema
        gene_file = aux.join_paths(schema_path,
                                   '{0}{1}'.format(gene_id, '.fasta'))

        gene_short_file = aux.join_paths(schema_short_path,
                                         '{0}{1}'.format(gene_id, '_short.fasta'))

        # create path to temp working directory for current gene
        gene_temp_dir = aux.join_paths(schema_path,
                                       '{0}{1}'.format(gene_id, '_temp'))

        # create temp directory for the current gene
        aux.create_directory(gene_temp_dir)

        # dictionaries mapping gene identifiers to DNA sequences
        # and Protein sequences
        gene_seqs, prot_seqs, gene_invalid, seqids_map, total_sequences = \
            aux.get_seqs_dicts(gene, gene_id, table_id,
                               min_len, size_threshold)
        invalid_alleles.extend(gene_invalid)

        # if locus has no valid CDS sequences,
        # continue to next locus
        if len(prot_seqs) == 0:
            shutil.rmtree(gene_temp_dir)
            invalid_genes.append(gene_id)
            summary_stats.append([gene_id, str(total_sequences), '0', '0'])
            continue

        if len(gene_seqs) > 1:
            # identify DNA sequences that code for same protein
            equal_prots = aux.determine_duplicated_prots(prot_seqs)

            # get only one identifier per protein
            ids_to_blast = [protids[0]
                            for protein, protids in equal_prots.items()]

            # get longest sequence as first representative
            longest = aux.determine_longest(ids_to_blast, prot_seqs)
            representatives.append(longest)
            final_representatives.append(longest)

            # create FASTA file with distinct protein sequences
            protein_file = aux.join_paths(gene_temp_dir,
                                          '{0}_protein.fasta'.format(gene_id))
            protein_lines = aux.fasta_lines(ids_to_blast, prot_seqs)
            aux.write_list(protein_lines, protein_file)

            # create blastdb with all distinct proteins
            blastp_db = os.path.join(gene_temp_dir, gene_id)
            aux.make_blast_db(protein_file, blastp_db, 'prot')

            # determine appropriate blastp task (proteins < 30aa need blastp-short)
            blastp_task = aux.determine_blast_task(equal_prots)

            # cycles to BLAST representatives against non-representatives until
            # all non-representatives have a representative
            while len(set(ids_to_blast) - set(representatives)) != 0:

                # create FASTA file with representative sequences
                rep_file = aux.join_paths(gene_temp_dir,
                                          '{0}_rep_protein.fasta'.format(gene_id))
                rep_protein_lines = aux.fasta_lines(representatives, prot_seqs)
                aux.write_list(rep_protein_lines, rep_file)

                # create file with seqids to BLAST against
                ids_str = aux.concatenate_list(
                    [str(i) for i in ids_to_blast], '\n')
                ids_file = aux.join_paths(gene_temp_dir,
                                          '{0}_ids.txt'.format(gene_id))
                aux.write_text_chunk(ids_file, ids_str)

                # BLAST representatives against non-represented
                blast_output = aux.join_paths(gene_temp_dir,
                                              '{0}_blast_out.tsv'.format(gene_id))
                # set max_target_seqs to huge number because BLAST only
                # returns 500 hits by default
                blast_command = ('blastp -task {0} -db {1} -query {2} -out {3} '
                                 '-outfmt "6 qseqid sseqid score" -max_hsps 1 '
                                 '-num_threads {4} -max_target_seqs 100000 '
                                 '-seqidlist {5} 2>/dev/null'.format(blastp_task, blastp_db,
                                                                     rep_file, blast_output,
                                                                     1, ids_file))
                os.system(blast_command)

                # import BLAST results
                blast_results = aux.read_blast_tabular(blast_output)

                # get self-score for representatives
                rep_self_scores = {res[1]: res[2] for res in blast_results
                                   if res[0] == res[1]}

                # divide results into high, low and hot BSR values
                hitting_high, hitting_low, hotspots, high_reps, low_reps, hot_reps = \
                    bsr_categorizer(blast_results, representatives,
                                    rep_self_scores, bsr, bsr+0.1)

                excluded_reps = []

                # remove high BSR hits that have representative
                hitting_high = set(hitting_high)
                ids_to_blast = [
                    i for i in ids_to_blast if i not in hitting_high]

                # remove representatives that led to high BSR with subjects that were removed
                prunned_high_reps = {
                    k: [r for r in v if r in ids_to_blast] for k, v in high_reps.items()}
                reps_to_remove = [
                    k for k, v in prunned_high_reps.items() if len(v) == 0]

                excluded_reps.extend(reps_to_remove)

                # determine smallest set of representatives that allow to get all cycle candidates
                excluded = []
                hotspot_reps = set(aux.flatten_list(list(hot_reps.values())))
                for rep, hits in hot_reps.items():
                    common = hotspot_reps.intersection(set(hits))
                    if len(common) > 0:
                        hotspot_reps = hotspot_reps - common
                    else:
                        excluded.append(rep)

                excluded_reps.extend(excluded)

                # remove representatives that only led to low BSR
                excluded_reps.extend(low_reps)

                representatives = [
                    rep for rep in representatives if rep not in excluded_reps]
                ids_to_blast = [
                    i for i in ids_to_blast if i not in excluded_reps]

                # determine next representative from candidates
                rep_candidates = list(set(hotspots) - hitting_high)
                # sort to guarantee reproducible results with same datasets
                rep_candidates = sorted(rep_candidates, key=lambda x: int(x))
                representatives, final_representatives = select_candidate(rep_candidates,
                                                                          prot_seqs,
                                                                          ids_to_blast,
                                                                          representatives,
                                                                          final_representatives)

                # remove files created for current gene iteration
                os.remove(rep_file)
                os.remove(blast_output)
                os.remove(ids_file)

        else:
            final_representatives = list(prot_seqs.keys())

        # write schema file with all alleles
        gene_lines = aux.fasta_lines(list(gene_seqs.keys()), gene_seqs)
        aux.write_list(gene_lines, gene_file)

        # get total number of valid sequences
        valid_sequences = len(gene_lines)

        # write schema file with representatives
        final_representatives = [seqids_map[rep]
                                 for rep in final_representatives]
        gene_rep_lines = aux.fasta_lines(final_representatives, gene_seqs)
        aux.write_list(gene_rep_lines, gene_short_file)

        # get number of representatives
        representatives_number = len(gene_rep_lines)

        summary_stats.append([gene_id,
                              str(total_sequences),
                              str(valid_sequences),
                              str(representatives_number)])

        shutil.rmtree(gene_temp_dir)

    return [invalid_alleles, invalid_genes, summary_stats]


def main(external_schema, output_schema, core_count, bsr, min_len, trans_tbl, ptf_path, size_threshold, logfile):

    logging.basicConfig(filename=logfile, level=logging.INFO)

    start = time.time()

    logging.info('Prodigal training file: {0}'.format(ptf_path))
    logging.info('Number of cores: {0}'.format(core_count))
    logging.info('BLAST Score Ratio: {0}'.format(bsr))
    logging.info('Translation table: {0}'.format(trans_tbl))
    logging.info('Minimum accepted sequence length: {0}'.format(min_len))
    logging.info('Size threshold: {0}'.format(size_threshold))

    # define output paths
    schema_path = os.path.abspath(output_schema)
    schema_short_path = aux.join_paths(schema_path, 'short')

    # create output directories
    # check if they exist first
    aux.create_directory(schema_path)
    aux.create_directory(schema_short_path)

    # list schema gene files
    genes_file = aux.check_input_type(external_schema,
                                      os.path.join(output_schema, 'schema_genes.txt'))

    # import list of schema files
    with open(genes_file, 'r') as gf:
        genes_list = [line.rstrip('\n') for line in gf]
    os.remove(genes_file)

    logging.info('Number of genes to adapt: {0}'.format(len(genes_list)))

    logging.info('Determining the total number of alleles and '
                 'allele mean length per gene...'.format())

    # count number of sequences and mean length per gene
    genes_info = []
    genes_pools = multiprocessing.Pool(processes=core_count)
    gp = genes_pools.map_async(aux.gene_seqs_info, genes_list,
                               callback=genes_info.extend)
    gp.wait()

    # split files according to number of sequences and sequence mean length
    # in each file to pass even groups of sequences to all cores
    even_genes_groups = aux.split_genes_by_core(genes_info, core_count*4,
                                                'seqcount')
    # with few inputs, some sublists might be empty
    even_genes_groups = [i for i in even_genes_groups if len(i) > 0]

    # append output paths and bsr value to each input
    for i in range(len(even_genes_groups)):
        even_genes_groups[i].append(schema_path)
        even_genes_groups[i].append(schema_short_path)
        even_genes_groups[i].append(bsr)
        even_genes_groups[i].append(min_len)
        even_genes_groups[i].append(trans_tbl)
        even_genes_groups[i].append(size_threshold)

    logging.info('Adapting {0} genes...'.format(len(genes_list)))

    invalid_data = []
    # process inputs in parallel
    genes_pools = multiprocessing.Pool(processes=core_count)

    rawr = genes_pools.map_async(adapt_loci, even_genes_groups,
                                 callback=invalid_data.extend)

    rawr.wait()

    # handle exceptions
    try:
        # try to get returned results
        # will re-raise exceptions raised during multiprocessing
        a = rawr.get()
    except Exception as e:
        # get exception info
        exc_type, exc_value, exc_traceback = sys.exc_info()
        logging.info('The process encountered some problem and could '
                     'not complete successfully. Raised exceptions:\n')
        # get traceback as list of lines
        traceback_lines = traceback.format_exception(
            exc_type, exc_value, exc_traceback)
        # keep first exception traceback and exclude traceback from rawr.get()
        exc_index = traceback_lines.index(
            'The above exception was the direct cause of the following exception:\n\n')
        traceback_lines[0] = traceback_lines[0].split(
            'multiprocessing.pool.RemoteTraceback: \n"""')[1]
        traceback_lines[exc_index-1] = traceback_lines[exc_index-1].rstrip('"""\n')
        logging.info(''.join(traceback_lines[0:exc_index]))
        return False

    # log alleles that were determined to be invalid
    invalid_alleles = [sub[0] for sub in invalid_data]
    invalid_alleles = list(itertools.chain.from_iterable(invalid_alleles))
    invalid_alleles = [','.join(a) for a in invalid_alleles]
    if len(invalid_alleles) > 0:
        logging.warning('Invalid alleles: {0}'.format(
            ';'.join(invalid_alleles)))

    # log identifiers of genes that had no valid alleles
    invalid_genes = [sub[1] for sub in invalid_data]
    invalid_genes = list(itertools.chain.from_iterable(invalid_genes))
    invalid_genes = [','.join(a) for a in invalid_genes]
    if len(invalid_genes) > 0:
        logging.warning('Invalid_genes: {0}'.format(';'.join(invalid_genes)))

    logging.info('Number of invalid genes: {0}'.format(len(invalid_genes)))
    logging.info('Number of invalid alleles: {0}'.format(len(invalid_alleles)))

    logging.info('Successfully adapted {0}/{1} genes present in the '
                 'schema.'.format(len(genes_list)-len(invalid_genes),
                                  len(genes_list)))

    end = time.time()
    delta = end - start
    minutes = int(delta // 60)
    seconds = int(delta % 60)
    logging.info('Adapted in {0}m{1}s.'.format(minutes, seconds))

    return True


def parse_arguments():

    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument('-i', type=str, required=True, dest='input_files',
                        help='Path to the folder containing the fasta files, '
                             'one fasta file per gene/locus (alternatively, '
                             'a file with a list of paths can be given).')

    parser.add_argument('-o', type=str, required=True, dest='output_directory',
                        help='The directory where the output files will be '
                        'saved (will create the directory if it does not '
                        'exist).')

    parser.add_argument('-ptf', type=str, required=True,
                        dest='ptf_path',
                        help='Path to the Prodigal training file. '
                             'Default is to get training file in '
                             'schema directory.')

    parser.add_argument('--cpu', type=int, required=False, default=1,
                        dest='cpu_cores',
                        help='The number of CPU cores to use (default=1).')

    parser.add_argument('--bsr', type=float, required=False, default=0.6,
                        dest='blast_score_ratio',
                        help='The BLAST Score Ratio value that will be '
                        'used to adapt the external schema (default=0.6).')

    parser.add_argument('--l', type=int, required=False, default=0,
                        dest='minimum_length',
                        help='Minimum sequence length accepted. Sequences with'
                        ' a length value smaller than the value passed to this'
                        ' argument will be discarded (default=0).')

    parser.add_argument('--t', type=int, required=False, default=11,
                        dest='translation_table',
                        help='Genetic code to use for CDS translation.'
                        ' (default=11, for Bacteria and Archaea)')

    parser.add_argument('--st', type=float, required=False,
                        default=None, dest='size_threshold',
                        help='CDS size variation threshold. At the default '
                             'value no alleles will be discarded due to size '
                             'variation.')

    parser.add_argument('--log', type=str, required=False,
                        default=None, dest='logfile',
                        help='Logfile of the execution.')

    args = parser.parse_args()

    return [args.input_files, args.output_directory,
            args.cpu_cores, args.blast_score_ratio,
            args.minimum_length, args.translation_table,
            args.ptf_path, args.size_threshold,
            args.logfile]


if __name__ == '__main__':

    args = parse_arguments()
    main(args[0], args[1], args[2], args[3],
         args[4], args[5], args[6], args[7],
         args[8])
