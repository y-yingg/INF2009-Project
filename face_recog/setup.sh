#!/bin/bash

sudo apt update
sudo apt install -y python3-venv python3-opencv v4l-utils

python3 -m venv venv
source venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt