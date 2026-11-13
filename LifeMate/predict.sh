#!/bin/sh
set -eu
if [ "$#" -eq 0 ]; then
    code_dir=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
    set -- --config "$code_dir/configs/inference.competition.json"
fi
export PYTHONHASHSEED=20261109
exec python -m lifemate predict "$@"
