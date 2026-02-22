# Archive Guide

## Archive Structure

The `/archive` folder contains original files from 2004:

| Folder/File | Source | Description |
|-------------|--------|-------------|
| `data/DECS*.DAT` | Student (owner) | Decision input files (Company 1) |
| `data/REPT12.DAT` | Instructor | Andy's Week 12 report (Company 2) |
| `data/REPT13.DAT` | Instructor | Shorty's Week 13 report (Company 2) |
| `data/REPT14.DAT` | Instructor | Unknown student's Week 14 (Company 2) |
| `data/week1.txt` | Original game | Human-readable Week 1 report (Rosetta Stone!) |
| `spreadsheets/ProsimTable.xls` | Student (owner) | Reverse-engineered simulation spreadsheet |
| `spreadsheets/Nelson.xls` | Reconstructed (Dec 2025) | External data file for ProsimTable.xls (see below) |
| `*.xtc` | Original game | Binary game state files |

**Important**: REPT12/13/14 are from DIFFERENT game runs (cumulative costs decrease), not sequential weeks.

## Nelson.xls - External Data Dependency

`ProsimTable.xls` contains formulas that reference an external file `Nelson.xls` for operator training history lookups. The original file was lost, but was reconstructed in December 2025 based on:

1. **Formula analysis** from ProsimTable.xls Operators tab (DGET/DSUM functions)
2. **Existing training data** visible in the spreadsheet
3. **Reverse-engineering** the required database structure

### Structure of Nelson.xls (Sheet1)

- **Rows 2-30, Columns A-B**: Operator base lookup (`op`, `base`)
- **Rows 34-62, Columns A-E**: Training accumulator (`op`, `week`, `days_wo`, `days_with`, `op` for lookup)
- **Rows 34-62, Columns G-H**: Trained weeks accumulator (`op`, `trained`)

### Using ProsimTable.xls

The spreadsheet expects Nelson.xls at path `C:\Operators\Nelson.xls` (Windows). Update the external references in Excel via Data > Edit Links if using a different location.

### Related files for other players' data

The Entry tab in ProsimTable.xls shows data labeled "andy" and "Shorty", suggesting similar external files (Andy.xls, Shorty.xls) may have existed for comparing different players' game runs.

## Original Data Location

The original archive files are in a sibling directory:

```
/Users/dewittn/Programing/dewittn/Other/Prosim/
```

This contains the raw 2004 files including:
- `ProsimTable CVS Export/` — Spreadsheet analysis tabs
- `A/` — Additional DECS/REPT files
- `475ProSim.ppt` — Instructor's course presentation
- `report.doc` — Human-readable report (Word format)
