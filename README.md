# Chewie-NS :whale2: :package: :cookie:

[![Documentation Status](https://readthedocs.org/projects/chewie-ns/badge/?version=latest)](https://chewie-ns.readthedocs.io/en/latest/?badge=latest)
[![DOI:10.1093/nar/gkaa889](https://img.shields.io/badge/DOI-10.1093%2Fnar%2Fgkaa889-blue)](https://academic.oup.com/nar/advance-article/doi/10.1093/nar/gkaa889/5929238)
[![License: GPL v3](https://img.shields.io/github/license/B-UMMI/Chewie-NS)](https://www.gnu.org/licenses/gpl-3.0)

Docker-compose for the Chewie-NS webapp. The main instance of Chewie-NS is available at [chewbbaca.online](https://chewbbaca.online/).

Chewie-NS uses the following docker images:

- postgres: `postgres:10`
- virtuoso: `openlink/virtuoso-opensource-7:7.2.6-r3-g1b16668`
- redis: `redis:5.0.6`
- nginx: `nginx:1.17`
- node: `node:13`
- NS API: [this dockerfile](https://github.com/B-UMMI/Chewie-NS/blob/master/%7B%7Bcookiecutter.directory_name%7D%7D/Dockerfile)
- NS UI: [this dockerfile](https://github.com/B-UMMI/Chewie-NS/blob/master/%7B%7Bcookiecutter.directory_name%7D%7D/frontend_react/chewie_ns/Dockerfile.prod)

## Chewie-NS Documentation

Chewie-NS has all its documentation available at [Chewie-NS' Read The Docs](https://chewie-ns.readthedocs.io/en/latest/).

## Local installation

### Cookiecutter installation

Chewie-NS has a [cookiecutter](https://github.com/cookiecutter/cookiecutter) template that will perform the installation
of a local server by automatically modifying some files.

#### Quickstart

Start by installing the latest cookiecutter version:

```bash
pip install cookiecutter
```

Then, in the directory where you want to create your local server, run:

```bash
cookiecutter https://github.com/B-UMMI/Chewie-NS.git
```

#### Input variables

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
- `gunicorn_workers`: Number of workers [gunicorn](https://gunicorn.org/) will use to deploy the backend of the server.
- `gunicorn_threads`: Number of threads [gunicorn](https://gunicorn.org/) will use to deploy the backend of the server.
- `local_schema_stats_url`: The URL for the Available Schemas page of the local server.
- `local_register_url`: The URL for the user registration page of the local server.
- `local_species_url`: The URL for a particular species' page.
- `api_url`: The URL for the Swagger documentation of the backend API.

After defining the input variables, cookiecutter will create the necessary self-signed certificates for the server to work.

After executing cookiecutter, you can build the local instance of Chewie-NS with the following command:

```bash
docker-compose -f docker-compose-production.yaml up --build
```

Launch the Chewie-NS app by accessing [127.0.0.1](https://127.0.0.1) on your browser. This link will take you to the Home page of your local instance of Chewie-NS.

### Manual installation

To start a local instance of Chewie-NS, the following files must be modified:

- [Docker compose configuration file](https://github.com/B-UMMI/Chewie-NS/blob/master/%7B%7Bcookiecutter.directory_name%7D%7D/docker-compose-production.yaml)
- [NS API Dockerfile](https://github.com/B-UMMI/Chewie-NS/blob/master/%7B%7Bcookiecutter.directory_name%7D%7D/Dockerfile)
- [NGINX configuration file](https://github.com/B-UMMI/Chewie-NS/blob/master/%7B%7Bcookiecutter.directory_name%7D%7D/frontend_react/chewie_ns/nginx.conf)
- [Axios configuration file](https://github.com/B-UMMI/Chewie-NS/blob/master/%7B%7Bcookiecutter.directory_name%7D%7D/frontend_react/chewie_ns/src/axios-backend.js)
- [Frontend Left Menu Component API URL](https://github.com/B-UMMI/Chewie-NS/blob/master/%7B%7Bcookiecutter.directory_name%7D%7D/frontend_react/chewie_ns/src/components/Navigation/MuiSideDrawer/MuiSideDrawer.js)

### Docker compose configuration file

In [this file](https://github.com/B-UMMI/Chewie-NS/blob/9f5871b88672cb7f7819a0cf80b987abf2bb55dc/docker-compose-production.yaml#L19), the **BASE_URL** variable needs to be changed to your localhost in the `flask_app` and the `periodic_worker` services.

```yaml
environment:
  - BASE_URL=http://127.0.0.1:5000/NS/api/
```

The port 80 from the `nginx_react` service needs to be commented out because only port 443 will be used.

```yaml
ports:
  # - "80:80"
  - "443:443"

```

A username and password need to be provided to the [pgadmin4 service](https://github.com/B-UMMI/Chewie-NS/blob/612fad1edfd0691e30b3fa878d7b13bfb9f3eb97/docker-compose-production.yaml#L51).

```yaml
environment:
  PGADMIN_DEFAULT_EMAIL: "test@email.com"
  PGADMIN_DEFAULT_PASSWORD: "testpassword"
```

### NS API Dockerfile

In [this Dockerfile](https://github.com/B-UMMI/Chewie-NS/blob/9f5871b88672cb7f7819a0cf80b987abf2bb55dc/Dockerfile#L31), the number of **workers** and **threads** provided to the _gunicorn_ command should be adequate to your machines resources.
An example command could be:

```dockerfile
CMD ["gunicorn", "--worker-tmp-dir", "/dev/shm", "-w", "4", "--threads=2", "--worker-class=gthread", "-b", "0.0.0.0:5000", "wsgi:app"]
```

### NGINX configuration file

The NGINX configuration file has been written to work on a server that uses ports 80 (HTTP) and 443 (HTTPS).
On a local instance, we recommend that Chewie-NS only runs on port 443 (HTTPS), so the server block code must be commented out or deleted.

```nginx
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
```

The code block that performs the redirection to the server name should also be commented out to avoid redirection to the main instance of Chewie-NS.

```nginx
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
```

The **server_name** on the 443 server block should also be commented out.

```nginx
#server_name chewbbaca.online;
```

We also recommend that the certificates be self-signed. Therefore, the block of code related to the path of the self-signed certificates should be uncommented and the [Lets Encrypt](https://letsencrypt.org/) code block should be deleted.

More information about the creation of the self-signed certificates is below.

```nginx
# SSL self-signed certificates
ssl_certificate /etc/nginx/certs/cert.pem;
ssl_certificate_key /etc/nginx/certs/key.pem;

# Letsencrypt certficates
# ssl_certificate /etc/letsencrypt/live/chewbbaca.online/fullchain.pem;
# ssl_certificate_key /etc/letsencrypt/live/chewbbaca.online/privkey.pem;
```

Finally, the last server block that redirects the IP to the domain name should be commented to avoid redirects to the main Chewie-NS website.

### Axios configuration file

[Axios](https://github.com/axios/axios) is a promise-based HTTP client that is used to perform requests to Chewie-NS' API.

The URL of the API on the [Axios configuration file](https://github.com/B-UMMI/Chewie-NS/blob/master/%7B%7Bcookiecutter.directory_name%7D%7D/frontend_react/chewie_ns/src/axios-backend.js) needs to be changed to the localhost API in order to perform requests to the local instance of Chewie-NS.

```js
const instance = axios.create({
  baseURL: "http://127.0.0.1:5000/NS/api/",
  headers: { "Content-Type": "application/json" },
});
```

### Frontend Menu Component API URL

The [left menu](https://github.com/B-UMMI/Chewie-NS/blob/93063e3534cca77820bbd3490fa4445d41769f94/frontend_react/chewie_ns/src/components/Navigation/MuiSideDrawer/MuiSideDrawer.js#L225) of Chewie-NS' user interface contains a button that redirects the user to the Swagger interface, in order to interact with the API.
The URL needs to be changed to the localhost.

```js
<ListItem
    button
    component="a"
    href={"https://127.0.0.1/NS/api/docs"}
    target={"_blank"}
    rel="noopener noreferrer"
>
```

### Homepage description

The [homepage description markdown](https://github.com/B-UMMI/Chewie-NS/blob/master/%7B%7Bcookiecutter.directory_name%7D%7D/frontend_react/chewie_ns/src/components/data/chewie.js) of Chewie-NS has links to the main instance which need to be changed to the localhost.

```md
|[Click here to see the Available Schemas](https://127.0.0.1/stats)|


## Schema submission
If you wish to submit schemas to Chewie-NS you need to register first at the [Register](https://127.0.0.1/register) page.
```

### Creating the self-signed certificates

For starters, create a new directory on the root of the repo named “self_certs”.

```bash
mkdir self_certs
```

Next, run this command to generate the certificate:

```bash
openssl req -new -newkey rsa:4096 -days 365 -nodes -x509 -keyout self_certs/key.pem -out self_certs/cert.pem
```

Finally, run a command to generate the [Diffie-Hellman](https://en.wikipedia.org/wiki/Diffie%E2%80%93Hellman_key_exchange) coefficients to improve security:

```bash
openssl dhparam -out self_certs/dhparam.pem 4096
```

In the end, you should have three files inside the “self_certs” directory, **key.pem**, **cert.pem** and **dhparam.pem**.

### Starting the compose

To build your local instance of Chewie-NS, run the following command:

```bash
docker-compose -f docker-compose-production.yaml up --build
```

Launch the NS app by accessing [127.0.0.1](https://127.0.0.1) on your browser. This link will take you to the Home page of your local instance of Chewie-NS.

The default user's credentials are the following:

```py
username = test@refns.com
password = mega_secret
```

## Notes

Make sure that the necessary ports are not already in use by other services!
More info is available [here](https://www.cyberciti.biz/faq/unix-linux-check-if-port-is-in-use-command/).

## Contacts

- Chewie-NS development team (imm-bioinfo@medicina.ulisboa.pt)

## Citation

If you use **Chewie-NS**, please cite: 

> Mamede, R., Vila-Cerqueira, P., Silva, M., Carriço, J. A., & Ramirez, M. (2020). Chewie Nomenclature Server (chewie-NS): a deployable nomenclature server for easy sharing of core and whole genome MLST schemas. Nucleic Acids Research.

Available from: https://academic.oup.com/nar/advance-article/doi/10.1093/nar/gkaa889/5929238
