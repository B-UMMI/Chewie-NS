import datetime as dt
import os

from app.api.dependencies import auxiliary_functions as aux
from app.api.dependencies import sparql_queries as sq
from app.core.celery_app import celery_app

# from aiosparql.client import SPARQLClient, SPARQLRequestFailed

from SPARQLWrapper import SPARQLWrapper


@celery_app.task(acks_late=True)
def example_task(word: str) -> str:
    return f"test task returns {word}"


@celery_app.task(acks_late=True)
def add_allele(
    new_locus_url: str,
    spec_name: str,
    loci_id: str,
    new_user_url: str,
    new_seq_url: str,
    isNewSeq: bool,
    sequence: str,
    allele_uri: str,
):
    """Adds an allele to a locus.

        Parameters
        ----------
        new_locus_url: str
            URL of the locus to be inserted
        spec_name: str
            Name of the species the allele belongs to.
        loci_id: str
            ID of the locus the allele is being added to.
        new_user_url: str
            URI of the user adding the allele.
        new_seq_url: str
            URI of the allele DNA sequence.
        isNewSeq: bool
            True if it's a new sequence,
            False if it's already on NS.
        sequence: str
            Allele DNA sequence.
        allele_uri: str
            URI of the allele.

        Returns
        -------
        dict
            JSON format dict with the result of the request.
        int
            Request status code.
            201 if Successful
    """

    # client = SPARQLClient(os.environ.get("LOCAL_SPARQL"))

    max_tries = 3
    new_allele_url = allele_uri

    # add allele to virtuoso
    if isNewSeq:

        query2send = sq.INSERT_ALLELE_NEW_SEQUENCE.format(
            os.environ.get("DEFAULT_GRAPH"),
            new_seq_url,
            sequence,
            new_allele_url,
            spec_name,
            new_user_url,
            new_locus_url,
            str(dt.datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")),
            new_allele_url.split("/")[-1],
        )
        operation = ["ADD", "add", "added"]
    else:

        query2send = sq.INSERT_ALLELE_LINK_SEQUENCE.format(
            os.environ.get("DEFAULT_GRAPH"),
            new_allele_url,
            spec_name,
            new_user_url,
            new_locus_url,
            str(dt.datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")),
            new_allele_url.split("/")[-1],
            new_seq_url,
        )
        operation = ["LINK", "link", "linked"]

    tries = 0
    insert = False
    while insert is False:

        # if len(sequence) < 2000:
        result = aux.send_data(
            query2send,
            os.environ.get("LOCAL_SPARQL"),
            os.environ.get("VIRTUOSO_USER"),
            os.environ.get("VIRTUOSO_PASS"),
        )
        #            else:
        #                result = aux.send_big_query(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
        #                                            query2send,
        #                                            current_app.config['VIRTUOSO_USER'],
        #                                            current_app.config['VIRTUOSO_PASS'])

        tries += 1

        if result.status_code in [200, 201]:
            insert = True
        elif tries == max_tries:
            insert = True

    if result.status_code > 201:
        # return (
        #     {"FAIL": "Could not {0} new allele.".format(operation[1])},
        #     result.status_code,
        # )

        return {"Could not {0} new allele.".format(operation[1])}
    else:
        # return (
        #     {
        #         operation[0]: "A new allele has been {0} to {1}".format(
        #             operation[2], new_allele_url
        #         )
        #     },
        #     result.status_code,
        # )

        return {
            "operation": operation[0],
            "message": "A new allele has been {0} to {1}".format(
                operation[2], new_allele_url
            ),
        }


# queue to insert single locus
@celery_app.task(acks_late=True)
def add_locus_schema(new_schema_url, new_locus_url):
    """ Add a locus to a schema.

        Parameters
        ----------
        new_schema_url: str
            URL of the schema
        new_locus_url: str
            URL of the locus to be inserted

        Return
        ------
        dict
            JSON format dict with the result of the request.
        int
            Request status code.
            201 if Successful
    """

    # count number of loci on schema and build the uri based on that number+1
    loci_count = aux.get_data(
        SPARQLWrapper(os.environ.get("LOCAL_SPARQL")),
        sq.COUNT_SCHEMA_LOCI.format(
            os.environ.get("DEFAULT_GRAPH"), new_schema_url
        ),
    )

    # 0 if schema has no loci
    number_schema_parts = int(
        loci_count["results"]["bindings"][0]["count"]["value"]
    )

    # create URI for new schema part
    new_schema_part_url = "{0}/loci/{1}".format(
        new_schema_url, str(number_schema_parts + 1)
    )

    # link locus to schema (previous operations determined that schema exists)
    link_query = sq.INSERT_SCHEMA_LOCUS.format(
        os.environ.get("DEFAULT_GRAPH"),
        new_schema_part_url,
        str(number_schema_parts + 1),
        new_locus_url,
        new_schema_url,
        new_schema_part_url,
    )

    link_locus = aux.send_data(
        link_query,
        os.environ.get("LOCAL_SPARQL"),
        os.environ.get("VIRTUOSO_USER"),
        os.environ.get("VIRTUOSO_PASS"),
    )

    if link_locus.status_code in [200, 201]:
        return {"message": "Locus successfully added to schema."}, 201
    else:
        return (
            {"message": "Could not add locus to schema."},
            link_locus.status_code,
        )
