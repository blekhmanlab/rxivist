#!/bin/bash

# Runs basic commands to set up the environment within a container
# so the user can begin running commands immediately
cd /app
pip install -r requirements.txt
python main.py
bash
