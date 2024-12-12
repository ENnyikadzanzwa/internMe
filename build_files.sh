#!/bin/bash


python3 -m pip install --upgrade pip             # Upgrade pip
pip3 install -r requirements.txt                 # Install dependencies
python3 manage.py collectstatic --noinput        # Collect static files
python3 manage.py migrate                        # Run migrations
