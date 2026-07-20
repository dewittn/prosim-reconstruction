#!/usr/bin/env python3
"""TEST 3: Rice/Golomb/Elias-gamma/delta/unary decode of the ID04 16-byte
sparse-bit prefix, confirmed present byte-for-byte identical at offset 4366
in prosim.xtc and 4896 in prosim1.xtc (start of the 66-byte ID04 constant
block): 30 48 29 00 80 c0 20 30 08 09 01 80 00 00 00 09

Tries every combination of:
  - bit order: MSB-first per byte / LSB-first per byte
  - unary convention: run-of-0s terminated by 1 / run-of-1s terminated by 0
  - Golomb-Rice k = 0..8
  - Elias gamma, Elias delta
Reports the decoded integer sequence for each, how many bits were consumed
before the stream became implausible (unary run > 32 with no terminator, or
a code longer than the region), and flags any result that looks like
plausible game data (values 1-26, monotonic runs, hits near known constants:
week numbers, operator ids, 40/60 split, common demand/cost magnitudes).
"""

PREFIX_HEX = "3048290080c020300809018000000009"
BLOCK = bytes.fromhex(PREFIX_HEX)
assert len(BLOCK) == 16


def bits_msb(data):
    out = []
    for byte in data:
        for i in range(7, -1, -1):
            out.append((byte >> i) & 1)
    return out


def bits_lsb(data):
    out = []
    for byte in data:
        for i in range(0, 8):
            out.append((byte >> i) & 1)
    return out


class BitReader:
    def __init__(self, bits):
        self.bits = bits
        self.pos = 0

    def eof(self):
        return self.pos >= len(self.bits)

    def read_bit(self):
        if self.eof():
            return None
        b = self.bits[self.pos]
        self.pos += 1
        return b

    def read_bits(self, n):
        if self.pos + n > len(self.bits):
            return None
        v = 0
        for _ in range(n):
            v = (v << 1) | self.bits[self.pos]
            self.pos += 1
        return v

    def read_unary(self, terminator, max_run=40):
        """Count bits != terminator until we see `terminator`. Returns run length,
        or None if we exceed max_run (runaway) or hit eof."""
        run = 0
        while True:
            b = self.read_bit()
            if b is None:
                return None
            if b == terminator:
                return run
            run += 1
            if run > max_run:
                return None


def decode_rice_stream(bits, k, unary_terminator):
    """Rice code: unary quotient (terminated by `unary_terminator`), then k-bit
    remainder. value = quotient * 2^k + remainder."""
    r = BitReader(bits)
    vals = []
    starts = []
    while not r.eof():
        start = r.pos
        q = r.read_unary(unary_terminator)
        if q is None:
            break
        if k > 0:
            rem = r.read_bits(k)
            if rem is None:
                break
        else:
            rem = 0
        vals.append(q * (1 << k) + rem)
        starts.append(start)
    return vals, r.pos


def decode_elias_gamma_stream(bits):
    r = BitReader(bits)
    vals = []
    while not r.eof():
        nzeros = r.read_unary(1)  # count 0s until a 1
        if nzeros is None:
            break
        if nzeros == 0:
            vals.append(1)
            continue
        rest = r.read_bits(nzeros)
        if rest is None:
            break
        val = (1 << nzeros) | rest
        vals.append(val)
    return vals, r.pos


def decode_elias_delta_stream(bits):
    r = BitReader(bits)
    vals = []
    while not r.eof():
        nzeros = r.read_unary(1)
        if nzeros is None:
            break
        if nzeros == 0:
            length = 1
        else:
            lenbits = r.read_bits(nzeros)
            if lenbits is None:
                break
            length = (1 << nzeros) | lenbits
        if length - 1 == 0:
            val = 1
        else:
            rest = r.read_bits(length - 1)
            if rest is None:
                break
            val = (1 << (length - 1)) | rest
        vals.append(val)
    return vals, r.pos


def plausibility(vals):
    if not vals:
        return "empty"
    small = sum(1 for v in vals if 1 <= v <= 26)
    monotonic = sum(1 for a, b in zip(vals, vals[1:]) if b >= a)
    hits = sum(1 for v in vals if v in (40, 60, 100))
    notes = []
    if len(vals) >= 3 and small / len(vals) > 0.6:
        notes.append(f"{small}/{len(vals)} in [1,26] (op-id-like)")
    if len(vals) >= 3 and monotonic / max(1, len(vals) - 1) > 0.8:
        notes.append("mostly monotonic")
    if hits:
        notes.append(f"{hits} hits on 40/60/100")
    return "; ".join(notes) if notes else "no obvious structure"


def main():
    print(f"BLOCK (16 bytes): {BLOCK.hex(' ')}")
    print(f"binary: {' '.join(format(b, '08b') for b in BLOCK)}")
    print()

    orders = {"MSB-first": bits_msb(BLOCK), "LSB-first": bits_lsb(BLOCK)}

    for order_name, bits in orders.items():
        print("=" * 100)
        print(f"BIT ORDER: {order_name}  ({len(bits)} bits)")
        print("=" * 100)

        print("-- unary (both conventions) --")
        for term in (1, 0):
            r = BitReader(bits)
            runs = []
            while not r.eof():
                run = r.read_unary(term, max_run=128)
                if run is None:
                    break
                runs.append(run)
            print(f"  unary(terminator={term}): runs={runs[:20]} consumed={r.pos}/{len(bits)}  "
                  f"plausible={plausibility(runs)}")

        print("-- Golomb-Rice k=0..8, both unary conventions --")
        for term in (1, 0):
            for k in range(0, 9):
                vals, consumed = decode_rice_stream(bits, k, term)
                if len(vals) < 2:
                    continue
                tag = f"Rice(k={k},term={term})"
                print(f"  {tag:22s} n={len(vals):3d} consumed={consumed:4d}/{len(bits)}  "
                      f"vals={vals[:16]}{'...' if len(vals) > 16 else ''}  {plausibility(vals)}")

        print("-- Elias gamma --")
        vals, consumed = decode_elias_gamma_stream(bits)
        print(f"  n={len(vals)} consumed={consumed}/{len(bits)}  vals={vals[:20]}  {plausibility(vals)}")

        print("-- Elias delta --")
        vals, consumed = decode_elias_delta_stream(bits)
        print(f"  n={len(vals)} consumed={consumed}/{len(bits)}  vals={vals[:20]}  {plausibility(vals)}")
        print()


if __name__ == "__main__":
    main()
