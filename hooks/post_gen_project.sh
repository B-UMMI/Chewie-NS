#!/bin/bash

#### Creating the self-signed certificates.

# Create a new directory on the root of the repo named “self_certs”.
mkdir self_certs

# Generate the certificate
openssl req -new -newkey rsa:4096 -days 365 -nodes -x509 -keyout self_certs/key.pem -out self_certs/cert.pem

# Generate the Diffie-Hellman coefficients to improve security.
openssl dhparam -out self_certs/dhparam.pem 4096
