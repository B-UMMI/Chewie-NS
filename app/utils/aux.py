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
    if len(arg) == 0:
        abort(400)
	
    # if arg is larger than 30000, abort
    elif len(arg) > 30000:
        abort(400)



def reverseComplement(strDNA):
    basecomplement = {'A': 'T', 'C': 'G', 'G': 'C', 'T': 'A'}
    strDNArevC = ''
    for l in strDNA:
        strDNArevC += basecomplement[l]

    return strDNArevC[::-1]


def translateSeq(DNASeq, verbose,CDSEnforce):
    if verbose:
        def verboseprint(*args):
            for arg in args:
                print (arg),
            print
    else:
        verboseprint = lambda *a: None  # do-nothing function

    seq = DNASeq
    tableid = 11
    inverted = False
    try:
        myseq = Seq(seq)
        protseq = Seq.translate(myseq, table=tableid, cds=CDSEnforce)
    except:
        try:
            seq = reverseComplement(seq)
            myseq = Seq(seq)
            protseq = Seq.translate(myseq, table=tableid, cds=CDSEnforce)
            inverted = True
        except:
            try:
                seq = seq[::-1]
                myseq = Seq(seq)
                protseq = Seq.translate(myseq, table=tableid, cds=CDSEnforce)
                inverted = True
            except:
                try:
                    seq = seq[::-1]
                    seq = reverseComplement(seq)
                    myseq = Seq(seq)
                    protseq = Seq.translate(myseq, table=tableid, cds=CDSEnforce)
                    inverted = False
                except Exception as e:
                    verboseprint("translation error")
                    verboseprint(e)
                    raise

    return str(protseq)

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
