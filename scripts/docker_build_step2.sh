#!/bin/bash

npm run build

export SECRET_KEY=abcd
python /app/manage.py collectstatic --noinput

# Save space by deleting unnecessary content
rm -rf /root/.cache
rm -rf /app/node_modules/
rm -rf /app/assets/
rm -rf /app/dist/
