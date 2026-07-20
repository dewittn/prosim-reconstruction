#!/usr/bin/env python3
"""TEST 5: transform-then-retest sweep on packed-payload dense interiors.
For a sample of distinct payloads, take the interior region (between the
first and last [0x80-0x87][0xF8-0xFE] sub-header marker -- the densest,
least-structured part) and apply:
  - XOR with absolute byte position i
  - XOR with (i & 0xFF)   [degenerate/same for interiors < 256 bytes, kept
    for completeness on longer interiors]
  - XOR with a repeating 2-byte key derived from the record's own marker
    bytes [n, 0x0a]
  - XOR with a repeating 4-byte key [n, 0x0a, n, 0x0a]
  - byte-wise delta (mod 256)
  - byte-wise delta then XOR with position (compound)
For each, recompute Shannon entropy (bits/byte) and 1-bit density, and flag
any transform that drops entropy below ~6.0 bits/byte (the threshold noted
in the brief as a real lead).
"""
import sys
import math
from collections import Counter

sys.path.insert(0, "/Users/dewittn/Programing/dewittn/Other/prosim-reconstruction/analysis/xtc")
from pay_anchor import FILES, parse_body, chain_walk, get_payloads


def entropy(b):
    if not b:
        return 0.0
    c = Counter(b)
    n = len(b)
    return -sum((v / n) * math.log2(v / n) for v in c.values())


def bit_density(b):
    if not b:
        return 0.0
    ones = sum(bin(x).count("1") for x in b)
    return ones / (len(b) * 8)


def find_markers(payload):
    out = []
    for i in range(len(payload) - 1):
        b0, b1 = payload[i], payload[i + 1]
        if 0x80 <= b0 <= 0x87 and 0xF8 <= b1 <= 0xFE:
            out.append(i)
    return out


def interior_of(payload):
    marks = find_markers(payload)
    if len(marks) < 2:
        return None
    return payload[marks[0] + 2: marks[-1]]


def xor_position(b):
    return bytes(x ^ (i & 0xFF) for i, x in enumerate(b))


def xor_key(b, key):
    return bytes(x ^ key[i % len(key)] for i, x in enumerate(b))


def delta(b):
    out = bytearray(len(b))
    prev = 0
    for i, x in enumerate(b):
        out[i] = (x - prev) & 0xFF
        prev = x
    return bytes(out)


def load_samples():
    """Return list of (tag, n, payload) for distinct payloads, largest first
    (so interiors are long enough to be meaningful)."""
    seen = {}
    for tag, cfg in FILES.items():
        data = open(cfg["path"], "rb").read()
        body = parse_body(data, cfg["body_start"], cfg["body_end"])
        markers = chain_walk(data, cfg["pk_start"], cfg["maxn"])
        payloads = get_payloads(data, markers, len(data))
        for (kind, fl), (n, payload) in zip(body, payloads):
            if kind != "15":
                continue
            p = bytes(payload)
            seen.setdefault(p, (tag, n))
    items = [(tag, n, p) for p, (tag, n) in seen.items()]
    items.sort(key=lambda t: -len(t[2]))
    return items[:8]


def fixed_width_test(b, widths=(3, 4, 5, 6, 7, 8, 12)):
    """Quick fixed-bit-width symbol test: pack bits MSB-first, split into
    fixed-width symbols, measure the symbol-level entropy relative to max
    possible for that width. Returns dict width->ratio (close to 1.0 = looks
    close to uniform/random at that width, i.e. no useful fixed-width
    structure found; much < 1.0 = a candidate width)."""
    bits = []
    for byte in b:
        for i in range(7, -1, -1):
            bits.append((byte >> i) & 1)
    results = {}
    for w in widths:
        nsym = len(bits) // w
        if nsym < 8:
            continue
        syms = []
        for i in range(nsym):
            v = 0
            for j in range(w):
                v = (v << 1) | bits[i * w + j]
            syms.append(v)
        c = Counter(syms)
        n = len(syms)
        h = -sum((cnt / n) * math.log2(cnt / n) for cnt in c.values())
        results[w] = h / w  # ratio of achieved entropy to max (w bits/symbol)
    return results


def main():
    samples = load_samples()
    print(f"testing {len(samples)} distinct payloads (largest interiors)\n")

    transforms_summary = Counter()
    total = 0

    for tag, n, payload in samples:
        interior = interior_of(payload)
        if interior is None or len(interior) < 32:
            continue
        total += 1
        print("=" * 100)
        print(f"{tag} n={n} payload_len={len(payload)} interior_len={len(interior)}")
        print("=" * 100)

        base_h = entropy(interior)
        base_bd = bit_density(interior)
        print(f"  RAW          entropy={base_h:.3f} bits/byte  bit_density={base_bd*100:.1f}%")

        key2 = bytes([n & 0xFF, 0x0A])
        key4 = bytes([n & 0xFF, 0x0A, n & 0xFF, 0x0A])

        variants = {
            "XOR pos (i&0xFF)": xor_position(interior),
            "XOR key2 [n,0x0a]": xor_key(interior, key2),
            "XOR key4 [n,0x0a,n,0x0a]": xor_key(interior, key4),
            "DELTA (mod 256)": delta(interior),
            "DELTA then XOR pos": xor_position(delta(interior)),
        }

        for name, out in variants.items():
            h = entropy(out)
            bd = bit_density(out)
            drop = base_h - h
            flag = "  <<< LEAD (entropy < 6.0)" if h < 6.0 else ""
            transforms_summary[name] += (1 if h < 6.0 else 0)
            print(f"  {name:26s} entropy={h:.3f} bits/byte  bit_density={bd*100:.1f}%  "
                  f"delta_vs_raw={drop:+.3f}{flag}")

        print("  fixed-width-symbol entropy ratio (raw interior; 1.0 = looks uniform at that width):")
        fw = fixed_width_test(interior)
        for w, ratio in sorted(fw.items()):
            flag = "  <<< possible width" if ratio < 0.85 else ""
            print(f"    width={w:2d}: ratio={ratio:.3f}{flag}")
        print()

    print("=" * 100)
    print(f"SUMMARY across {total} interiors: transforms achieving entropy<6.0 bits/byte on any sample:")
    for name, cnt in transforms_summary.items():
        print(f"  {name}: {cnt}/{total}")
    if not any(transforms_summary.values()):
        print("  NONE. No transform in this sweep reduced entropy below 6.0 bits/byte on any sample.")


if __name__ == "__main__":
    main()
