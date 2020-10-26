# Chewie-NS :whale2: :package:

[![Documentation Status](https://readthedocs.org/projects/chewie-ns/badge/?version=latest)](https://chewie-ns.readthedocs.io/en/latest/?badge=latest)
[![DOI:10.1093/nar/gkaa889](https://img.shields.io/badge/DOI-10.1093%2Fnar%2Fgkaa889-blue)](https://academic.oup.com/nar/advance-article/doi/10.1093/nar/gkaa889/5929238)
[![License: GPL v3](https://img.shields.io/github/license/B-UMMI/Chewie-NS)](https://www.gnu.org/licenses/gpl-3.0)

Docker-compose for the [Nomenclature Server](https://github.com/B-UMMI/Nomenclature_Server) webapp.
It uses the following docker images:

- postgres: `postgres:10`
- virtuoso: `openlink/virtuoso-opensource-7:7.2.6-r3-g1b16668`
- redis: `redis:5.0.6`
- nginx: `nginx:1.17`
- node: `node:13`
- NS API: [this dockerfile](https://github.com/B-UMMI/Chewie-NS/blob/master/Dockerfile)
- NS UI: [this dockerfile](https://github.com/B-UMMI/Chewie-NS/blob/master/frontend_react/chewie_ns/Dockerfile.prod)

## Chewie-NS Documentation

Chewie-NS has all its documentations available at [Chewie-NS' Read The Docs](https://chewie-ns.readthedocs.io/en/latest/).

## Local installation

To start a local instance of Chewie-NS the following files must be modified:

- [Docker compose configuration file](https://github.com/B-UMMI/Chewie-NS/blob/master/docker-compose-production.yaml)
- [NS API Dockerfile](https://github.com/B-UMMI/Chewie-NS/blob/master/Dockerfile)
- [NGINX configuration file](https://github.com/B-UMMI/Chewie-NS/blob/master/frontend_react/chewie_ns/nginx.conf)
- [Axios configuration file](https://github.com/B-UMMI/Chewie-NS/blob/master/frontend_react/chewie_ns/src/axios-backend.js)
- [Frontend Left Menu Component API URL](https://github.com/B-UMMI/Chewie-NS/blob/master/frontend_react/chewie_ns/src/components/Navigation/MuiSideDrawer/MuiSideDrawer.js)

### Docker compose configuration file

In this file the **BASE_URL** variable needs to be changed to your localhost.

```yaml
environment:
  - FLASK_ENV=development
  - BASE_URL=http://127.0.0.1:5000/NS/api/
```

### NS API Dockerfile

In this Dockerfile, the number of **workers** and **threads** provided to the _gunicorn_ command should be adequate to your machines resources.
An example command could be:

```dockerfile
CMD ["gunicorn", "--worker-tmp-dir", "/dev/shm", "-w", "4", "--threads=2", "--worker-class=gthread", "-b", "0.0.0.0:5000", "wsgi:app"]
```

### NGINX configuration file

The NGINX configuration file has been written to work on a server that requires the use of port 80 (HTTP) and 443 (HTTPS).
On a local instance, we recomend that Chewie-NS only runs on port 443 (HTTPS), so the server block code must commented out or deleted.

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

The **server_name** on the 443 server block should also be commented out.

```nginx
#server_name chewbbaca.online;
```

We also recomend that the certificates should be self-signed, therefore, the block of code related to the path of the self-signed certificates should uncommented and the Lets Encrypt code block sohuld be deleted.

More information about the creation of the self-signed certifcates below.

```nginx
# SSL self-signed certificates
ssl_certificate /etc/nginx/certs/cert.pem;
ssl_certificate_key /etc/nginx/certs/key.pem;
```

Finally, the last server block that redirects the IP to the domain name should be commented to avoid redirects to the main Chewie-NS website.

### Axios configuration file

[Axios](https://github.com/axios/axios) is a Promise based HTTP client that is used to perform requests to Chewie-NS' API.

The URL of the API on the [Axios configuration file](https://github.com/B-UMMI/Chewie-NS/blob/master/frontend_react/chewie_ns/src/axios-backend.js) needs to be changed to the localhost API in order to perform requests to the local instance of Chewie-NS.

```js
const instance = axios.create({
  baseURL: "http://127.0.0.1:5000/NS/api/",
  headers: { "Content-Type": "application/json" },
});
```

### Frontend Menu Component API URL

The left menu of Chewie-NS' user interface contains a button that redirects the user to the Swagger interface, in order to interact with the API.
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

### Creating the self-signed certificates

For starters, create a new directory on the root of the repo named “self_certs”.

```bash
mkdir self_certs
```

Next run this command to generate the certificate:

```bash
openssl req -new -newkey rsa:4096 -days 365 -nodes -x509 -keyout self_certs/key.pem -out self_certs/cert.pem
```

Finally run another command to generate the [Diffie-Hellman](https://en.wikipedia.org/wiki/Diffie%E2%80%93Hellman_key_exchange) coefficients to improve security:

```bash
openssl dhparam -out self_certs/dhparam.pem 4096
```

In the end you should have three files inside the “self_certs” directory, **key.pem**, **cert.pem** and **dhparam.pem**.

### Starting the compose

To build your local instance of Chewie-NS rrun this command:

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

Make sure that these ports or your localhost are not already in use by other services!
More info available [here](https://www.cyberciti.biz/faq/unix-linux-check-if-port-is-in-use-command/).

## Contacts

- Chewie-NS development team (imm-bioinfo@medicina.ulisboa.pt)

## Citation

If you use **Chewie-NS**, please cite: 

Mamede, R., Vila-Cerqueira, P., Silva, M., Carriço, J. A., & Ramirez, M. (2020). Chewie Nomenclature Server (chewie-NS): a deployable nomenclature server for easy sharing of core and whole genome MLST schemas. Nucleic Acids Research.

Available from: https://academic.oup.com/nar/advance-article/doi/10.1093/nar/gkaa889/5929238