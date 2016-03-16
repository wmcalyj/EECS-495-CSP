#!/bin/bash
mkdir logs
mkdir js_repository
mkdir certs
openssl req -new -x509 -keyout ./certs/key.pem -out ./certs/cert.pem -days 365 -nodes
sudo npm install --save express
sudo npm install --save morgan
sudo npm install --save cors
sudo npm install --save formidable
sudo npm install --save body-parser
sudo npm install --save base-64
