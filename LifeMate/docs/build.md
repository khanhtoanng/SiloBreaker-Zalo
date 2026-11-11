# Build and verify the Python package

The Python build produces an installable wheel and a source archive. Both
contain LifeMate code. Supply the organizer kit and any model files separately
when running the app.

## 1. Build a wheel and source archive

Open PowerShell in `LifeMate/`, where `pyproject.toml` lives. Use a Python
3.10+ environment with the development extra. These steps use the [README setup](../README.md#start-locally)
for `$Python`. Package installation needs a package index or a complete local
wheelhouse for the chosen environment.

```powershell
& $Python -m pip install -e '.[dev]'
$RunTag = Get-Date -Format 'yyyyMMdd-HHmmss'
$BuildOut = Join-Path $env:USERPROFILE "LifeMateWork\packages\$RunTag"
& $Python -m build --no-isolation --outdir $BuildOut
Get-ChildItem -LiteralPath $BuildOut
```

Expect one `.whl` and one `.tar.gz`. Inspect both before sharing them.
The wheel contains the `lifemate` package and distribution metadata. The source
archive also includes the app's docs, configs, scripts, and tests. The build
rules exclude local environments, caches, and development snapshots. Check
that the archive contents contain only project files and metadata.

```powershell
$Wheel = (Get-ChildItem -LiteralPath $BuildOut -Filter '*.whl').FullName
$Sdist = (Get-ChildItem -LiteralPath $BuildOut -Filter '*.tar.gz').FullName
& $Python -m zipfile -l $Wheel
& $Python -m tarfile -l $Sdist
```

## 2. Verify an installed wheel

Install the wheel in a fresh environment so the CLI loads the packaged
application. This step installs the wheel's core dependencies too.

```powershell
$CheckVenv = Join-Path $env:USERPROFILE "LifeMateWork\venvs\wheel-$RunTag"
python -m venv $CheckVenv
$CheckPython = Join-Path $CheckVenv 'Scripts\python.exe'
& $CheckPython -m pip install $Wheel
& $CheckPython -m pip check
& (Join-Path $CheckVenv 'Scripts\lifemate.exe') --help
```

Expect `No broken requirements found.` and a command list including
`predict`, `validate`, and `train`. For a prepared wheelhouse, add
`--no-index --find-links $Wheelhouse` to the pip install commands, with
`$Wheelhouse` set to the directory containing the required wheels.

Run the [test suite](local_quickstart.md#test-the-code) and
[SDK smoke test](local_quickstart.md#1-run-one-sdk-read)
from the source checkout for behavioral checks. For the Linux container build
and its wheelhouse requirements, see [offline packaging](offline_packaging.md).
For competition-specific deliverables, see the [Zalo submission milestone](milestones/06-zalo-submission.md).
