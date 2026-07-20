#!/usr/bin/env python3
"""Event-semantics timeline: join body floats, block index, and payload-change
flags per identity, in log order. Looks for correlation between payload
changes, period boundaries, and accumulator behavior."""
import sys
sys.path.insert(0, "/Users/dewittn/Programing/dewittn/Other/prosim-reconstruction/analysis/xtc")
from map_common import body_walk, packed_chain_walk, load, build_identity_labeler

for fkey, pstart in (("a", 912), ("b", 1355)):
    name, data = load(fkey)
    body, _ = body_walk(data)
    packed = packed_chain_walk(data, pstart)
    L = build_identity_labeler()

    print(f"\n=== {fkey} ({name}) timeline ===")
    print(f"{'n':>3} {'blk':>3} {'ident':<5} {'f3':>10} {'f4':>10} {'psize':>5} chg")
    last_payload = {}   # ident -> content
    block = 0
    for entry, rec in zip(body, packed):
        ident = L(entry)
        content = rec["payload"][2:]
        if entry["tag"] == 0x12:
            block += 1
            print(f"{rec['n']:>3} {block:>3} {'--SEP':<5} {'':>10} {'':>10} {rec['size']:>5}")
            continue
        prev = last_payload.get(ident)
        chg = "" if prev is None else ("CHANGE" if prev != content else ".")
        last_payload[ident] = content
        f3 = f"{entry['f3']:.1f}" if entry['f3'] is not None else ""
        f4 = f"{entry['f4']:.1f}" if entry['f4'] is not None else ""
        print(f"{rec['n']:>3} {block:>3} {ident:<5} {f3:>10} {f4:>10} {rec['size']:>5} {chg}")
