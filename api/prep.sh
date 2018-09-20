#!/bin/bash

# Runs basic commands to set up the environment within a container
# so the user can begin running commands immediately
# TODO: Bake this into the image?
cd /app
pip install -r requirements.txt
python main.py
bash # if someone kills the server, drop them into a shell TODO: Don't do this in prod
