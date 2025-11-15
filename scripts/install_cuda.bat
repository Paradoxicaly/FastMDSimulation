@echo off
echo Detecting CUDA-capable GPU...

where nvidia-smi >nul 2>nul
if %errorlevel% equ 0 (
    echo NVIDIA GPU detected
    for /f "tokens=*" %%i in ('nvidia-smi ^| findstr "CUDA Version"') do (
        echo %%i
        echo Installing latest cudatoolkit...
        mamba install -y -c conda-forge cudatoolkit
        if errorlevel 1 (
            conda install -y -c conda-forge cudatoolkit
        )
        echo CUDA toolkit installed successfully
    )
) else (
    echo No NVIDIA GPU detected - CPU-only installation
    echo For HPC systems, use 'module load cuda' before running simulations
)