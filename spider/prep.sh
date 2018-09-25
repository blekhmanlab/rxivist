#!/bin/bash

# Runs basic commands to set up the environment within a container
# so the user can begin running commands immediately
# TODO: Bake this into the image?
cd /app
pip3 install -r requirements.txt
python3 spider.py
bash
