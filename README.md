# CAZM-Admin-Dashboard
Administrator dashboard for the HB-CAZM senior design project. This dashboard allows administrators to view, edit, and sync the available courses as well as view student schedule entries.

- [CAZM-Admin-Dashboard](#cazm-admin-dashboard)
- [Installation](#installation)
- [Setup](#setup)
- [Running](#running)

# Installation

Downloading the project from GitHub.
```
git clone https://github.com/redParrot17/CAZM-Admin-Dashboard.git
```

# Setup

Setting up the GitHub clone to be able to run.
```
cd CAZM-Admin-Dashboard
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
```

Generating the certificates.
```
openssl genrsa -des3 -out server.key 2048
openssl req -new -key server.key -out server.csr
cp server.key server.key.org
openssl rsa -in server.key.org -out server.key
openssl x509 -req -days 365 -in server.csr -signkey server.key -out server.crt
rm server.csr
rm server.key.org
```

Creating and editing the `.env` file.
```
touch .env
nano .env
```
```
FLASK_APP=server.py
FLASK_RUN_HOST=0.0.0.0
FLASK_RUN_PORT=5005
FLASK_RUN_CERT=server.crt
FLASK_RUN_KEY=server.key
```
> The above is what should be typed in the `.env` file.

Save the new `.env` file with `Ctrl+O` + `Enter` + `Ctrl+X`

Likewise create the `mysql.cnf` file and include the appropriate values so the server can connect to the database.

```
[client]
host=
user=
password=
database=
```

# Running

Navigate to the project directory if you haven't already.
```
cd CAZM-Admin-Dashboard
```

Activate the virtual-environment if you haven't already.
```
source venv/bin/activate
```

Start the web-server.
```
flask run
```