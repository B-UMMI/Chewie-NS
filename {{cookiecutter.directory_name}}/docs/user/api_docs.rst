Swagger Namespaces Overview
===========================

The Swagger page shows that the API is divided by 7 namespaces, which contain endpoints for specific operations:

auth
::::

In this namespace we have endopints responsible for the authentication in the API. The ``/login`` endpoint is where the authentication takes place, containing the default admin user.

::

    {
        "email": "your_email",
        "password": "your_password"
    }

Output

::

    {
        "status": "success",
        "message": "Successfully logged in.",
        "access_token": "[access token]",
        "refresh_token": "[refresh token]"
    }

The access token has an expiry period of **3 hours**, after which you need to access the ``/refresh`` endpoint to acquire a new access token by providing the refresh token that was received after the login.

user
::::

This namespace contains endpoints mainly for user management where only the admins will have access, except on the ``/register_user`` endpoint where users will be able to register freely.

download
::::::::

This namespace contains endpoints that allow the download of a compressed chewBBACA schema and the prodigal training file used to create it.

stats
:::::

This namespace contains the endpoints that are accessed by the user interface. Returns the data necessary to generate the plots that are rendered on the web page.

loci
::::

This namespace contains endpoints to get data about the loci of the database, such as its alleles, the FASTA sequence and the Uniprot annotation.

species
:::::::

This namespace contains endpoints to get data about all species on the database and also about a specific species, such as the schemas avaliable for it and the loci belonging to them.

sequences
:::::::::

This namespace contains only two endpoints, ``/list`` and ``seq_info``.

``/list`` counts all the sequences on the database and returns that count.

``seq_info`` allows the user to provide a DNA sequence (or hash) to check if the sequence exists in the database.

For example, if we want to find out if a particular allele exists in the database we can provide the DNA sequence to the endpoint to search on the database.

If it exists the output will show which schema it belongs to, the locus and allele IDs and the Uniprot annotation.

Output

::

    {
        "result": [
            {
            "schemas": {
                "type": "uri",
                "value": "http://127.0.0.1:5000/NS/api/species/2/schemas/1"
            },
            "locus": {
                "type": "uri",
                "value": "http://127.0.0.1:5000/NS/api/loci/1"
            },
            "alleles": {
                "type": "uri",
                "value": "http://127.0.0.1:5000/NS/api/loci/1/alleles/1"
            },
            "uniprot": {
                "type": "uri",
                "value": "http://purl.uniprot.org/uniprot/S9B1H0"
            },
            "label": {
                "type": "typed-literal",
                "datatype": "http://www.w3.org/2001/XMLSchema#string",
                "value": "Chromosomal replication initiator protein DnaA"
            }
        } ]
    }
