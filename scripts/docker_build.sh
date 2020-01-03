#!/bin/bash

curl -sL https://deb.nodesource.com/setup_12.x | bash -
apt-get install -y nodejs

pip install -r requirements.txt
npm install
npm run build

export SECRET_KEY=abcd
python /app/manage.py collectstatic --noinput

# Save space by deleting unnecessary content
rm -rf /root/.cache
rm -rf /app/node_modules/
rm -rf /app/assets/
rm -rf /app/dist/
apt-get clean
