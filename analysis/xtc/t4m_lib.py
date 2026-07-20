#!/usr/bin/env python3
"""Encoding/decoding + transform primitives for the known-plaintext transform hunt.

Encodings: MBF32/MBF64 (QuickBasic/GW-BASIC Microsoft Binary Format), VB Currency,
scaled integers (u16/u32/i16/i32, LE/BE, x1/x10/x100), fixed-point 16.16 / 8.24,
packed BCD (both nibble orders).

Transforms: XOR (0x01-0xFF), byte-wise delta decode (cumulative sum), nibble swap,
bit-reverse-per-byte, high-bit-strip (7-bit stream), base-128 VLQ (MIDI-style).
"""
import struct
import math


# ---------------- Microsoft Binary Format floats ----------------
# Memory layout (low->high address): mantissa low bytes ..., (sign|mantissa-high), exponent.
# value = sign * (0x800000|mantissa24) * 2**(exp_byte - 128 - 24)   [single, 4 bytes]
# value = sign * (0x80..|mantissa56) * 2**(exp_byte - 128 - 56)     [double, 8 bytes]

def mbf32_decode(b):
    b0, b1, b2, b3 = b[0], b[1], b[2], b[3]
    if b3 == 0:
        return 0.0
    sign = -1 if (b2 & 0x80) else 1
    exponent = b3 - 128 - 24
    mant = 0x800000 | ((b2 & 0x7f) << 16) | (b1 << 8) | b0
    return sign * mant * (2.0 ** exponent)


def mbf32_encode(v):
    if v == 0:
        return bytes(4)
    sign = 0x80 if v < 0 else 0
    v = abs(v)
    exp = math.floor(math.log2(v))
    exponent = exp - 23
    mant = round(v / (2.0 ** exponent))
    if mant >= (1 << 24):
        mant >>= 1
        exponent += 1
    elif mant < (1 << 23):
        mant <<= 1
        exponent -= 1
    b3 = exponent + 128 + 24
    if b3 < 1 or b3 > 255:
        return None
    b2 = ((mant >> 16) & 0x7f) | sign
    b1 = (mant >> 8) & 0xff
    b0 = mant & 0xff
    return bytes([b0, b1, b2, b3])


def mbf64_decode(b):
    b0, b1, b2, b3, b4, b5, b6, b7 = b[0], b[1], b[2], b[3], b[4], b[5], b[6], b[7]
    if b7 == 0:
        return 0.0
    sign = -1 if (b6 & 0x80) else 1
    exponent = b7 - 128 - 56
    mant = (0x80000000000000 | ((b6 & 0x7f) << 48) | (b5 << 40) | (b4 << 32)
            | (b3 << 24) | (b2 << 16) | (b1 << 8) | b0)
    return sign * mant * (2.0 ** exponent)


def mbf64_encode(v):
    if v == 0:
        return bytes(8)
    sign = 0x80 if v < 0 else 0
    v = abs(v)
    exp = math.floor(math.log2(v))
    exponent = exp - 55
    mant = round(v / (2.0 ** exponent))
    if mant >= (1 << 56):
        mant >>= 1
        exponent += 1
    elif mant < (1 << 55):
        mant <<= 1
        exponent -= 1
    b7 = exponent + 128 + 56
    if b7 < 1 or b7 > 255:
        return None
    b6 = ((mant >> 48) & 0x7f) | sign
    b5 = (mant >> 40) & 0xff
    b4 = (mant >> 32) & 0xff
    b3 = (mant >> 24) & 0xff
    b2 = (mant >> 16) & 0xff
    b1 = (mant >> 8) & 0xff
    b0 = mant & 0xff
    return bytes([b0, b1, b2, b3, b4, b5, b6, b7])


def _self_test_mbf():
    # 1.0 -> 00 00 00 81 (well-known reference value)
    assert mbf32_encode(1.0) == bytes([0x00, 0x00, 0x00, 0x81]), mbf32_encode(1.0).hex()
    assert abs(mbf32_decode(bytes([0x00, 0x00, 0x00, 0x81])) - 1.0) < 1e-9
    # round-trip a batch of realistic values
    for v in [0.850856, 0.807425, 1.03125, 10003.68, 10423.6, 3823.6, 1999.46,
              2707.5, 22775.2, 2.80045, 416.0, -33.25, 0.1, 12345.6789]:
        enc = mbf32_encode(v)
        dec = mbf32_decode(enc)
        rel = abs(dec - v) / max(abs(v), 1e-9)
        assert rel < 1e-5, f"mbf32 roundtrip fail {v} -> {dec} rel={rel}"
        enc8 = mbf64_encode(v)
        dec8 = mbf64_decode(enc8)
        rel8 = abs(dec8 - v) / max(abs(v), 1e-9)
        assert rel8 < 1e-9, f"mbf64 roundtrip fail {v} -> {dec8} rel={rel8}"
    return True


# ---------------- VB Currency ----------------
def vb_currency_encode(v):
    iv = round(v * 10000)
    if not (-(1 << 63) <= iv < (1 << 63)):
        return None
    return struct.pack("<q", iv)


# ---------------- Scaled integers ----------------
def scaled_int_variants(v):
    out = {}
    for scale in (1, 10, 100):
        iv = round(v * scale)
        for width, fmt in ((2, 'H'), (4, 'I')):
            for endc, estr in (('<', 'LE'), ('>', 'BE')):
                lo, hi = 0, 2 ** (8 * width) - 1
                if lo <= iv <= hi:
                    out[f"u{width*8}{estr}_x{scale}"] = struct.pack(endc + fmt, iv)
                slo, shi = -(2 ** (8 * width - 1)), 2 ** (8 * width - 1) - 1
                if slo <= iv <= shi:
                    out[f"i{width*8}{estr}_x{scale}"] = struct.pack(endc + fmt.lower(), iv)
    return out


# ---------------- Fixed point ----------------
def fixed_point_variants(v):
    out = {}
    for frac, name in ((16, '16.16'), (24, '8.24')):
        iv = round(v * (1 << frac))
        for endc, estr in (('<', 'LE'), ('>', 'BE')):
            if -(1 << 31) <= iv < (1 << 31):
                out[f"fx{name}_{estr}_s32"] = struct.pack(endc + 'i', iv)
            if 0 <= iv < (1 << 32):
                out[f"fx{name}_{estr}_u32"] = struct.pack(endc + 'I', iv)
    return out


# ---------------- Packed BCD ----------------
def bcd_variants(int_value):
    if int_value is None or int_value < 0:
        return {}
    digits = str(int(round(int_value)))
    if len(digits) % 2 == 1:
        digits = '0' + digits
    nbytes = len(digits) // 2
    normal = bytes((int(digits[2 * i]) << 4) | int(digits[2 * i + 1]) for i in range(nbytes))
    swapped = bytes((int(digits[2 * i + 1]) << 4) | int(digits[2 * i]) for i in range(nbytes))
    out = {"bcd_normal": normal}
    if swapped != normal:
        out["bcd_swapped"] = swapped
    return out


# ---------------- Transforms ----------------
def xor_bytes(data, k):
    if k == 0:
        return bytes(data)
    return bytes(b ^ k for b in data)


_BITREV = bytes(int(f"{i:08b}"[::-1], 2) for i in range(256))


def bit_reverse(data):
    return bytes(_BITREV[b] for b in data)


def nibble_swap(data):
    return bytes(((b & 0x0f) << 4) | ((b & 0xf0) >> 4) for b in data)


def delta_decode(data):
    out = bytearray(len(data))
    acc = 0
    for i, b in enumerate(data):
        acc = (acc + b) & 0xff
        out[i] = acc
    return bytes(out)


def high_bit_strip(data):
    return bytes(b & 0x7f for b in data)


def find_all(buf, pattern):
    """Return all start offsets of pattern in buf (allow overlap)."""
    if not pattern:
        return []
    out = []
    start = 0
    while True:
        i = buf.find(pattern, start)
        if i == -1:
            break
        out.append(i)
        start = i + 1
    return out


def chance_hits(buflen, patlen):
    """Expected number of matches of a random patlen-byte pattern in buflen
    bytes of uniform-random data (approx, ignores overlap correlations)."""
    space = 256 ** patlen
    n_positions = max(0, buflen - patlen + 1)
    return n_positions / space


def binom_logsf_upper(n, k, p):
    """Rough -log10(P(X>=k)) for X~Binomial(n,p), p small. Uses Poisson approx
    lambda=n*p when p is small (valid here since p = 1/256^d is tiny)."""
    lam = n * p
    if lam <= 0:
        return float('inf') if k > 0 else 0.0
    # log P(X>=k) ~ log P(X=k) for tiny lam and k small (dominant term), else sum a few terms
    from math import log, lgamma, exp
    logp = 0.0
    total = 0.0
    for i in range(0, max(k, 1) + 5):
        if i < k:
            continue
        term = -lam + i * log(lam) - lgamma(i + 1)
        total += exp(term)
    if total <= 0:
        return float('inf')
    return -total and (-1) * (total)


if __name__ == "__main__":
    ok = _self_test_mbf()
    print("MBF self-test:", "PASS" if ok else "FAIL")
    # quick sanity on scaled/bcd/fixed
    print("scaled_int_variants(410):", {k: v.hex() for k, v in scaled_int_variants(410).items()})
    print("bcd_variants(410):", {k: v.hex() for k, v in bcd_variants(410).items()})
    print("fixed_point_variants(0.850856):", {k: v.hex() for k, v in fixed_point_variants(0.850856).items()})
    print("vb_currency_encode(10003.68):", vb_currency_encode(10003.68).hex())
