#!/bin/bash

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Create model folder
mkdir -p models

# Download model
huggingface-cli download HuggingFaceTB/SmolVLM-500M-Instruct \
  --local-dir models/SmolVLM-500M-Instruct