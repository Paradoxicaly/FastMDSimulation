
#!/usr/bin/env bash
# PBS: simulation then analysis with dependency.
# Usage:
#   bash scripts/submit_pbs_with_analysis.sh job.yml --output simulate_output [--options pbs_options.yml] [--frames N or "start,stop,stride"] [--atoms SELECT] [--slides True|False]
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
ACCOUNT=""; QUEUE="gpuq"; WALLTIME="02:00:00"; GPUS="1"; NCPUS="1"; AQUEUE="gpuq"; AWALLTIME="00:30:00"
if [ -n "$OPTFILE" ]; then
  read -r ACCOUNT QUEUE WALLTIME GPUS NCPUS AQUEUE AWALLTIME <<EOF
$(python - <<'PY' "$OPTFILE"
import sys, yaml
opt = yaml.safe_load(open(sys.argv[1])) or {}
def gv(*ks, default=""):
    d=opt
    for k in ks: d=(d or {}).get(k, {} if k!=ks[-1] else None)
    return default if d is None else d
print(gv('account',''), gv('queue','gpuq'), gv('walltime','02:00:00'), gv('gpus',1), gv('ncpus',1), gv('analyze','queue','gpuq'), gv('analyze','walltime','00:30:00'))
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
SIM_PBS=$(mktemp)
cat > "$SIM_PBS" <<PBS
#!/usr/bin/env bash
#PBS -N fmds-sim
#PBS -q ${QUEUE}
#PBS -l walltime=${WALLTIME}
#PBS -l select=1:ncpus=${NCPUS}:ngpus=${GPUS}
PBS
[ -n "$ACCOUNT" ] && echo "#PBS -A ${ACCOUNT}" >> "$SIM_PBS"
cat >> "$SIM_PBS" <<'PBS'
set -euo pipefail
PBS
echo "$SIM_CMD" >> "$SIM_PBS"
SIM_JOBID=$(qsub "$SIM_PBS")
echo "Submitted simulation job: $SIM_JOBID"
AN_PBS=$(mktemp)
cat > "$AN_PBS" <<PBS
#!/usr/bin/env bash
#PBS -N fmds-an
#PBS -q ${AQUEUE}
#PBS -l walltime=${AWALLTIME}
#PBS -l select=1:ncpus=1
#PBS -W depend=afterok:${SIM_JOBID}
PBS
[ -n "$ACCOUNT" ] && echo "#PBS -A ${ACCOUNT}" >> "$AN_PBS"
cat >> "$AN_PBS" <<'PBS'
set -euo pipefail
PROJ="$1"
AN_ARGS="$2"
for run in "$PROJ"/*; do
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
PBS
qsub "$AN_PBS" -- "$OUTDIR/$PROJECT" "$AN_ARGS"
echo "Submitted analysis job dependent on $SIM_JOBID"
