
#!/usr/bin/env bash
# Submit simulation, then analysis (production-only) with afterok dependency.
# Usage:
#   bash scripts/submit_slurm_with_analysis.sh job.yml --output simulate_output [--options slurm_options.yml] [--frames N or "start,stop,stride"] [--atoms SELECT] [--slides True|False]
set -euo pipefail
JOB_YML=""; OUTDIR="simulate_output"; OPTFILE=""; FRAMES=""; ATOMS=""; SLIDES="True"
while [[ $# -gt 0 ]]; do
  case "$1" in
    *.yml|*.yaml) JOB_YML="$1"; shift ;;
    --output|-o) OUTDIR="$2"; shift 2 ;;
    --options) OPTFILE="$2"; shift 2 ;;
    --frames) FRAMES="$2"; shift 2 ;;
    --atoms) ATOMS="$2"; shift 2 ;;
    --slides) SLIDES="$2"; shift 2 ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done
[ -z "$JOB_YML" ] && { echo "Provide a job YAML."; exit 1; }
ACCOUNT=""; PARTITION="gpu"; TIME="02:00:00"; GPUS="1"; NODES="1"; NTASKS="1"; APARTITION="gpu"; ATIME="00:30:00"
if [ -n "$OPTFILE" ]; then
  read -r ACCOUNT PARTITION TIME GPUS NODES NTASKS APARTITION ATIME <<EOF
$(python - <<'PY' "$OPTFILE"
import sys, yaml
opt = yaml.safe_load(open(sys.argv[1])) or {}
def gv(*ks, default=""):
    d=opt
    for k in ks: d=(d or {}).get(k, {} if k!=ks[-1] else None)
    return default if d is None else d
print(gv('account',''), gv('partition','gpu'), gv('time','02:00:00'), gv('gpus',1), gv('nodes',1), gv('ntasks',1), gv('analyze','partition','gpu'), gv('analyze','time','00:30:00'))
PY
)
EOF
fi
PROJECT=$(python - <<'PY' "$JOB_YML"
import sys, yaml; print((yaml.safe_load(open(sys.argv[1])) or {}).get('project','project'))
PY
)
SIM_CMD="fastmds simulate -s $JOB_YML --output $OUTDIR"
AN_ARGS=""; if [ "$SLIDES" = "True" ]; then AN_ARGS="--slides"; fi
[ -n "$FRAMES" ] && AN_ARGS="$AN_ARGS --frames $FRAMES"
[ -n "$ATOMS" ] && AN_ARGS="$AN_ARGS --atoms $ATOMS"
SBATCH_SIM="#!/usr/bin/env bash
#SBATCH -J fmds-sim
#SBATCH -p ${PARTITION}
#SBATCH -t ${TIME}
#SBATCH -N ${NODES}
#SBATCH -n ${NTASKS}
"
if [ -n "$ACCOUNT" ]; then SBATCH_SIM+="#SBATCH -A ${ACCOUNT}
"; fi
if [ -n "$GPUS" ] && [ "$GPUS" != "0" ]; then SBATCH_SIM+="#SBATCH --gres=gpu:${GPUS}
"; fi
SBATCH_SIM+="
set -euo pipefail
$SIM_CMD
"
SIM_JOBID=$(echo -e "$SBATCH_SIM" | sbatch --parsable)
echo "Submitted simulation job: $SIM_JOBID"
PROJECT_DIR="${OUTDIR}/${PROJECT}"
SBATCH_AN="#!/usr/bin/env bash
#SBATCH -J fmds-an
#SBATCH -p ${APARTITION}
#SBATCH -t ${ATIME}
#SBATCH -N 1
#SBATCH -n 1
"
if [ -n "$ACCOUNT" ]; then SBATCH_AN+="#SBATCH -A ${ACCOUNT}
"; fi
SBATCH_AN+="
set -euo pipefail
PROJ="$PROJECT_DIR"
for run in "$PROJECT_DIR"/*; do
  [ -d "$run" ] || continue
  stage="$run/production"
  if [ -f "$stage/traj.dcd" ] && [ -f "$stage/topology.pdb" ]; then
    traj="$stage/traj.dcd"; top="$stage/topology.pdb"
    if command -v fastmda >/dev/null 2>&1; then
      echo fastmda analyze -traj "$traj" -top "$top" $AN_ARGS
      fastmda analyze -traj "$traj" -top "$top" $AN_ARGS
    else
      echo python -m fastmdanalysis analyze -traj "$traj" -top "$top" $AN_ARGS
      python -m fastmdanalysis analyze -traj "$traj" -top "$top" $AN_ARGS
    fi
  fi
done
"
echo -e "$SBATCH_AN" | sbatch --dependency=afterok:${SIM_JOBID}
echo "Submitted analysis job dependent on $SIM_JOBID"
