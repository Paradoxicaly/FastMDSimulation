"""Ligand parameterization helpers (AmberTools GAFF).

These utilities shell out to AmberTools (antechamber/parmchk2/tleap) to
parameterize a small-molecule ligand with GAFF/GAFF2 and produce a combined
protein–ligand Amber system (prmtop/inpcrd/pdb) suitable for OpenMM.

The functions are intentionally strict: they raise RuntimeError with helpful
messages when external tools are missing or commands fail.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Dict, Literal

from ..utils.logging import get_logger
from .pdbfix import fix_pdb_with_pdbfixer

logger = get_logger("ligand")


AmberChargeMethod = Literal["bcc", "gas", "resp"]


def _ensure_tool(name: str) -> str:
    """Return the tool path if available, otherwise raise with guidance."""
    path = shutil.which(name)
    if not path:
        raise RuntimeError(
            f"Required AmberTools executable '{name}' not found on PATH. "
            "Install AmberTools (e.g., mamba install -c conda-forge ambertools) and ensure it is on PATH."
        )
    return path


def _run(cmd: list[str], cwd: Path) -> None:
    logger.info(f"Running: {' '.join(cmd)}")
    proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(
            f"Command failed: {' '.join(cmd)}\nstdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        )


def _detect_format(ligand_file: Path) -> str:
    ext = ligand_file.suffix.lower()
    if ext == ".sdf":
        return "sdf"
    if ext == ".mol2":
        return "mol2"
    raise ValueError(f"Unsupported ligand format: {ligand_file}")


def parameterize_ligand_with_gaff(
    ligand_file: str,
    workdir: str,
    *,
    charge_method: AmberChargeMethod = "bcc",
    net_charge: int | None = None,
    ligand_name: str = "LIG",
    gaff: Literal["gaff", "gaff2"] = "gaff2",
) -> Dict[str, str]:
    """
    Parameterize a small-molecule ligand using AmberTools (GAFF/GAFF2).

    Returns a dict with keys: mol2 (GAFF-assigned), frcmod.
    """

    ligand_path = Path(ligand_file).expanduser().resolve()
    work = Path(workdir).expanduser().resolve()
    work.mkdir(parents=True, exist_ok=True)

    fmt = _detect_format(ligand_path)
    name = ligand_name.upper()
    gaff_mol2 = work / f"{name}_gaff.mol2"
    frcmod = work / f"{name}.frcmod"

    # Ensure tools exist before doing anything
    _ensure_tool("antechamber")
    _ensure_tool("parmchk2")

    # 1) antechamber: assign GAFF atom types + charges
    cmd = [
        "antechamber",
        "-i",
        str(ligand_path),
        "-fi",
        fmt,
        "-o",
        str(gaff_mol2),
        "-fo",
        "mol2",
        "-c",
        charge_method,
        "-s",
        "2",
        "-nc",
        str(net_charge if net_charge is not None else 0),
        "-rn",
        name,
    ]
    _run(cmd, work)

    # 2) parmchk2: build frcmod with missing parameters
    cmd = [
        "parmchk2",
        "-i",
        str(gaff_mol2),
        "-f",
        "mol2",
        "-o",
        str(frcmod),
    ]
    _run(cmd, work)

    return {
        "mol2": str(gaff_mol2),
        "frcmod": str(frcmod),
        "ligand_name": name,
        "gaff": gaff,
    }


def build_protein_ligand_system_with_gaff(
    protein_pdb: str,
    ligand_file: str,
    output_prefix: str,
    *,
    ph: float = 7.0,
    charge_method: AmberChargeMethod = "bcc",
    net_charge: int | None = None,
    ligand_name: str = "LIG",
    gaff: Literal["gaff", "gaff2"] = "gaff2",
    box_padding_nm: float = 1.0,
    neutralize: bool = True,
    keep_heterogens: bool = False,
    keep_water: bool = False,
) -> Dict[str, str]:
    """
    Create a solvated protein–ligand Amber system (prmtop/inpcrd/pdb) using GAFF.

    Steps:
      1) Fix protein PDB with PDBFixer (optionally retaining heterogens/waters).
      2) Parameterize ligand with GAFF/GAFF2 (antechamber + parmchk2).
      3) Use tleap to combine, solvate (TIP3PBOX), neutralize, and write prmtop/inpcrd/pdb.
    """

    protein_path = Path(protein_pdb).expanduser().resolve()
    out_prefix = Path(output_prefix).expanduser().resolve()
    out_prefix.parent.mkdir(parents=True, exist_ok=True)

    fixed_protein = out_prefix.parent / f"{protein_path.stem}_fixed.pdb"
    fix_pdb_with_pdbfixer(
        str(protein_path),
        str(fixed_protein),
        ph=ph,
        keep_heterogens=keep_heterogens,
        keep_water=keep_water,
    )

    # Parameterize ligand
    lig_out = parameterize_ligand_with_gaff(
        ligand_file,
        workdir=str(out_prefix.parent),
        charge_method=charge_method,
        net_charge=net_charge,
        ligand_name=ligand_name,
        gaff=gaff,
    )

    # Ensure tleap exists
    _ensure_tool("tleap")

    padding_angstrom = float(box_padding_nm) * 10.0
    prmtop = str(out_prefix.with_suffix(".prmtop"))
    inpcrd = str(out_prefix.with_suffix(".inpcrd"))
    pdb_out = str(out_prefix.with_suffix(".pdb"))
    leapin = out_prefix.with_suffix(".leap.in")

    leap_lines = [
        "source leaprc.protein.ff14SB",
        f"source leaprc.{gaff}",
        "source leaprc.water.tip3p",
        f"loadamberparams {Path(lig_out['frcmod']).name}",
        f"{lig_out['ligand_name']} = loadmol2 {Path(lig_out['mol2']).name}",
        f"PROT = loadpdb {fixed_protein.name}",
        f"COMPLEX = combine {{PROT {lig_out['ligand_name']}}}",
        f"solvatebox COMPLEX TIP3PBOX {padding_angstrom:.3f}",
    ]

    if neutralize:
        leap_lines.append("addions COMPLEX Na+ 0")
        leap_lines.append("addions COMPLEX Cl- 0")

    leap_lines.extend(
        [
            f"saveamberparm COMPLEX {Path(prmtop).name} {Path(inpcrd).name}",
            f"savepdb COMPLEX {Path(pdb_out).name}",
            "quit",
        ]
    )

    leapin.write_text("\n".join(leap_lines))

    # Run tleap in the working directory so relative paths resolve
    _run(["tleap", "-f", str(leapin.name)], cwd=out_prefix.parent)

    # GAFF outputs written; log key artifacts
    logger.info(
        "Built protein–ligand system with GAFF: prmtop=%s, inpcrd=%s, pdb=%s",
        prmtop,
        inpcrd,
        pdb_out,
    )

    return {
        "prmtop": prmtop,
        "inpcrd": inpcrd,
        "pdb": pdb_out,
        "ligand": lig_out["mol2"],
        "frcmod": lig_out["frcmod"],
        "fixed_protein": str(fixed_protein),
    }
