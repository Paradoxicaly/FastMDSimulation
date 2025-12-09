# FastMDSimulation — Quick Start

Minimal knobs to run **automated MD with OpenMM**, with optional analysis via **FastMDAnalysis**.

---

## CLI

### YAML-driven (recommended)
```bash
fastmds simulate -system job.yml -o simulate_output   [--analyze] [--frames "0,-1,10"] [--atoms protein] [--slides True|False] [--dry-run]
```

### One-shot from PDB
```bash
fastmds simulate -system protein.pdb -o simulate_output --config config.yml   [--analyze] [--frames "0,-1,10"] [--atoms protein] [--slides True|False] [--dry-run]
```

**Notes**
- `-system` may also be provided as `-s` or `--system`.
- `--slides` defaults to **True**; set `--slides False` to disable.
- `--frames` uses FastMDAnalysis format (e.g., `"0,-1,10"` or `"200"`).
- `--atoms` is an MD selection string (e.g., `protein`, `"protein and name CA"`).

---

## Python API
```python
from fastmdsimulation import FastMDSimulation

fastmds = FastMDSimulation("protein.pdb", output="simulate_output", config=None)
project_dir = fastmds.simulate(analyze=True, frames="0,-1,10", atoms="protein", slides=True)
```

---

## Dry run
See the plan and the exact `fastmda analyze` commands (no compute done):
```bash
# YAML
fastmds simulate -system job.yml -o simulate_output --analyze --frames 0,-1,10 --atoms protein --dry-run

# PDB
fastmds simulate -system protein.pdb -o simulate_output --config config.yml --analyze --dry-run
```

---

## Logging
- Human-readable console logs; a file log is written to `<output>/<project>/fastmds.log`.
- `--dry-run` prints the exact `fastmda analyze` command(s) that would run.

## PLUMED (optional)
- Install (Linux/WSL recommended): `mamba install -c conda-forge openmm-plumed`.
- CLI (all stages):
	```bash
	fastmds simulate -system job.yml --plumed --plumed-script plumed.dat --plumed-log-frequency 100
	```
- YAML (default and per-stage overrides):
	```yaml
	defaults:
	  plumed:
	    enabled: true
	    script: plumed.dat
	    log_frequency: 100
	stages:
	  - { name: nvt, steps: 5000, plumed: { enabled: true, script: stage_nvt.dat } }
	```
- Outputs (COLVAR, HILLS, etc.) are auto-written inside each stage directory.

---

## Tips
- **Ions:** choose salt in YAML via `defaults.ions: NaCl` or `KCl` (custom `{positiveIon, negativeIon}` supported).
- **PDB fixing is strict:** if PDBFixer fails, the run aborts (no silent fallback).
