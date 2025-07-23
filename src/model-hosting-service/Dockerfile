
# Use NVIDIA CUDA base image with cuDNN for GPU support
FROM nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu20.04

# Set working directory
WORKDIR /app

# Set non-interactive frontend to avoid prompts
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies and Python 3.9
RUN apt-get update && apt-get install -y --no-install-recommends \
    software-properties-common \
    curl \
    libjpeg-dev \
    zlib1g-dev \
    && add-apt-repository ppa:deadsnakes/ppa \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
    python3.9 \
    python3.9-dev \
    python3.9-distutils \
    && rm -rf /var/lib/apt/lists/*

# Install pip for Python 3.9
RUN curl -sS https://bootstrap.pypa.io/get-pip.py | python3.9 \
    && python3.9 -m pip install --upgrade pip

# Ensure python3 and pip3 point to Python 3.9
RUN PIP3_9_PATH=$(find /usr/local/bin -name pip3.9 2>/dev/null | head -n 1) \
    && update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.9 1 \
    && update-alternatives --install /usr/bin/pip3 pip3 "$PIP3_9_PATH" 1

# Install Python dependencies
RUN pip3 install --no-cache-dir \
    torch==2.0.1+cu118 -f https://download.pytorch.org/whl/torch_stable.html \
    requests \
    pillow \ 
    openslide-python \
    openslide-bin

# Copy scripts
COPY main.py .
COPY techcyte_client.py .

# Run main script
ENTRYPOINT ["python3", "main.py"]