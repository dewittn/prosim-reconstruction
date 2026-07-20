#!/usr/bin/env python3
"""Shared body-walk + packed-chain-walk primitives for the alignment map."""
import struct
import hashlib
from pathlib import Path

DATA = Path("/Users/dewittn/Programing/dewittn/Other/prosim-reconstruction/archive/data")
FILES = {
    "a": ("prosim.xtc", DATA / "prosim.xtc"),
    "b": ("prosim1.xtc", DATA / "prosim1.xtc"),
}

BODY_START = 87


def body_walk(data, start=BODY_START):
    """Walk the body operator log. Returns list of dicts with offset, tag, floats."""
    pos = start
    out = []
    while pos < len(data):
        t = data[pos]
        if t == 0x15 and pos + 17 <= len(data):
            f1, f2, f3, f4 = struct.unpack("<4f", data[pos + 1:pos + 17])
            out.append({"offset": pos, "tag": 0x15, "f1": f1, "f2": f2, "f3": f3, "f4": f4})
            pos += 17
        elif t == 0x12 and pos + 9 <= len(data):
            f1, f2 = struct.unpack("<2f", data[pos + 1:pos + 9])
            out.append({"offset": pos, "tag": 0x12, "f1": f1, "f2": f2, "f3": None, "f4": None})
            pos += 9
        else:
            break
    return out, pos  # pos = offset where log ends (first unrecognized byte)


# --- identity labeling: consistent across files, order of first appearance a-then-b ---
def build_identity_labeler():
    lbl = {}
    nxt = [1]

    def L(entry):
        if entry["tag"] == 0x12:
            return "SEP"
        f1 = entry["f1"]
        if 2.7 < f1 < 2.9:
            return "SENT"
        key = struct.pack("<f", f1).hex()
        if key not in lbl:
            lbl[key] = "ID%02d" % nxt[0]
            nxt[0] += 1
        return lbl[key]

    return L


def packed_chain_walk(data, start, max_n=500):
    """Chain-walk the packed region: for n=1,2,3,... find earliest offset > prev
    marker offset where byte[i]==n and byte[i+1]==0x0a. Returns list of dicts
    with n, marker_offset, payload_start, payload_end, payload bytes.
    Payload for record n spans [marker_offset(n), marker_offset(n+1)) i.e. from
    its own marker byte through the byte before the next marker. The last
    record's payload runs to EOF.
    """
    records = []
    prev_marker = start - 1  # search must find offset > prev_marker
    n = 1
    while True:
        target = n if n < 256 else None
        if target is None:
            break
        found = None
        i = prev_marker + 1
        while i + 1 < len(data):
            if data[i] == target and data[i + 1] == 0x0a:
                found = i
                break
            i += 1
        if found is None:
            break
        records.append({"n": n, "marker_offset": found})
        prev_marker = found
        n += 1
        if n > max_n:
            break
    # fill in payload spans
    for idx, rec in enumerate(records):
        start_off = rec["marker_offset"]
        end_off = records[idx + 1]["marker_offset"] if idx + 1 < len(records) else len(data)
        rec["payload_start"] = start_off
        rec["payload_end"] = end_off
        rec["payload"] = data[start_off:end_off]
        rec["size"] = end_off - start_off
        rec["sha1_8"] = hashlib.sha1(rec["payload"]).hexdigest()[:8]
    return records


def load(fkey):
    name, path = FILES[fkey]
    return name, path.read_bytes()
