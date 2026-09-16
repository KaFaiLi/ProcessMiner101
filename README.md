# Process Mining with Python: Investment-Banking Booking Workshop

This repository contains a one-hour, hands-on introduction to process mining with
Python and PM4Py. The examples use a completely fictional investment-banking
trade-booking process.

## Workshop files

- `process_mining_workshop.ipynb` — learner notebook with guided `TODO` exercises.
- `process_mining_workshop_solutions.ipynb` — fully worked notebook with outputs and interpretations.
- `data/investment_banking_booking_log.csv` — synthetic event log used in both notebooks.
- `data/instructor_outlier_answer_key.csv` — planted anomaly labels for solution checking only.
- `src/generate_booking_log.py` — deterministic dataset generator.

All people, firms, accounts, counterparties, and transactions in the dataset are
fictional. The material is educational and is not a control framework or financial advice.

## Setup with uv

The project is pinned through `pyproject.toml` and `uv.lock` and targets Python 3.12 or newer.

```powershell
uv sync
uv run jupyter lab
```

If Windows reports that the system drive has no temporary space during installation,
redirect uv's temporary files and cache to this project drive and retry:

```powershell
New-Item -ItemType Directory -Force .tmp | Out-Null
$env:TEMP = (Resolve-Path .tmp).Path
$env:TMP = $env:TEMP
$env:UV_CACHE_DIR = Join-Path $env:TEMP "uv-cache"
uv sync
```

Open `process_mining_workshop.ipynb` to take the workshop, or
`process_mining_workshop_solutions.ipynb` for the completed version.

PM4Py's native graph renderer uses the Graphviz system executable (`dot`). The
notebooks detect whether it is installed. If it is not available, the DFGs still
render through the included NetworkX/Matplotlib fallback, and the discovered
process tree is shown as text.

## Rebuild the synthetic data and notebooks

The checked-in data is generated with seed `42`:

```powershell
uv run python src/generate_booking_log.py --output-dir data
uv run python scripts/build_notebooks.py
uv run jupyter nbconvert --to notebook --execute --inplace process_mining_workshop_solutions.ipynb
uv run python -m unittest discover -s tests -v
```

The first command always produces 160 cases: 120 clean baseline cases and 40
monitoring cases. Exactly 15 monitoring cases contain planted anomalies.

## Suggested facilitation

The notebooks contain a timed agenda. Pause at each **Your turn** prompt before
showing the corresponding solution. The final detector deliberately combines
three interpretable signals—rare variants, long duration, and conformance fitness.
It is a teaching example: an anomaly is evidence for investigation, not proof of
misconduct or error.
