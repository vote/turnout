#!/bin/bash

curl -sL https://deb.nodesource.com/setup_12.x | bash -
apt-get install -y nodejs

pip install -r requirements.txt
npm install

# Save space by deleting unnecessary content
rm -rf /root/.cache
apt-get clean
