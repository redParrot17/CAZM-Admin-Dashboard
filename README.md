# CAZM-Admin-Dashboard
Administrator dashboard for the HB-CAZM senior design project.

## Setup

> Start in the project root directory.

### Setting up certificate

1. Generate a private key `openssl genrsa -des3 -out server.key 1024`
2. Generate a CSR `openssl req -new -key server.key -out server.csr`
3. Remove Passphrase from key `cp server.key server.key.org` then `openssl rsa -in server.key.org -out server.key`
4. Generate self signed certificate `openssl x509 -req -days 365 -in server.csr -signkey server.key -out server.crt`

### Windows

1. python3 -m venv venv
2. venv\Scripts\activate
3. set FLASK_APP=server.py
4. pip install -r requirements.txt
5. flask run

### Unix

1. python3 -m venv venv
2. source venv/bin/activate
3. export FLASK_APP=server.py
4. export FLASK_RUN_PORT=5005
5. export FLASK_RUN_HOST=0.0.0.0
6. pip3 install -r requirements.txt
7. flask run --host 0.0.0.0 --port 5005

### Env Variables

- FLASK_APP=server.py
- FLASK_RUN_PORT=5005
- FLASK_RUN_HOST=0.0.0.0
- FLASK_RUN_CERT=server.crt
- FLASK_RUN_KEY=server.key