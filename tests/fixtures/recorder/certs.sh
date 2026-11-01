#!/bin/sh
# Mint a one-run CA and a server certificate for HOST into /certs.
#
# The bw CLI refuses any server URL that is not https (its isDev() is fixed
# false in release builds), so the throwaway Vaultwarden serves TLS. Only
# the bw container trusts this CA, through NODE_EXTRA_CA_CERTS; nothing
# reaches a system trust store, and the volume holding it dies with the run.

set -eu

host=$1

cd /certs

openssl req -x509 -newkey rsa:2048 -nodes -days 1 -subj "/CN=bw-recorder CA" \
  -keyout ca.key -out ca.crt 2> /dev/null

openssl req -newkey rsa:2048 -nodes -subj "/CN=$host" \
  -keyout server.key -out server.csr 2> /dev/null

printf 'subjectAltName=DNS:%s\n' "$host" > san.ext

openssl x509 -req -in server.csr -CA ca.crt -CAkey ca.key -CAcreateserial \
  -days 1 -extfile san.ext -out server.crt 2> /dev/null

chmod 644 ca.crt server.crt
