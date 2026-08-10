#!/bin/bash
set -euo pipefail

URL="${1:-http://flask-hpa:5000/up/1}"
BURST="${2:-3}"          # how many /up/1 requests to fire per step
SLEEP="${3:-5}"          # seconds between steps
STEPS="${4:-60}"         # total number of steps

for i in $(seq 1 "$STEPS"); do
  echo "[${i}/${STEPS}] sending ${BURST} load bumps to ${URL}"
  for _ in $(seq 1 "$BURST"); do
    curl -sS "${URL}" > /dev/null &
  done
  wait
  sleep "$SLEEP"
done

echo "Load ramp complete"
