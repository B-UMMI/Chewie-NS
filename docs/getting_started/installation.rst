Installation
============
While you can access public repositories at `chewBBACA.online <https://chewBBACA.online>`_,
you may want to setup a private instance of Chewie-NS.
The deployment of local instances of Chewie-NS can be easily achieved through the
use of Docker Compose.

Chewie-NS is available for cloning from its Github 
`repository <https://github.com/B-UMMI/Chewie-NS>`_. ::

    git clone https://github.com/B-UMMI/Chewie-NS.git

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

File modifications
------------------

In order to install and build Chewie-NS locally the following files need to be modified:

- `Docker compose configuration file <https://github.com/B-UMMI/Chewie-NS/blob/master/docker-compose-production.yaml>`_
- `NS API Dockerfile <https://github.com/B-UMMI/Chewie-NS/blob/master/Dockerfile>`_
- `NGINX configuration file <https://github.com/B-UMMI/Chewie-NS/blob/master/frontend_react/chewie_ns/nginx.conf)>`_
- `Axios configuration file <https://github.com/B-UMMI/Chewie-NS/blob/master/frontend_react/chewie_ns/src/axios-backend.js>`_
- `Frontend Left Menu Component API URL <https://github.com/B-UMMI/Chewie-NS/blob/master/frontend_react/chewie_ns/src/components/Navigation/MuiSideDrawer/MuiSideDrawer.js>`_

Docker compose configuration file
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In this file the **BASE_URL** variable needs to be changed to your localhost. ::

    environment:
      - FLASK_ENV=development
      - BASE_URL=http://127.0.0.1:5000/NS/api/

### NS API Dockerfile

In this Dockerfile, the number of **workers** and **threads** provided to the *gunicorn* command should be adequate to your machines resources.
An example command could be: ::

    CMD ["gunicorn", "--worker-tmp-dir", "/dev/shm", "-w", "4", "--threads=2", "--worker-class=gthread", "-b", "0.0.0.0:5000", "wsgi:app"]

NGINX configuration file
^^^^^^^^^^^^^^^^^^^^^^^^

The NGINX configuration file has been written to work on a server that requires the use of port 80 (HTTP) and 443 (HTTPS).
On a local instance, we recomend that Chewie-NS only runs on port 443 (HTTPS), so the server block code must commented out or deleted. ::

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
    #}

The **server_name** on the 443 server block should also be commented out. ::

    #server_name chewbbaca.online;

We also recomend that the certificates should be self-signed, therefore, the block of code related to the path of the self-signed 
certificates should uncommented and the Lets Encrypt code block sohuld be deleted.

More information about the creation of the self-signed certifcates below. ::

    # SSL self-signed certificates
    ssl_certificate /etc/nginx/certs/cert.pem;
    ssl_certificate_key /etc/nginx/certs/key.pem;

Finally, the last server block that redirects the IP to the domain name should be commented to avoid redirects to the main Chewie-NS website.

Axios configuration file
^^^^^^^^^^^^^^^^^^^^^^^^

`Axios <https://github.com/axios/axios>`_ is a Promise based HTTP client that is used to perform requests to Chewie-NS' API.

The URL of the API on the `Axios configuration file <https://github.com/B-UMMI/Chewie-NS/blob/master/frontend_react/chewie_ns/src/axios-backend.js>`_ 
needs to be changed to the localhost API in order to perform requests to the local instance of Chewie-NS. ::

    const instance = axios.create({
    baseURL: "http://127.0.0.1:5000/NS/api/",
    headers: { "Content-Type": "application/json" },
    });

Frontend Left Menu Component API URL
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The left menu of Chewie-NS' user interface contains a button that redirects the user to the Swagger interface, in order to interact with the API.
The URL needs to be changed to the localhost.

    <ListItem
        button
        component="a"
        href={"https://127.0.0.1/NS/api/docs"}
        target={"_blank"}
        rel="noopener noreferrer"
    >

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

.. important:: Make sure that the ports (HOST:CONTAINER) specified in the docker-compose services are not being currently used by other applications!
If they are, docker-compose will not be able to build Chewie-NS. To solve this issue, map the HOST port to an available port.


After completing the previous steps, you only need to run this command::

    docker-compose up -f docker-compose-production.yaml --build

Docker-compose will create all the necessary containers and images and will orchestrate them to build a local instance of Chewie-NS, available by
default in your localhost.

Launch the NS app by accessing `127.0.0.1 <https://127.0.0.1>`_ on your browser. This link will take you to the Home page of your local instance of Chewie-NS.
