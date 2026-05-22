#!/usr/bin/env bash
set -o errexit
pip install --upgrade pip
pip install -r requirements.txt
 manage.py collectstatic --noinput
 manage.py migrate
