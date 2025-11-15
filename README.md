# FastMDSimulation

Automated Molecular Dynamics Simulation — OpenMM‑based one‑liner MD with a simple CLI & Python API. Optional post‑run analysis via **FastMDAnalysis**.

- **Pipeline:** PDBFixer (if needed) → solvate+ions → minimize → NVT → NPT → production  
- **Reproducible:** YAML job files **or** one‑shot from PDB with optional overrides  
- **Analysis:** `--analyze` invokes `fastmda analyze` (supports `--frames`, `--atoms`, `--slides`)  
- **HPC‑ready:** Works on CPU, NVIDIA GPUs (CUDA), and clusters with module‑provided CUDA  
- **OpenMM 8:** Modern `openmm` namespace; defaults to **CHARMM36** + TIP3P

---

## Installation (Conda‑only)

We recommend **Miniforge** (conda‑forge first). This avoids mixing package channels and makes GPU installs predictable.

### 1) Install Miniforge

If `mamba` isn’t present after installing Miniforge, you can add it with `conda install -n base -c conda-forge mamba`.

#### macOS (Apple Silicon / arm64)
```bash
curl -L -o "$HOME/Miniforge3-MacOSX-arm64.sh" \
  "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-MacOSX-arm64.sh"
bash "$HOME/Miniforge3-MacOSX-arm64.sh" -b -p "$HOME/miniforge3"
source "$HOME/miniforge3/etc/profile.d/conda.sh"
conda init zsh
exec $SHELL -l
mamba --version || true
conda --version
```

#### macOS (Intel / x86_64)
```bash
curl -L -o "$HOME/Miniforge3-MacOSX-x86_64.sh" \
  "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-MacOSX-x86_64.sh"
bash "$HOME/Miniforge3-MacOSX-x86_64.sh" -b -p "$HOME/miniforge3"
source "$HOME/miniforge3/etc/profile.d/conda.sh"
conda init zsh
exec $SHELL -l
mamba --version || true
conda --version
```

#### Linux (x86_64)
```bash
curl -L -o "$HOME/Miniforge3-Linux-x86_64.sh" \
  "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh"
bash "$HOME/Miniforge3-Linux-x86_64.sh" -b -p "$HOME/miniforge3"
source "$HOME/miniforge3/etc/profile.d/conda.sh"
conda init "$(basename "$SHELL")"
exec $SHELL -l
mamba --version || true
conda --version
```

#### Linux (ARM64 / aarch64)
```bash
curl -L -o "$HOME/Miniforge3-Linux-aarch64.sh" \
  "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-aarch64.sh"
bash "$HOME/Miniforge3-Linux-aarch64.sh" -b -p "$HOME/miniforge3"
source "$HOME/miniforge3/etc/profile.d/conda.sh"
conda init "$(basename "$SHELL")"
exec $SHELL -l
mamba --version || true
conda --version
```

#### Windows (PowerShell)
```powershell
$inst = "$env:USERPROFILE\Downloads\Miniforge3-Windows-x86_64.exe"
Invoke-WebRequest -Uri "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Windows-x86_64.exe" -OutFile $inst
Start-Process -Wait $inst
& "$env:USERPROFILE\miniforge3\condabin\conda.bat" init powershell
# Close and reopen PowerShell
conda --version
# Optional: add mamba
conda install -n base -c conda-forge mamba
```

### 2) Create the environment

Pick the file that matches your setup:

| Scenario | Use this | Why |
| --- | --- | --- |
| Laptop / CPU‑only (macOS/Windows/Linux) | `environment.yml` | No GPU runtime bundled. Portable baseline. |
| HPC with CUDA via **modules** | `environment.yml` + `module load cuda/<ver>` | Avoids conflicts with cluster CUDA. |
| Local NVIDIA GPU (no modules) | `environment.gpu.yml` | Bundles `cudatoolkit` so CUDA “just works”. |

```bash
# CPU or HPC (with CUDA module)
mamba env create -f environment.yml || conda env create -f environment.yml
conda activate fastmds

# Local NVIDIA GPU (bundled CUDA)
mamba env create -f environment.gpu.yml || conda env create -f environment.gpu.yml
conda activate fastmds
```

> **HPC note:** If your site provides CUDA via modules, do **not** install `cudatoolkit` in the env. Use:
> ```bash
> module load cuda/11.8  # or the site default
> ```

### 3) Install FastMDSimulation into the env

From the project root:
```bash
pip install -e .
```

> We intentionally **do not** publish on PyPI because core dependencies (e.g., OpenMM) are conda‑first; using conda avoids binary/ABI issues.

### 4) Verify OpenMM sees your platforms
```bash
python - <<'PY'
import openmm as mm
print('Platforms:', [mm.Platform.getPlatform(i).getName() for i in range(mm.Platform.getNumPlatforms())])
PY
# Expect 'CUDA' if a GPU is available (macOS usually shows 'CPU' and sometimes 'OpenCL').
```

To force a backend in your job YAML:
```yaml
defaults:
  platform: CUDA   # or OpenCL / CPU
```

At runtime, the engine logs:
```
Platform: CUDA (CudaDeviceIndex=0, CudaPrecision=single)
```

---

## Quick Start

### YAML‑driven (recommended for reproducibility)

```bash
fastmds simulate -system examples/waterbox/job.yml -o simulate_output --analyze
```

### One‑shot from PDB (with overrides)

```bash
fastmds simulate -system examples/trp_cage/trp_cage.pdb -o simulate_output \
  --config examples/config.quick.yml \
  --analyze --frames "0,-1,10" --atoms protein
```

**Analysis flags** (only when `--analyze` is present):

- `--slides` (default **True**; set `--slides False` to disable slides)
- `--frames` (e.g., `"0,-1,10"` subsample; `"200"` first 200 frames; FastMDAnalysis format)
- `--atoms` (e.g., `protein`, `"protein and name CA"`)

Analysis output is streamed line‑by‑line and prefixed with `[fastmda]` in your log.

---

## Accepted Inputs & Behavior

You can supply **raw structures** or **parameterized systems** in your YAML. The orchestrator normalizes each entry and the engine dispatches to the right OpenMM loader.

### PDB route (auto‑prepared by FastMDSimulation)
```yaml
systems:
  - id: MyProt
    pdb: path/to/protein.pdb        # raw PDB → PDBFixer → *_fixed.pdb → solvate+ions → run
    # OR if you already vetted a fixed file:
    # fixed_pdb: path/to/protein_fixed.pdb  # skips PDBFixer
```
- PDB inputs are **strictly** fixed with PDBFixer (missing atoms/residues, hydrogens at pH 7.0). Failures abort.
- After fixing, the system is **solvated (TIP3P)**, ions are added (NaCl by default), and CHARMM36 is used unless overridden.

### AMBER route (already parameterized)
```yaml
systems:
  - id: MyAmber
    type: amber
    prmtop: path/to/system.prmtop
    inpcrd: path/to/system.inpcrd   # or rst7:
    # rst7: path/to/system.rst7
```
- Loaded via `AmberPrmtopFile/AmberInpcrdFile`. Box vectors are propagated when present.

### GROMACS route (already parameterized)
```yaml
systems:
  - id: MyGro
    type: gromacs
    top: path/to/topol.top
    gro: path/to/conf.gro           # or g96:
    # g96: path/to/conf.g96
    # Optional additional includes:
    itp: [path/to/ffcustom.itp, path/to/ligand.itp]
```
- Loaded via `GromacsTopFile/GromacsGroFile`. Periodic box vectors are used from the coordinate file.

### CHARMM route (already parameterized)
```yaml
systems:
  - id: MyCharmm
    type: charmm
    psf: path/to/system.psf
    # coordinates (choose one)
    crd: path/to/system.crd
    # or
    # pdb: path/to/system.pdb
    # parameters (choose 'params' list OR any of prm/rtf/str)
    params: [toppar/par_all36m_prot.prm]
    # or
    # prm: [file.prm, another.prm]
    # rtf: [file.rtf]
    # str: [file.str]
```

---

## YAML Reference (minimal)

```yaml
project: TrpCage

defaults:
  engine: openmm
  platform: auto              # auto → CUDA → OpenCL → CPU
  temperature_K: 300
  timestep_fs: 2.0
  constraints: HBonds
  minimize_tolerance_kjmol_per_nm: 10.0
  minimize_max_iterations: 0
  report_interval: 100
  checkpoint_interval: 500
  forcefield: ["charmm36.xml", "charmm36/water.xml"]
  box_padding_nm: 1.0
  ionic_strength_molar: 0.15
  neutralize: true
  ions: NaCl                  # "NaCl" | "KCl" | {positiveIon: "K+", negativeIon: "Cl-"}
  # integrator: langevin      # default; see below
  # log_style: pretty         # pretty | plain (console only)

stages:
  - { name: minimize,   steps: 0 }
  - { name: nvt,        steps: 5000,  ensemble: NVT }
  - { name: npt,        steps: 5000,  ensemble: NPT }
  - { name: production, steps: 10000, ensemble: NPT }

systems:
  - id: TrpCage
    pdb: examples/trp_cage/trp_cage.pdb
```

### Integrator selection
Set via `defaults.integrator`:
```yaml
defaults:
  integrator:
    name: langevin            # langevin | brownian | verlet | variable_langevin | variable_verlet
    timestep_fs: 2.0
    friction_ps: 1.0          # used by langevin/brownian
    error_tolerance: 0.001    # used by variable_* integrators
```

### Logging style
- Console style: `defaults.log_style: pretty | plain` (or env `FASTMDS_LOG_STYLE`).
- Project log file is always plain ISO timestamps: `<output>/<project>/fastmds.log`.

---

## Python API

```python
from fastmdsimulation import FastMDSimulation

fastmds = FastMDSimulation("examples/trp_cage/trp_cage.pdb",
                           output="simulate_output",
                           config="examples/config.quick.yml")  # optional for overrides
project_dir = fastmds.simulate(analyze=True,
                               frames="0,-1,10",
                               atoms="protein",
                               slides=True)
print("Outputs in:", project_dir)
```

- If `system` ends with `.yml/.yaml`, the YAML is executed; `config` is ignored.
- If `system` ends with `.pdb`, PDBFixer runs (strict), then a temporary `job.auto.yml` is generated and executed.

---

## Dry‑run (plan only)

Print stages, approx ps, output dirs, and the exact `fastmda analyze` commands (when `--analyze` is present):

```bash
# YAML
fastmds simulate -system job.yml -o simulate_output --analyze --frames "0,-1,10" --atoms protein --dry-run

# PDB
fastmds simulate -system examples/trp_cage/trp_cage.pdb -o simulate_output \
  --config examples/config.quick.yml --analyze --dry-run
```

---

## Outputs

```
simulate_output/<project>/
  fastmds.log                     # project log (plain text)
  inputs/                         # auto-populated provenance bundle
    job.yml
    <system-id>/                  # per-system inputs (engine-ready + originals when applicable)
      protein.pdb | *_fixed.pdb | prmtop | inpcrd | top | gro | psf | prm/rtf/str | ...
  <run_id>/                       # e.g., TrpCage_T300
    minimize/
      state.log | state.chk | stage.json | topology.pdb
    nvt/
      traj.dcd | state.log | state.chk | stage.json | topology.pdb
    npt/
      traj.dcd | state.log | state.chk | stage.json | topology.pdb
    production/
      traj.dcd | state.log | state.chk | stage.json | topology.pdb
    done.ok
  meta.json                       # start/end time, job.yml SHA256
```

---

## Troubleshooting

- **No CUDA in `Platforms:` list**  
  On clusters, load the site CUDA module (e.g., `module load cuda/11.8`) *and* use `environment.yml` (CPU).  
  On local workstations, use `environment.gpu.yml` to bundle `cudatoolkit`.

- **Mixed CUDA runtimes**  
  Avoid mixing module CUDA and conda `cudatoolkit` in the same job. Pick one strategy.

- **PDBFixer failed**  
  The fixer is strict by design. Inspect the error in `fastmds.log`, repair upstream, or provide a vetted `fixed_pdb:` path.

- **Different log look**  
  FastMDSimulation uses a compact, icon‑and‑color console style (or `plain` if you set `log_style: plain` or `FASTMDS_LOG_STYLE=plain`).  
  FastMDAnalysis prints timestamped Python‑logging lines. We forward them prefixed with `[fastmda]` for clarity.

---

## Help & Version

```bash
fastmds -h
fastmds simulate -h
fastmds -v
```

---

## License

MIT
