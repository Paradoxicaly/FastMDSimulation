#!/bin/bash
# install_cuda.sh - Smart CUDA installation for FastMDSimulation

set -e

echo "Detecting CUDA-capable GPU..."
if command -v nvidia-smi &> /dev/null; then
    echo "NVIDIA GPU detected"
    if nvidia-smi | grep -q "CUDA Version"; then
        CUDA_VERSION=$(nvidia-smi | grep "CUDA Version" | sed 's/.*CUDA Version: //' | sed 's/\..*//')
        echo "System CUDA version: $CUDA_VERSION.x"
        
        # Install compatible cudatoolkit
        echo "Installing compatible cudatoolkit..."
        mamba install -y -c conda-forge cudatoolkit=${CUDA_VERSION}.* || conda install -y -c conda-forge cudatoolkit=${CUDA_VERSION}.*
        echo "CUDA toolkit installed successfully"
    else
        echo "NVIDIA GPU found but CUDA driver may be outdated"
        echo "Installing latest cudatoolkit..."
        mamba install -y -c conda-forge cudatoolkit || conda install -y -c conda-forge cudatoolkit
    fi
else
    echo "No NVIDIA GPU detected - CPU-only installation"
    echo "For HPC systems, use 'module load cuda' before running simulations"
fi