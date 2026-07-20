"""Dump all sheets of the ProsimTable workbook versions as cached values."""
import sys
import xlrd

def dump(path, label):
    print("=" * 100)
    print(f"WORKBOOK: {label}")
    print(f"  path: {path}")
    book = xlrd.open_workbook(path)
    print(f"  sheets ({book.nsheets}): {book.sheet_names()}")
    for sh in book.sheets():
        print("-" * 100)
        print(f"SHEET '{sh.name}'  ({sh.nrows} rows x {sh.ncols} cols)")
        for r in range(sh.nrows):
            cells = []
            any_val = False
            for c in range(sh.ncols):
                v = sh.cell_value(r, c)
                if v == "" or v is None:
                    cells.append("")
                else:
                    any_val = True
                    if isinstance(v, float):
                        # trim trailing .0
                        if v == int(v):
                            cells.append(str(int(v)))
                        else:
                            cells.append(f"{v:.4g}")
                    else:
                        cells.append(str(v).strip())
            if any_val:
                print(f"  r{r:>2}: " + " | ".join(f"{c}:{val}" for c, val in enumerate(cells) if val != ""))

if __name__ == "__main__":
    base = "/Users/dewittn/Programing/dewittn/Other/prosim-reconstruction/archive/spreadsheets/"
    which = sys.argv[1] if len(sys.argv) > 1 else "final"
    files = {
        "final": (base + "ProsimTable.xls", "ProsimTable.xls (final, Jul 13 2004)"),
        "week3": (base + "ProsimTable(Week3).xls", "ProsimTable(Week3).xls (Jun 5 2004)"),
        "nelson": (base + "ProsimTable(Nelson).xls", "ProsimTable(Nelson).xls (May 25 2004)"),
    }
    p, lbl = files[which]
    dump(p, lbl)
