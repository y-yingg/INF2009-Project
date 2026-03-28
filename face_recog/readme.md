sudo apt update
sudo apt install -y python3-venv python3-opencv v4l-utils
pip install --upgrade pip
pip install numpy pillow




pip install --upgrade pip
pip install torch torchvision transformers accelerate pillow sentencepiece safetensors
pip install "huggingface_hub[cli]"
mkdir -p models
huggingface-cli download HuggingFaceTB/SmolVLM-500M-Instruct --local-dir models/SmolVLM-500M-Instruct 
