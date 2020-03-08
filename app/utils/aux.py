import json
import time
import urllib.request
from urllib.parse import urlparse

import requests
from Bio.Seq import Seq
from flask import abort
from SPARQLWrapper import JSON


def get_data(server, sparql_query):
    """ Gets data from Virtuoso """
    
    try:
        server.setQuery(sparql_query)
        server.setReturnFormat(JSON)
        server.setTimeout(20)
        result = server.query().convert()
    except Exception as e:
        time.sleep(5)
        try:
            server.setQuery(sparql_query)
            server.setReturnFormat(JSON)
            server.setTimeout(20)
            result = server.query().convert()
        except Exception as e:
            result = e
            
    return result

def get_read_run_info_ena(ena_id):

	url = 'http://www.ebi.ac.uk/ena/data/warehouse/filereport?accession=' + ena_id + 'AAA&result=read_run'

	read_run_info = False
	try:
		with urllib.request.urlopen(url) as url:
			read_run_info = url.read().splitlines()
			if len(read_run_info) <= 1:
				read_run_info = False
			else:
				read_run_info=True
	except Exception as error:
		print(error)
	
	return read_run_info


def get_read_run_info_sra(SRA_id):
	
	url = 'https://trace.ncbi.nlm.nih.gov/Traces/sra/sra.cgi?save=efetch&db=sra&rettype=runinfo&term=%20'+SRA_id
	
	read_run_info = False
	try:
		with urllib.request.urlopen(url,timeout = 2) as url:

			#if the SRA_id is not found ncbi is very generous and may give a tsunami of info, limit that to 30k bytes if that's the case
			#we wont consider that ID
			read_run_info = url.read(30000)
			try:
				read_run_info=read_run_info.splitlines()
			except:
				return read_run_info

			
			#check if the ERR is on the second element of the list returned
			#thanks NCBI for returning wtv if the SRA_id is "LALA" or whatever I put there
			#very cranky bypass of this, change in the future
			
			if SRA_id in read_run_info[1].decode("utf-8") :
				read_run_info=True
			else:
				read_run_info=False
			
	except Exception as error:
		print(error)

	return read_run_info


#dirty way to check the disease URI is real, no pun intended :)))
def check_disease_resource(URI):
	try:
		
		print('http://www.ontobee.org/ontology/rdf/DOID?iri='+URI)
		r = requests.get('http://www.ontobee.org/ontology/rdf/DOID?iri='+URI)
		print(r.status_code)
		diseaseFound=False
		if int(r.status_code)<202:
			diseaseFound=True
	except Exception as e:
		print(e)
		diseaseFound=False
	return diseaseFound


def sanitize_input(mystring):
    """
    """
    
    print ("sanitizing")
    
    mystring = mystring.replace("'", "")
    
    mystring = mystring.encode('ascii', 'ignore')
    mystring = mystring.decode("utf-8")
    
    mystring = mystring.replace("\\", "") 
	
    return mystring


def send_data(sparql_query, url_send_local_virtuoso, virtuoso_user, virtuoso_pass):
    """ Sends data to Virtuoso
    """

    url = url_send_local_virtuoso
    headers = {'content-type': 'application/sparql-query'}
    r = requests.post(url, data=sparql_query, headers=headers, auth=requests.auth.HTTPBasicAuth(virtuoso_user, virtuoso_pass))
    
    #sometimes virtuoso returns 405 God knows why ¯\_(ツ)_/¯ retry in 2 sec
    if r.status_code >201:
        time.sleep(2)
        r = requests.post(url, data=sparql_query, headers=headers, auth=requests.auth.HTTPBasicAuth(virtuoso_user, virtuoso_pass))
        
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
    """ Check string length 
    """
    
    # if there is no arg, abort
    if len(arg) == 0 or len(arg) > 30000:
        return False
    else:
        return True


def check_prefix(prefix):
    """ Check prefix 
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


def reverse_str(string):
    """ Reverse character order in input string.

        Args:
            string (str): string to be reversed.

        Returns:
            revstr (str): reverse of input string.
    """

    revstr = string[::-1]

    return revstr


def reverse_complement(dna_sequence):
    """ Determines the reverse complement of given DNA strand.

        Args:
            dna_sequence (str): string representing a DNA sequence.

        Returns:
            reverse_complement_strand (str): the reverse complement
            of the DNA sequence, without lowercase letters.
    """

    base_complement = {'A': 'T', 'C': 'G', 'G': 'C', 'T': 'A',
                       'a': 'T', 'c': 'G', 'g': 'C', 't': 'A'}

    # convert string into list with each character as a separate element
    bases = list(dna_sequence)

    # determine complement strand
    complement_bases = []
    for base in bases:
        if base in base_complement:
            complement_bases.append(base_complement[base])
        else:
            complement_bases.append(base.upper())

    complement_strand = join_list(complement_bases, '')

    # reverse strand
    reverse_complement_strand = reverse_str(complement_strand)

    return reverse_complement_strand


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
    # sequences must be a complete and valid CDS
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
        exception_str = join_list(exception_collector, ',')
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

def is_url(url):
    """ Checks if a url is valid

        Args: 
        url (str): the url to be checked

        Returns:
        True if url is valid, False otherwise.

    """

    try:
        
        result = urlparse(url)
        return all([result.scheme, result.netloc, result.path])

    except:
        return False


def uniprot_query(sequence):
    """ Constructs a SPARQL query to search for exact matches in the
        UniProt endpoint.

        Args:
            sequence (str): the Protein sequence that will be added
            to the query.
        Returns:
            query (str): the SPARQL query that will allow to seaarch for
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

        Args:
            result (dict): a dictionary with the results
            from querying the UniProt SPARQL endpoint.
        Returns:
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
