#!/bin/sh
set -eu
cd -- "$(dirname -- "$0")"
export PYTHONHASHSEED=20261109
exec jupyter lab --port=9777 --ip=0.0.0.0 --IdentityProvider.token=zac2026 --allow-root --no-browser
