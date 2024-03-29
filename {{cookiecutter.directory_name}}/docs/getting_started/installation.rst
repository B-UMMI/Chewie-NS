Installation
============
While you have access to public schemas at `chewbbaca.online <https://chewbbaca.online/>`_,
you may want to setup a private instance of Chewie-NS.
The deployment of local instances can be easily achieved through the
use of `Docker Compose <https://docs.docker.com/compose/>`_.

Chewie-NS is available on `Github <https://github.com/B-UMMI/Chewie-NS>`_. You will also need a container engine (see `Container engine`_ below)

Container engine
----------------

All components of Chewie-NS are executed in `docker`_ containers and are orchestrated by `docker-compose`_.

Docker
::::::

Docker can be installed following the instructions on the website: https://www.docker.com/community-edition#/download.
To run docker as a non-root user, you will need to follow the instructions on the website: https://docs.docker.com/install/linux/linux-postinstall/#manage-docker-as-a-non-root-user.


Docker-compose
::::::::::::::

To install docker-compose, you need to have installed docker beforehand. 
The installation instructions for Docker-compose can be found `here <https://docs.docker.com/compose/install/>`_.

Cookiecutter installation
-------------------------

Chewie-NS has a `cookiecutter <https://github.com/cookiecutter/cookiecutter>`_ template that will perform the installation
of a local server by automatically modifying some files.

Quickstart
::::::::::

Start by installing the latest cookiecutter version:

::

    pip install cookiecutter


Then, in the directory where you want to create your local server, run:

::

    cookiecutter https://github.com/B-UMMI/Chewie-NS.git


Input variables
:::::::::::::::

Chewie-NS cookiecutter has default input variables defined to create a local installation of Chewie-NS. The values can be changed by the user if necessary.
To use the default values, simply press Enter.

The input variables are:

- `directory_name`: The name of the directory where the server will be created.
- `flask_app_local_port`: Local port for the Flask backend API.
- `flask_email`: The email address that sends the reset token to recover a forgotten password.
- `flask_email_password`: The password of the email address that will send the reset token.
- `flask_email_default_sender`: The email address of the reset token sender.
- `flask_email_server`: The server of the email address.
- `flask_email_port`: The port of the email server.
- `flask_email_use_tls`: Use TLS.
- `flask_email_use_ssl`: Use SSL.
- `base_url`: The base URL that will be used for the communication between the backend and frontend.
- `postgres_local_port`: Local port of the PostgreSQL database.
- `pgadmin_email`: PGAdmin email, to log into the PGAdmin interface.
- `pgadmin_password`: PGAdmin user password.
- `pgadmin_local_port`: Local port of PGAdmin.
- `virtuoso_local_port`: Local port of the Virtuoso triple store database.
- `virtuoso_isql_local_port`: Local port for Virtuoso's ISQL.
- `redis_local_port`: Local port of Redis queuing system.
- `flower_local_port`: Local port of Flower, a dashboard to monitor Celery jobs.
- `gunicorn_workers`: Number of workers `gunicorn <https://gunicorn.org/>`_ will use to deploy the backend of the server.
- `gunicorn_threads`: Number of threads `gunicorn <https://gunicorn.org/>`_ will use to deploy the backend of the server.
- `local_schema_stats_url`: The URL for the Available Schemas page of the local server.
- `local_register_url`: The URL for the user registration page of the local server.
- `local_species_url`: The URL for a particular species' page.
- `api_url`: The URL for the Swagger documentation of the backend API.

After defining the input variables, cookiecutter will create the necessary self-signed certificates for the server to work.

After executing cookiecutter, you can build the local instance of Chewie-NS with the following command:

::

    docker-compose -f docker-compose-production.yaml up --build


Launch the Chewie-NS app by accessing `127.0.0.1 <https://127.0.0.1>`_ on your browser. This link will take you to the Home page of your local instance of Chewie-NS.


Manual Installation
-------------------

In order to install and build Chewie-NS locally, the following files need to be modified:

- `Docker compose configuration file <https://github.com/B-UMMI/Chewie-NS/blob/master/%7B%7Bcookiecutter.directory_name%7D%7D/docker-compose-production.yaml>`_
- `NS API Dockerfile <https://github.com/B-UMMI/Chewie-NS/blob/master/%7B%7Bcookiecutter.directory_name%7D%7D/Dockerfile>`_
- `NGINX configuration file <https://github.com/B-UMMI/Chewie-NS/blob/master/%7B%7Bcookiecutter.directory_name%7D%7D/frontend_react/chewie_ns/nginx.conf>`_
- `Axios configuration file <https://github.com/B-UMMI/Chewie-NS/blob/master/%7B%7Bcookiecutter.directory_name%7D%7D/frontend_react/chewie_ns/src/axios-backend.js>`_
- `Frontend Left Menu Component API URL <https://github.com/B-UMMI/Chewie-NS/blob/master/%7B%7Bcookiecutter.directory_name%7D%7D/frontend_react/chewie_ns/src/components/Navigation/MuiSideDrawer/MuiSideDrawer.js>`_

Docker compose configuration file
---------------------------------

In this file the **BASE_URL** variable needs to be changed to your localhost in the **flask_app** and the **periodic_worker** services.

::

    environment:
      - FLASK_ENV=development
      - BASE_URL=http://127.0.0.1:5000/NS/api/


The port 80 from the **nginx_react** service needs to be commented out because only the 443 port will be used.

::

    ports:
      # - "80:80"
      - "443:443"


A username and password need to be provided to the `pgadmin4 service <https://github.com/B-UMMI/Chewie-NS/blob/612fad1edfd0691e30b3fa878d7b13bfb9f3eb97/docker-compose-production.yaml#L51>`_.

::

    environment:
        PGADMIN_DEFAULT_EMAIL: "test@email.com"
        PGADMIN_DEFAULT_PASSWORD: "testpassword"

NS API Dockerfile
-----------------

In this Dockerfile, the number of **workers** and **threads** provided to the *gunicorn* command should be adequate to your machines resources.
An example command could be: ::

    CMD ["gunicorn", "--worker-tmp-dir", "/dev/shm", "-w", "4", "--threads=2", "--worker-class=gthread", "-b", "0.0.0.0:5000", "wsgi:app"]

NGINX configuration file
------------------------

The NGINX configuration file has been written to work on a server that requires the use of port 80 (HTTP) and 443 (HTTPS).
On a local instance, we recomend that Chewie-NS only runs on port 443 (HTTPS), so the server block code must commented out or deleted.

::

    #server {
    #    listen 80;
    #    server_name chewbbaca.online;
    #
    #    location ^~ /.well-known {
    #      allow all;
    #      root  /data/letsencrypt/;
    #    }
    #
    #    location / {
    #        return 301 https://chewbbaca.online$request_uri;
    #    }
    #


The code block that perform the redirection to the server name should also be commented out to avoid redirection to the main instance of Chewie-NS.

::

    # Redirect IP to Server Name
    # server {
        
    #     listen 443 ssl http2;
    
    #     # SSL certificates
    #     #ssl_certificate /etc/nginx/certs/cert.pem;
    #     #ssl_certificate_key /etc/nginx/certs/key.pem;
    
    #     # Letsencrypt certficates
    #     ssl_certificate /etc/letsencrypt/live/chewbbaca.online/fullchain.pem;
    #     ssl_certificate_key /etc/letsencrypt/live/chewbbaca.online/privkey.pem;
    
    #     server_name 194.210.120.209;
    
    #     return 301 $scheme://chewbbaca.online$request_uri;
    
    # }

The **server_name** on the 443 server block should also be commented out.

::

    #server_name chewbbaca.online;

We also recomend that the certificates should be self-signed, therefore, the block of code related to the path of the self-signed 
certificates should uncommented and the Lets Encrypt code block sohuld be deleted.

More information about the creation of the self-signed certifcates below.

::

    # SSL self-signed certificates
    ssl_certificate /etc/nginx/certs/cert.pem;
    ssl_certificate_key /etc/nginx/certs/key.pem;

    # Letsencrypt certficates
    # ssl_certificate /etc/letsencrypt/live/chewbbaca.online/fullchain.pem;
    # ssl_certificate_key /etc/letsencrypt/live/chewbbaca.online/privkey.pem;

Finally, the last server block that redirects the IP to the domain name should be commented to avoid redirects to the main Chewie-NS website.

Axios configuration file
------------------------

`Axios <https://github.com/axios/axios>`_ is a Promise based HTTP client that is used to perform requests to Chewie-NS' API.

The URL of the API on the `Axios configuration file <https://github.com/B-UMMI/Chewie-NS/blob/master/%7B%7Bcookiecutter.directory_name%7D%7D/frontend_react/chewie_ns/src/axios-backend.js>`_ 
needs to be changed to the localhost API in order to perform requests to the local instance of Chewie-NS. ::

    const instance = axios.create({
    baseURL: "http://127.0.0.1:5000/NS/api/",
    headers: { "Content-Type": "application/json" },
    });

Frontend Left Menu Component API URL
------------------------------------

The `left menu <https://github.com/B-UMMI/Chewie-NS/blob/93063e3534cca77820bbd3490fa4445d41769f94/frontend_react/chewie_ns/src/components/Navigation/MuiSideDrawer/MuiSideDrawer.js#L225>`_ of Chewie-NS' user interface contains a button that redirects the user to the Swagger interface, in order to interact with the API.
The URL needs to be changed to the localhost.

::

    <ListItem
        button
        component="a"
        href={"https://127.0.0.1/NS/api/docs"}
        target={"_blank"}
        rel="noopener noreferrer"


Homepage description
--------------------

The `homepage description markdown <https://github.com/B-UMMI/Chewie-NS/blob/master/%7B%7Bcookiecutter.directory_name%7D%7D/frontend_react/chewie_ns/src/components/data/chewie.js>`_ of Chewie-NS has links to the main instance which need to be changed to the **localhost**.

::

    |[Click here to see the Available Schemas](https://127.0.0.1/stats)|

    ## Schema submission
    If you wish to submit schemas to Chewie-NS you need to register first at the [Register](https://127.0.0.1/register) page.


Create self-signed certificates
-------------------------------

A local instance of Chewie-NS will have `SSL <https://www.ssl.com/faqs/faq-what-is-ssl/>`_ 
support, just like the public website, which means that at least we need 
to generate self-signed certificates.

For starters, create a new directory on the root of the repo named "self_certs". ::

    mkdir self_certs

Next run this command to generate the certificate::

    openssl req -new -newkey rsa:4096 -days 365 -nodes -x509 -keyout self_certs/key.pem -out self_certs/cert.pem

Finally run another command to generate the 
`Diffie-Hellman <https://en.wikipedia.org/wiki/Diffie%E2%80%93Hellman_key_exchange>`_ 
coefficients to improve security::

    openssl dhparam -out self_certs/dhparam.pem 4096


In the end you should have three files inside the "self-certs" 
directory, ``key.pem``, ``cert.pem`` and ``dhparam.pem``.

Build Chewie-NS
---------------

.. important::
    Make sure that the ports (HOST:CONTAINER) specified in the docker-compose services are not being currently used by other applications!
    If they are, docker-compose will not be able to build Chewie-NS. To solve this issue, map the HOST port to an available port.

After completing the previous steps, you only need to run this command

::

    docker-compose -f docker-compose-production.yaml up --build

Docker-compose will create all the necessary containers and images and will orchestrate them to build a local instance of Chewie-NS, available by
default in your localhost.

Launch the NS app by accessing `127.0.0.1 <https://127.0.0.1>`_ on your browser. This link will take you to the Home page of your local instance of Chewie-NS.
