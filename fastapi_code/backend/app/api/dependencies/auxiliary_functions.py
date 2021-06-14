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

# from flask import abort
from collections import Counter
from SPARQLWrapper import SPARQLWrapper, JSON
from urllib.parse import urlparse, urlencode, urlsplit, parse_qs

from Bio import SeqIO
from Bio.Seq import Seq

# from Bio.Alphabet import generic_dna


async def generate(header, iterable):
    """ Generates a stream response.

        Parameters
        ----------
        header: str
            Header of the response.
        iterable: iterable

        Yields
        ------
        str
            Stream response
    """

    # first '{' has to be escaped
    yield '{{ "{0}": ['.format(header)
    if len(iterable) > 0:
        yield json.dumps(iterable[0])
        for item in iterable[1:]:
            yield ",{0}".format(json.dumps(item))

    yield "] }"


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
    elif prefix == "string":
        return False
    elif " " in prefix:
        return False
    else:
        return True


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


def send_data(
    sparql_query, url_send_local_virtuoso, virtuoso_user, virtuoso_pass
):
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
        headers = {"content-type": "application/sparql-query"}
        r = requests.post(
            url,
            data=sparql_query,
            headers=headers,
            auth=requests.auth.HTTPBasicAuth(virtuoso_user, virtuoso_pass),
        )

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

    base_complement = {
        "A": "T",
        "C": "G",
        "G": "C",
        "T": "A",
        "a": "T",
        "c": "G",
        "g": "C",
        "t": "A",
        "n": "N",
        "N": "N",
    }

    # convert string into list with each character as a separate element
    bases = list(dna_sequence)

    # determine complement strand
    bases = [base_complement[base] for base in bases]

    complement_strand = "".join(bases)

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
    if method == "original":
        try:
            protseq = translate_sequence(myseq, table_id)
        except Exception as argh:
            return argh
    # try to translate the reverse complement
    elif method == "revcomp":
        try:
            myseq = reverse_complement(myseq)
            protseq = translate_sequence(myseq, table_id)
        except Exception as argh:
            return argh
    # try to translate the reverse
    elif method == "rev":
        try:
            myseq = reverse_str(myseq)
            protseq = translate_sequence(myseq, table_id)
        except Exception as argh:
            return argh
    # try to translate the reverse reverse complement
    elif method == "revrevcomp":
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
        return "ambiguous or invalid characters"


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
        return "sequence length is not a multiple of {0}".format(number)


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
    strands = ["sense", "antisense", "revsense", "revantisense"]
    translating_methods = ["original", "revcomp", "rev", "revrevcomp"]

    # check if the string is DNA, without ambiguous bases
    valid_dna = check_str_alphabet(original_seq, "ACTG")
    if valid_dna is not True:
        return valid_dna

    # check if sequence is multiple of three
    valid_length = check_str_multiple(original_seq, 3)
    if valid_length is not True:
        return valid_length

    # check if sequence is not shorter than the accepted minimum length
    if len(original_seq) < min_len:
        return "sequence shorter than {0} nucleotides".format(min_len)

    # try to translate in 4 different orientations
    # or reach the conclusion that the sequence cannot be translated
    i = 0
    translated = False
    while translated is False:
        sequence, exception_collector = retranslate(
            original_seq,
            translating_methods[i],
            table_id,
            strands[i],
            exception_collector,
        )

        i += 1
        if i == len(strands) or isinstance(sequence, list) is True:
            translated = True

    coding_strand = strands[i - 1]

    # if the sequence could be translated, return list with protein and DNA
    # sequence in correct orientation
    if isinstance(sequence, list):
        return [sequence, coding_strand]
    # if it could not be translated, return the string with all exception
    # that were collected
    else:
        exception_str = ",".join(exception_collector)
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
        exception_collector.append(
            "{0}({1})".format(strands, translated_seq.args[0])
        )

    return [translated_seq, exception_collector]


def enforce_locking(user_role, user_uri, locking_value):
    """ Enforce role permissions on users, in order to
        modify data.

        Parameters
        ----------
        user_role: str
            Role of a user.
        user_uri: str
            URI of a user.
        locking_value:

        Returns
        -------
        allow: list
            A list that contains:
                - bool, True if user has persmissions
                  False otherwise.
                - dict, JSON format dict containing message
                  detailing if the user is allowed or not
                  to modify a schema.

    """

    allow = [True, user_role]
    if user_role not in ["Admin", "Contributor"]:
        allow = [False, "must have Admin or Contributor permissions."]

    # if user is a Contributor, check if it is the one that locked the schema
    if user_role == "Contributor" and user_uri != locking_value:
        allow = [
            False,
            "must have Admin permissions or be the Contributor that is altering the schema.",
        ]

    return allow
