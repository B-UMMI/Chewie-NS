#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AUTHORS

    Mickael Silva
    github: @

    Pedro Cerqueira
    github: @pedrorvc

    Rafael Mamede
    github: @rfm-targa

DESCRIPTION

"""


COUNT_SCHEMA_LOCI = ('SELECT (COUNT(?parts) AS ?count) '
                     'FROM <{0}>'
                     'WHERE {{ <{1}> typon:hasSchemaPart ?parts. }}')

COUNT_SCHEMAS = ('SELECT (COUNT(?schemas) AS ?count) '
                 'FROM <{0}> '
                 'WHERE '
                 '{{ ?schemas a typon:Schema; typon:isFromTaxon <{1}>. }}')

INSERT_SCHEMA = ('INSERT DATA IN GRAPH <{0}> '
                 '{{ <{1}> a typon:Schema; typon:isFromTaxon <{2}>; '
                 'typon:administratedBy <{3}>; typon:schemaName "{4}"^^xsd:string; '
                 'typon:bsr "{5}"^^xsd:string; typon:chewBBACA_version "{6}"^^xsd:string; '
                 'typon:ptf "{7}"^^xsd:string; typon:translation_table "{8}"^^xsd:string; '
                 'typon:minimum_locus_length "{9}"^^xsd:string; '
                 'typon:size_threshold "{10}"^^xsd:string; '
                 'typon:word_size "{11}"^^xsd:string; '
                 'typon:cluster_sim "{12}"^^xsd:string; '
                 'typon:representative_filter "{13}"^^xsd:string; '
                 'typon:intraCluster_filter "{14}"^^xsd:string; '
                 'typon:dateEntered "{15}"^^xsd:dateTime; '
                 'typon:last_modified "{16}"^^xsd:string; '
                 'typon:Schema_lock "{17}"^^xsd:string .}}')

COUNT_TOTAL_LOCI = ('SELECT (COUNT(?locus) AS ?count) '
                    'FROM <{0}> '
                    'WHERE '
                    '{{ ?locus a typon:Locus . }}')

ASK_LOCUS_PREFIX = ('ASK WHERE {{ ?locus a typon:Locus; typon:name ?name . '
                    'FILTER CONTAINS(str(?name), "{0}") }}')

INSERT_LOCUS = ('INSERT DATA IN GRAPH <{0}> '
                '{{ <{1}> a typon:Locus; '
                'typon:name "{2}"^^xsd:string{3} }}')

SELECT_LOCUS = ('SELECT (str(?name) AS ?name) (str(?original_name) AS ?original_name) '
                'FROM <{0}>'
                ' WHERE '
                '{{ <{1}> a typon:Locus; typon:name ?name . '
                'OPTIONAL{{<{1}> typon:originalName ?original_name.}} '
                'OPTIONAL{{<{1}> typon:isOfTaxon ?taxon}} }}')

SELECT_LOCUS_FASTA = ('SELECT ?name ?allele_id (str(?nucSeq) AS ?nucSeq) (strlen(?nucSeq) as ?nucSeqLen) '
                      'FROM <{0}> '
                      'WHERE '
                      '{{ <{1}> a typon:Locus; typon:name ?name. '
                      '?alleles typon:isOfLocus <{1}> .'
                      '?alleles typon:hasSequence ?sequence; typon:id ?allele_id .'
                      '?sequence typon:nucleotideSequence ?nucSeq. }} '
                      'ORDER BY ASC(?allele_id)')

SELECT_LOCUS_FASTA_BY_DATE = ('SELECT ?name ?allele_id (str(?nucSeq) AS ?nucSeq) (strlen(?nucSeq) AS ?nucSeqLen) ?date '
                              'FROM <{0}> '
                              'WHERE '
                              '{{ <{1}> a typon:Locus; typon:name ?name .'
                              '?alleles typon:isOfLocus <{1}>; '
                              'typon:dateEntered ?date .'
                              '?alleles typon:hasSequence ?sequence; typon:id ?allele_id .'
                              '?sequence typon:nucleotideSequence ?nucSeq . '
                              'FILTER ( ?date < "{2}"^^xsd:dateTime )}} '
                              'ORDER BY ASC(?allele_id)')

SELECT_LOCUS_UNIPROT = ('select distinct ?name (str(?UniprotLabel) as ?UniprotLabel) (str(?UniprotSName) as ?UniprotSName) (str(?UniprotURI) as ?UniprotURI) '
                        'from <{0}>'
                        'where '
                        '{{ <{1}> a typon:Locus; typon:name ?name. '
                        '?alleles typon:isOfLocus <{1}> .'
                        '?alleles typon:hasSequence ?sequence. '
                        'OPTIONAL{{?sequence typon:hasUniprotLabel ?UniprotLabel.}} '
                        'OPTIONAL{{?sequence typon:hasUniprotSName ?UniprotSName.}}'
                        'OPTIONAL{{?sequence typon:hasUniprotSequence ?UniprotURI }} }}')

SELECT_LOCUS_SEQS = ('SELECT ?allele_id ?sequence '
                     'FROM <{0}>'
                     'WHERE '
                     '{{ <{1}> a typon:Locus; typon:name ?name. '
                     '?alleles typon:isOfLocus <{1}> .'
                     '?alleles typon:hasSequence ?sequence; typon:id ?allele_id .}} '
                     'ORDER BY ASC(?allele_id)')

SELECT_LOCUS_SEQS_BY_DATE = ('SELECT ?allele_id ?sequence ?date '
                             'FROM <{0}>'
                             'WHERE '
                             '{{ <{1}> a typon:Locus; typon:name ?name. '
                             '?alleles typon:isOfLocus <{1}>; '
                             'typon:dateEntered ?date .'
                             '?alleles typon:hasSequence ?sequence; typon:id ?allele_id . '
                             'FILTER ( ?date < "{2}"^^xsd:dateTime )}} '
                             'ORDER BY ASC(?allele_id)')

SELECT_LOCUS_SPECIES_ALLELES = ('SELECT ?alleles '
                                'FROM <{0}> '
                                'WHERE '
                                '{{ <{1}> a typon:Locus; typon:hasDefinedAllele ?alleles. '
                                '?alleles typon:id ?id; typon:name ?name . '
                                'FILTER CONTAINS(str(?name), "{2}")}}  '
                                'ORDER BY ASC(?id)')

SELECT_LOCUS_ALLELE = ('SELECT ?alleles '
                       'FROM <{0}> '
                       'WHERE '
                       '{{ ?alleles typon:isOfLocus <{1}>; typon:hasSequence ?seq. '
                       '?seq a typon:Sequence; typon:nucleotideSequence "{2}"^^xsd:string.}}')

SELECT_LOCUS_ALLELES = ('SELECT ?alleles '
                        'FROM <{0}> '
                        'WHERE '
                        '{{ <{1}> a typon:Locus; typon:hasDefinedAllele ?alleles. '
                        '?alleles typon:id ?id }}'
                        'ORDER BY ASC(?id)')

COUNT_LOCUS_ALLELES = ('SELECT (COUNT(?alleles) AS ?count)'
                       'FROM <{0}>'
                       'WHERE '
                       '{{ ?alleles typon:isOfLocus <{1}>.}}')

SELECT_SEQ_FASTA = ('select (str(?nucSeq) as ?nucSeq) '
                    'from <{0}>'
                    'where '
                    '{{<{1}> typon:nucleotideSequence ?nucSeq. }}')

SELECT_LOCUS_SCHEMA = ('SELECT ?schema '
                       'FROM <{0}> '
                       'WHERE {{?schema typon:hasSchemaPart ?part .'
                       '?part typon:hasLocus <{1}> .}}')

SELECT_ALL_LOCI = ('SELECT ?locus (str(?name) AS ?name) (str(?original_name) AS ?original_name)'
                   'FROM <{0}> '
                   'WHERE '
                   '{{ ?locus a typon:Locus; typon:name ?name; '
                   'typon:originalName ?original_name .'
                   'BIND((strafter(str(?locus), "loci/") AS ?lastChar))}}'
                   'ORDER BY ASC(xsd:integer(?lastChar))')

INSERT_SCHEMA_LOCUS = ('INSERT DATA IN GRAPH <{0}> '
                       '{{ <{1}> a typon:SchemaPart ; '
                       'typon:index "{2}"^^xsd:int ; '
                       'typon:hasLocus <{3}>.'
                       '<{4}> typon:hasSchemaPart <{5}>.}}')

ASK_SCHEMA_LOCK = ('ASK WHERE {{ <{0}> a typon:Schema; '
                   'typon:Schema_lock "Unlocked"^^xsd:string }}')

ASK_SCHEMA_LOCUS = ('ASK WHERE {{ <{0}> typon:hasSchemaPart ?part. '
                    '?part typon:hasLocus <{1}>.}}')

ASK_SCHEMA_LOCUS2 = ('ASK where {{ <{0}> typon:hasSchemaPart ?part. '
                     '?part typon:hasLocus <{1}>. '
                     'FILTER NOT EXISTS {{ ?part typon:deprecated  "true"^^xsd:boolean }}.}}')

ASK_SCHEMA_DEPRECATED = ('ASK WHERE {{ <{0}> typon:deprecated "true"^^xsd:boolean.}}')

ASK_SCHEMA_DEPRECATED2 = ('ASK WHERE {{ <{0}> a typon:Schema; typon:deprecated "true"^^xsd:boolean }}')

SELECT_SCHEMA_LOCK = ('SELECT (str(?description) AS ?name) '
                      '(str(?Schema_lock) AS ?Schema_lock) '
                      'FROM <{0}> '
                      'WHERE '
                      '{{ <{1}> typon:schemaName ?description; '
                      'typon:Schema_lock ?Schema_lock . }}')

SELECT_SCHEMA_DATE = ('SELECT (str(?description) AS ?name) '
                      '(str(?last_modified) AS ?last_modified) '
                      'FROM <{0}> '
                      'WHERE '
                      '{{ <{1}> typon:schemaName ?description; '
                      'typon:last_modified ?last_modified . }}')

SELECT_SCHEMA_PTF = ('SELECT (str(?description) AS ?name) '
                      '(str(?ptf) AS ?ptf) '
                      'FROM <{0}> '
                      'WHERE '
                      '{{ <{1}> typon:schemaName ?description; '
                      'typon:ptf ?ptf . }}')

SELECT_SCHEMA_LOCI = ('SELECT ?locus (str(?name) AS ?name) (str(?original_name) AS ?original_name)'
                      'FROM <{0}> '
                      'WHERE '
                      '{{ <{1}> typon:hasSchemaPart ?part. '
                      '?part typon:hasLocus ?locus.'
                      '?locus typon:name ?name ; typon:originalName ?original_name. '
                      'FILTER NOT EXISTS {{ ?part typon:deprecated  "true"^^xsd:boolean }} }}'
                      'ORDER BY (?name) ')

SELECT_SCHEMA_LATEST_ALLELES = ('SELECT ?locus_name ?allele_id ?sequence ?date '
                                'FROM <{0}> '
                                'WHERE {{ '
                                ' {{ SELECT ?locus_name ?allele_id ?sequence ?date '
                                'FROM <{0}> '
                                'WHERE {{ <{1}> typon:hasSchemaPart ?part. '
                                '?part typon:hasLocus ?locus . '
                                '?alleles typon:isOfLocus ?locus; '
                                'typon:dateEntered ?date; '
                                'typon:hasSequence ?sequence; typon:id ?allele_id. '
                                '?locus typon:name ?locus_name. '
                                'FILTER ( ?date > "{2}"^^xsd:dateTime ). '
                                'FILTER NOT EXISTS {{ ?part typon:deprecated  "true"^^xsd:boolean }}.}}'
                                'ORDER BY ASC(?date)}} }} LIMIT 50000')

SELECT_SCHEMA = ('SELECT ?schema '
                 'FROM <{0}> '
                 'WHERE {{?schema a typon:Schema; '
                 'typon:isFromTaxon <{1}>; '
                 'typon:schemaName "{2}"^^xsd:string .}}')

INSERT_USER = ('INSERT DATA IN GRAPH <{0}> '
               '{{ <{1}> a <http://xmlns.com/foaf/0.1/Agent>; '
               'typon:Role "{2}"^^xsd:string; '
               'typon:username "{3}"^^xsd:string . }}')

ASK_USER = ('ASK WHERE {{ <{0}> a <http://xmlns.com/foaf/0.1/Agent> .}}')

SELECT_USER = ('SELECT ?user ?role ?username '
               'FROM <{0}>'
               'WHERE {{ ?user a <http://xmlns.com/foaf/0.1/Agent>; '
               'typon:Role ?role; typon:username ?username . FILTER ( ?user = <{1}> )}}')

DELETE_USER = ('DELETE WHERE {{ GRAPH <{0}> {{ ?user a <http://xmlns.com/foaf/0.1/Agent>; '
               'typon:Role ?role; typon:username ?username . FILTER ( ?user = <{1}> ) }} }}')

DELETE_ROLE = ('DELETE WHERE {{ GRAPH <{0}> {{ <{1}> typon:Role ?role . }} }}')
INSERT_ROLE = ('INSERT DATA IN GRAPH <{0}> '
               '{{ <{1}> typon:Role "Contributor"^^xsd:string . }}')

SELECT_UNIPROT_TAXON = ('PREFIX up:<http://purl.uniprot.org/core/> '
                        'PREFIX taxon:<http://purl.uniprot.org/taxonomy/> '
                        'PREFIX rdfs:<http://www.w3.org/2000/01/rdf-schema#> '
                        'SELECT ?taxon FROM <http://sparql.uniprot.org/taxonomy> WHERE'
                        '{{ ?taxon a up:Taxon; rdfs:subClassOf taxon:2; up:scientificName "{0}" .}}')

COUNT_TAXON = ('SELECT (COUNT(?taxon) AS ?count) '
               'FROM <{0}> '
               'WHERE '
               '{{ ?taxon a <http://purl.uniprot.org/core/Taxon> }}')

# determine if species exists locally with Uniprot URL
ASK_SPECIES_UNIPROT = ('ASK WHERE {{ ?species owl:sameAs <{0}> .}}')

# determine if species exists locally with species NS URI
ASK_SPECIES_NS = ('ASK where {{ <{0}> a <http://purl.uniprot.org/core/Taxon>}}')

SELECT_SINGLE_SPECIES = ('SELECT ?species ?name '
                         'FROM <{0}> '
                         'WHERE '
                         '{{ <{1}> a <http://purl.uniprot.org/core/Taxon>; typon:name ?name .}}')

ASK_LOCUS = ('ASK WHERE {{ <{0}> a typon:Locus .}}')

ASK_SEQUENCE_HASH = ('ASK WHERE {{ <{0}> typon:nucleotideSequence ?seq.}}')

ASK_SEQUENCE_HASH_SEQ = ('ASK WHERE {{ <{0}> a typon:Sequence; '
                         'typon:nucleotideSequence "{1}"^^xsd:string.}}')

SELECT_ALLELE_INFO = ('SELECT ?sequence (str(?name) AS ?source) ?date ?id (COUNT(?isolate) AS ?isolate_count) '
                      'FROM <{0}> '
                      'WHERE '
                      '{{ <{1}> a typon:Allele; typon:name ?name; typon:dateEntered ?date; typon:hasSequence ?sequence; typon:id ?id. '
                      'OPTIONAL {{?isolate a typon:Isolate; typon:hasAllele <{1}>}} }}')

NS_STATS = ('SELECT * '
            'FROM <{0}>'
            'WHERE {{ '
            '{{ SELECT (COUNT(?seq) AS ?sequences) WHERE {{?seq a typon:Sequence }} }} '
            '{{ SELECT (COUNT(?spec) AS ?species) WHERE {{?spec a <http://purl.uniprot.org/core/Taxon>}} }} '
            '{{ SELECT (COUNT(?loc) AS ?loci) WHERE {{?loc a typon:Locus }} }} '
            '{{ SELECT (COUNT(?user) AS ?users) WHERE {{?user a <http://xmlns.com/foaf/0.1/Agent>. }} }} '
            '{{ SELECT (COUNT(?schema) AS ?schemas) WHERE {{?schema a typon:Schema. }} }} '
            '{{ SELECT (COUNT(?isol) AS ?isolates) WHERE {{?isol a typon:Isolate. }} }} '
            '{{ SELECT (COUNT(?all) AS ?alleles) WHERE {{?all a typon:Allele. }} }} }}')

COUNT_SPECIES_SCHEMAS = ('SELECT ?species ?name (COUNT(?sch) AS ?schemas) '
                         'FROM <{0}> '
                         'WHERE '
                         '{{ ?sch a typon:Schema; typon:isFromTaxon ?species . '
                         '?species a <http://purl.uniprot.org/core/Taxon>; typon:name ?name . }}'
                         'ORDER BY ?species')

COUNT_LOCI_ALLELE = ('SELECT ?schema ?locus (COUNT(DISTINCT ?allele) AS ?nr_allele) '
                     'FROM <{0}> '
                     'WHERE '
                     '{{ ?schema a typon:Schema; typon:isFromTaxon <{1}>; '
                     'typon:hasSchemaPart ?part . '
                     '?part a typon:SchemaPart; typon:hasLocus ?locus .'
                     '?allele a typon:Allele; typon:isOfLocus ?locus . '
                     '?allele typon:hasSequence ?sequence . }}'
                     'ORDER BY ?schema ?locus')

COUNT_SINGLE_SCHEMA_LOCI_ALLELE = ('SELECT ?locus (COUNT(DISTINCT ?allele) AS ?nr_allele) '
                                   'FROM <{0}> '
                                   'WHERE '
                                   '{{ <{1}> a typon:Schema; '
                                   'typon:hasSchemaPart ?part . '
                                   '?part a typon:SchemaPart; typon:hasLocus ?locus .'
                                   '?allele a typon:Allele; typon:isOfLocus ?locus . '
                                   '?allele typon:hasSequence ?sequence . }}'
                                   'ORDER BY ?schema ?locus')

COUNT_SCHEMA_LOCI_ALLELES = ('SELECT ?schema ?name ?user ?username ?chewie ?bsr ?ptf ?tl_table ?minLen ?Schema_lock (COUNT(DISTINCT ?locus) AS ?nr_loci) (COUNT(DISTINCT ?allele) AS ?nr_allele) '
                              'FROM <{0}> '
                              'WHERE '
                              '{{ ?schema a typon:Schema; typon:isFromTaxon <{1}>; '
                              'typon:schemaName ?name; typon:administratedBy ?user; '
                              'typon:chewBBACA_version ?chewie; typon:bsr ?bsr; '
                              'typon:ptf ?ptf; typon:translation_table ?tl_table; '
                              'typon:minimum_locus_length ?minLen; typon:Schema_lock ?Schema_lock; '
                              'typon:hasSchemaPart ?part . '
                              '?part a typon:SchemaPart; typon:hasLocus ?locus .'
                              '?allele a typon:Allele; typon:isOfLocus ?locus .'
                              '?user a <http://xmlns.com/foaf/0.1/Agent>; typon:username ?username .}}'
                              'ORDER BY ?schema')

# query for single schema
COUNT_SINGLE_SCHEMA_LOCI_ALLELES = ('SELECT ?name ?user ?username ?chewie ?bsr ?ptf ?tl_table ?minLen ?last_modified (COUNT(DISTINCT ?locus) AS ?nr_loci) (COUNT(DISTINCT ?allele) AS ?nr_allele) '
                                    'FROM <{0}> '
                                    'WHERE '
                                    '{{ <{1}> a typon:Schema; '
                                    'typon:schemaName ?name; typon:administratedBy ?user; '
                                    'typon:chewBBACA_version ?chewie; typon:bsr ?bsr; '
                                    'typon:ptf ?ptf; typon:translation_table ?tl_table; '
                                    'typon:minimum_locus_length ?minLen; '
                                    'typon:last_modified ?last_modified; '
                                    'typon:hasSchemaPart ?part . '
                                    '?part a typon:SchemaPart; typon:hasLocus ?locus .'
                                    '?allele a typon:Allele; typon:isOfLocus ?locus .'
                                    '?user a <http://xmlns.com/foaf/0.1/Agent>; typon:username ?username .}}')

COUNT_SCHEMA_ALLELES = ('SELECT ?locus (COUNT(DISTINCT ?allele) AS ?nr_allele) '
                        'FROM <{0}> '
                        'WHERE '
                        '{{ <{1}> a typon:Schema; '
                        'typon:hasSchemaPart ?part . '
                        '?part a typon:SchemaPart; typon:hasLocus ?locus .'
                        '?allele a typon:Allele; typon:isOfLocus ?locus .}}')

SELECT_ALLELES_LENGTH = ('SELECT ?locus (str(?name) AS ?name) (strlen(?nucSeq) AS ?nucSeqLen) '
                         'FROM <{0}> '
                         'WHERE '
                         '{{ <{1}> typon:hasSchemaPart ?part. '
                         '?part typon:hasLocus ?locus .'
                         '?locus typon:name ?name; typon:hasDefinedAllele ?allele . ' 
                         '?allele a typon:Allele; typon:isOfLocus ?locus .'
                         '?allele typon:hasSequence ?sequence .'
                         '?sequence typon:nucleotideSequence ?nucSeq .'
                         'FILTER NOT EXISTS {{ ?part typon:deprecated "true"^^xsd:boolean }} }}'
                         'ORDER BY (?name) OFFSET {2} LIMIT {3}')

SELECT_SCHEMA_LOCI_ANNOTATIONS = ('SELECT DISTINCT ?locus ?name (str(?UniprotLabel) AS ?UniprotLabel) '
                                  '(str(?UniprotURI) AS ?UniprotURI) '
                                  'FROM <{0}> '
                                  'WHERE '
                                  '{{ <{1}> a typon:Schema; typon:hasSchemaPart ?part . '
                                  '?part a typon:SchemaPart; typon:hasLocus ?locus .'
                                  '?locus a typon:Locus; typon:name ?name . '
                                  '?allele a typon:Allele; typon:isOfLocus ?locus . '
                                  '?allele typon:hasSequence ?sequence . '
                                  'OPTIONAL{{?sequence typon:hasUniprotLabel ?UniprotLabel.}} '
                                  'OPTIONAL{{?sequence typon:hasUniprotSequence ?UniprotURI }} }} '
                                  'ORDER BY ?locus ')

SELECT_SPECIES = ('PREFIX typon:<http://purl.phyloviz.net/ontology/typon#> '
                  'SELECT ?species ?name '
                  'FROM <{0}> '
                  'WHERE '
                  '{{ ?species owl:sameAs ?species2; '
                  'a <http://purl.uniprot.org/core/Taxon>;{1}}}')

INSERT_SPECIES = ('PREFIX typon:<http://purl.phyloviz.net/ontology/typon#> '
                  'INSERT DATA IN GRAPH <{0}> '
                  '{{ <{1}> owl:sameAs <{2}>; typon:name "{3}"^^xsd:string; a <http://purl.uniprot.org/core/Taxon>.}}')

SELECT_SPECIES_AND_SCHEMAS = ('SELECT ?species ?name ?schemas ?schemaName '
                              'FROM <{0}> '
                              'WHERE '
                              '{{ {{<{1}> owl:sameAs ?species; typon:name ?name.}} '
                              'UNION {{ ?schemas typon:isFromTaxon <{1}>; a typon:Schema; typon:schemaName ?schemaName. '
                              'FILTER NOT EXISTS {{ ?schemas typon:deprecated  "true"^^xsd:boolean }} }} }}')

SELECT_SPECIES_SCHEMA = ('SELECT ?schema '
                         '(str(?description) AS ?name) '
                         '(str(?bsr) AS ?bsr) '
                         '(str(?chewBBACA_version) AS ?chewBBACA_version) '
                         '(str(?ptf) AS ?prodigal_training_file) '
                         '(str(?trans) AS ?translation_table) '
                         '(str(?min_locus_len) AS ?minimum_locus_length) '
                         '(str(?st) AS ?size_threshold) '
                         '(str(?word_size) AS ?word_size) '
                         '(str(?cluster_sim) AS ?cluster_sim) '
                         '(str(?representative_filter) AS ?representative_filter) '
                         '(str(?intraCluster_filter) AS ?intraCluster_filter) '
                         '(str(?dateEntered) AS ?dateEntered) '
                         '(str(?last_modified) AS ?last_modified) '
                         '(str(?Schema_lock) AS ?Schema_lock) '
                         'FROM <{0}> '
                         'WHERE '
                         '{{ <{1}> typon:schemaName ?description; '
                         'typon:bsr ?bsr; typon:chewBBACA_version ?chewBBACA_version; typon:ptf ?ptf; '
                         'typon:translation_table ?trans; typon:minimum_locus_length ?min_locus_len; '
                         'typon:size_threshold ?st; typon:word_size ?word_size; '
                         'typon:cluster_sim ?cluster_sim; '
                         'typon:representative_filter ?representative_filter; '
                         'typon:intraCluster_filter ?intraCluster_filter; '
                         'typon:dateEntered ?dateEntered; '
                         'typon:last_modified ?last_modified; '
                         'typon:Schema_lock ?Schema_lock . }}')

SELECT_SPECIES_SCHEMAS = ('SELECT ?schemas ?name '
                          'FROM <{0}> '
                          'WHERE '
                          '{{ ?schemas a typon:Schema; typon:isFromTaxon <{1}>; typon:schemaName ?name. '
                          'FILTER NOT EXISTS {{ ?schemas typon:deprecated  "true"^^xsd:boolean }} }}')

ASK_SCHEMA_DESCRIPTION = ('ASK WHERE {{ ?schema a typon:Schema; '
                          'typon:isFromTaxon <{0}>; '
                          'typon:schemaName "{1}"^^xsd:string .}}')

ASK_SCHEMA_OWNERSHIP = ('ASK WHERE {{ <{0}> a typon:Schema; typon:administratedBy <{1}>.}}')

INSERT_SCHEMA_DEPRECATE = ('INSERT DATA IN GRAPH <{0}> '
                           '{{ <{1}> typon:deprecated "true"^^xsd:boolean.}}')

DELETE_SCHEMA_LOCK = ('DELETE WHERE {{ GRAPH <{0}> {{ <{1}> typon:Schema_lock ?Schema_lock . }} }}')

DELETE_SCHEMA_DATE = ('DELETE WHERE {{ GRAPH <{0}> {{ <{1}> typon:{2} ?{2} . }} }}')

INSERT_SCHEMA_LOCK = ('INSERT DATA IN GRAPH <{0}> '
                      '{{ <{1}> typon:Schema_lock "{2}"^^xsd:string . }}')

INSERT_SCHEMA_DATE = ('INSERT DATA IN GRAPH <{0}> '
                      '{{ <{1}> typon:{2} "{3}"^^xsd:string . }}')

COUNT_SEQUENCES = ('SELECT (COUNT(?seq) AS ?count) '
                   'FROM <{0}> '
                   'WHERE '
                   '{{?seq a typon:Sequence }}')

SELECT_LOCI_WITH_DNA = ('SELECT (str(?name) AS ?name) ?locus (str(?original_name) AS ?original_name) '
                        'FROM <{0}> '
                        'WHERE '
                        '{{?alleles typon:hasSequence <{1}>; '
                        'typon:isOfLocus ?locus.'
                        '?locus typon:isOfTaxon <{2}>.'
                        'OPTIONAL{{?locus typon:originalName ?original_name.}} .'
                        'OPTIONAL{{?locus typon:name ?name.}} }}')

SELECT_SPECIES_LOCI = ('SELECT (str(?name) AS ?name) ?locus (str(?original_name) AS ?original_name) '
                       'FROM <{0}> '
                       'WHERE '
                       '{{ ?locus a typon:Locus; typon:isOfTaxon <{1}>; typon:name ?name. '
                       'OPTIONAL{{?locus typon:originalName ?original_name.}} }}')

SELECT_SEQUENCE_INFO_BY_DNA = ('SELECT ?schemas ?locus ?alleles ?uniprot ?label '
                               'FROM <{0}> '
                               'WHERE '
                               '{{ ?alleles typon:hasSequence <{1}>; typon:isOfLocus ?locus. '
                               '?schemas a typon:Schema; typon:hasSchemaPart ?part . '
                               '?part a typon:SchemaPart; typon:hasLocus ?locus . '
                               '{2}'
                               'OPTIONAL {{ <{1}> typon:hasUniprotSequence ?uniprot.}}. '
                               'OPTIONAL {{ <{1}> typon:hasUniprotLabel ?label.}} }}')

SELECT_SEQUENCE_INFO_BY_HASH = ('SELECT ?schemas ?locus ?alleles ?sequence ?uniprot ?label '
                                'FROM <{0}> '
                                'WHERE '
                                '{{ <{1}> a typon:Sequence; typon:nucleotideSequence ?sequence . '
                                '?alleles typon:hasSequence <{1}>; typon:isOfLocus ?locus .'
                                '?schemas a typon:Schema; typon:hasSchemaPart ?part .'
                                '?part a typon:SchemaPart; typon:hasLocus ?locus . '
                                '{2}'
                                'OPTIONAL {{ <{1}> typon:hasUniprotSequence ?uniprot.}}. '
                                'OPTIONAL {{ <{1}> typon:hasUniprotLabel ?label.}} }}')

INSERT_ALLELE_NEW_SEQUENCE = ('INSERT DATA IN GRAPH <{0}> '
                              '{{ <{1}> a typon:Sequence {2} ; '
                              'typon:nucleotideSequence "{3}"^^xsd:string . '
                              '<{4}> a typon:Allele; '
                              'typon:name "{5}"^^xsd:string; '
                              'typon:sentBy <{6}>; '
                              'typon:isOfLocus <{7}>; '
                              'typon:dateEntered "{8}"^^xsd:dateTime; '
                              'typon:id "{9}"^^xsd:integer; '
                              'typon:hasSequence <{1}> . '
                              '<{7}> typon:hasDefinedAllele <{4}>.}}')

INSERT_ALLELE_LINK_SEQUENCE = ('INSERT DATA IN GRAPH <{0}> '
                               '{{ <{1}> a typon:Allele; '
                               'typon:name "{2}"; '
                               'typon:sentBy <{3}> ;'
                               'typon:isOfLocus <{4}>; '
                               'typon:dateEntered "{5}"^^xsd:dateTime; '
                               'typon:id "{6}"^^xsd:integer ; '
                               'typon:hasSequence <{7}>. '
                               '<{4}> typon:hasDefinedAllele <{1}>.}}')

SELECT_SEQUENCE_LOCI = ('SELECT ?locus (str(?name) AS ?name) (str(?original_name) AS ?original_name) '
                        'FROM <{0}>'
                        'WHERE '
                        '{{?alleles typon:hasSequence <{1}>; typon:isOfLocus ?locus .'                        
                        '?locus a typon:Locus; typon:name ?name; '
                        'typon:originalName ?original_name .}}')

