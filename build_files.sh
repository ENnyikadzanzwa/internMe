#!/bin/bash
pip install -r requirements.txt
python3.11 manage.py collectstatic --noinput
python3.11 manage.py migrate
