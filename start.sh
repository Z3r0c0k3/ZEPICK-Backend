#!/bin/bash
git pull
gunicorn -c gunicorn.conf.py main:app