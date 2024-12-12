#!/bin/bash

apt-get update && apt-get install -y python3-pip  # Install pip
python3 -m pip install --upgrade pip             # Upgrade pip
pip3 install -r requirements.txt                 # Install dependencies
python3 manage.py collectstatic --noinput        # Collect static files
python3 manage.py migrate                        # Run migrations
