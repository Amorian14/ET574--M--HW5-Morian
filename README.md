# Android Permissions Visualizer

A small wxPython GUI that loads an Android permissions CSV, shows a sample dataset table + summary, and can generate/export permission prevalence graphs for **malware vs benign**.

## Files
- `AndriodPermissionsData.py` — GUI application
- `data.csv` — example input dataset (if included with the assignment)

## Requirements

### Python packages
Install dependencies:
```bash
pip install pandas numpy matplotlib wxPython
```

> Note: `wxPython` is required to run the GUI.

## Input CSV format

Your CSV must contain:
- A label column named **`Result`** (or select another label column if it’s not present)
  - Values must be **only 0 and 1**
    - `0` = benign
    - `1` = malware
- Permission feature columns (numeric columns expected: usually 0/1 or counts)

## How to run

```bash
python AndriodPermissionsData.py
```

## Using the GUI

1. Click **Load CSV**
2. If the CSV does not include a `Result` column, select which column contains labels (0/1)
3. Browse:
   - **Dataset (sample)** tab: shows a preview of the first rows
   - **Summary** tab: dataset stats and top permissions (by frequency)
4. Optional: use **Filter columns...** to narrow which permission columns appear in the dataset preview
5. Click **Generate Graphs** to compute:
   - Malware: top permissions by prevalence across malware apps
   - Benign: top permissions by prevalence across benign apps
   - Comparison: permissions most indicative of malware (difference in mean prevalence)
6. Click **Export Graphs...** to save PNGs.

## Output files (export)
When you export, the app saves:
- `malware_permissions.png`
- `benign_permissions.png`
- `comparison_permissions.png`

## Notes / troubleshooting

- If you see an error about `wxPython`, install it with `pip install wxPython`.
- If your label column contains values other than `0` and `1`, the app will stop and show an error.
