Installation
============
While you can access public repositories at `chewBBACA.online <https://chewBBACA.online>`_,
you may want to setup a private instance of Chewie-NS.
The deployment of local instances of Chewie-NS can be easily achieved through the
use of Docker Compose.

Chewie-NS is available for cloning from its Github 
`repository <https://github.com/B-UMMI/Nomenclature_Server_docker_compose>`_. ::

    git clone https://github.com/B-UMMI/Nomenclature_Server_docker_compose.git

You will also need a container engine (see `Container engine`_ below)

Container engine
----------------

All components of Chewie-NS are executed in `docker`_ containers and are 
orchestrated by `docker-compose`_, which means that you will need to install 
this container engine.

Docker
::::::

Docker can be installed following the instructions on the website:
https://www.docker.com/community-edition#/download.
To run docker as a non-root user, you will need to follow the instructions
on the website: https://docs.docker.com/install/linux/linux-postinstall/#manage-docker-as-a-non-root-user.


Docker-compose
::::::::::::::

To install docker-compose, you need to have installed docker beforehand. 
The installation instructions for Docker-compose can be found here: https://docs.docker.com/compose/install/


Create self-signed certificates
-------------------------------

A local instance of Chewie-NS will have `SSL <https://www.ssl.com/faqs/faq-what-is-ssl/>`_ 
support, just like the public website, which means that at least we need 
to generate self-signed certificates.

For starters, create a new directory on the root of the repo named "self-certs". ::

    mkdir self-certs


Next run this command to generate the certificate::

    openssl req -new -newkey rsa:4096 -days 365 -nodes -x509 -keyout self-certs/key.pem -out self-certs/cert.pem

Finally run another command to generate the 
`Diffie-Hellman <https://en.wikipedia.org/wiki/Diffie%E2%80%93Hellman_key_exchange>`_ 
coefficients to improve security::

    openssl dhparam -out /path/to/dhparam.pem 4096


In the end you should have three files inside the "self-certs" 
directory, ``key.pem``, ``cert.pem`` and ``dhparam.pem``.


.. Docker-compose configurations
.. -----------------------------

 
.. Next you need to add sensitive data to your docker-compose.yaml file, such as usernames, passwords for the **Postgres** and **Virtuoso** services. ::

..     postgres_compose:
..     image: postgres:10
..     container_name: "postgres"
..     # Setup the username, password, and database name.
..     environment:
..         - POSTGRES_USER=[USER]
..         - POSTGRES_PASSWORD=[PASSWORD]
..         - POSTGRES_DB=ref_ns_sec

    
..     virtuoso:
..     image: openlink/virtuoso-opensource-7:7.2
..     container_name: virtuoso
..     environment:
..         #- SPARQL_UPDATE=true
..         - VIRTUOSO_DB_USER=[USER]
..         - VIRTUOSO_DB_PASSWORD=[PASSWORD]
..         - DEFAULT_GRAPH=http://localhost:8890/chewiens
..         - DBA_PASSWORD=[DBA_PASSWORD]
..         - DAV_PASSWORD=[DAV_PASSWORD]


Build Chewie-NS
---------------

.. important:: Make sure that the ports (HOST:CONTAINER) specified in the docker-compose services are not being currently used by other applications! If they are, docker-compose will not be able to build Chewie-NS. To solve this issue, map the HOST port to an available port.


After completing the previous steps, you only need to run this command::

    docker-compose up --build

Docker-compose will create all the necessary containers and images and will orchestrate them to build a local instance of Chewie-NS, available by default in your local host.

