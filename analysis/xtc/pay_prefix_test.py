#!/usr/bin/env python3
"""For each identity with multiple payload lengths, test if shorter payloads are
byte-identical prefixes of longer ones (growing log/list hypothesis)."""
import sys
sys.path.insert(0, "/Users/dewittn/Programing/dewittn/Other/prosim-reconstruction/analysis/xtc")
from pay_anchor import FILES, parse_body, chain_walk, get_payloads
from collections import defaultdict

def main():
    id_to_payloads = defaultdict(set)
    for tag, cfg in FILES.items():
        data = open(cfg["path"], "rb").read()
        body = parse_body(data, cfg["body_start"], cfg["body_end"])
        markers = chain_walk(data, cfg["pk_start"], cfg["maxn"])
        payloads = get_payloads(data, markers, len(data))
        for (kind, fl), (n, payload) in zip(body, payloads):
            if kind != "15":
                continue
            f1, f2, f3, f4 = fl
            key = (round(f1, 6), round(f2, 6))
            id_to_payloads[key].add(bytes(payload))

    for key, payset in sorted(id_to_payloads.items()):
        pl = sorted(payset, key=len)
        if len(pl) < 2:
            continue
        print(f"id={key}  lens={[len(p) for p in pl]}")
        for i in range(len(pl) - 1):
            shorter, longer = pl[i], pl[i+1]
            is_prefix = longer.startswith(shorter)
            # also check suffix / other alignment
            is_suffix = longer.endswith(shorter)
            # find longest common prefix length
            lcp = 0
            for a, b in zip(shorter, longer):
                if a == b:
                    lcp += 1
                else:
                    break
            print(f"    {len(shorter)} -> {len(longer)}: is_prefix={is_prefix} is_suffix={is_suffix} common_prefix_len={lcp}/{len(shorter)}")
            if not is_prefix and lcp > 0:
                print(f"       divergence at byte {lcp}: shorter[{lcp}:{lcp+8}]={shorter[lcp:lcp+8].hex()} longer[{lcp}:{lcp+8}]={longer[lcp:lcp+8].hex()}")

if __name__ == "__main__":
    main()
