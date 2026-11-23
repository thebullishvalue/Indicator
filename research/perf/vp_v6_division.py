"""pragyam.pine's binary search under Pine v6 division ((lo+hi)/2 is fractional), with array indices truncated.
Does inserting keys with it keep them sorted, and does it find keys that are there?"""
import random, math

def locate_v6(keys, k):
    lo, hi, pos, found = 0, len(keys) - 1, 0, False
    while lo <= hi:
        mid = (lo + hi) / 2                      # v6: fractional
        mk = keys[int(mid)]                      # index truncated
        if mk == k: pos, found = mid, True; break
        elif mk < k: lo = mid + 1
        else: hi = mid - 1
    if not found: pos = lo
    return int(pos), found

random.seed(3)
unsorted = missed = sessions = 0
for s in range(2000):
    keys = []; ok = True
    for _ in range(random.randint(5, 300)):
        k = random.randint(0, 120)
        pos, f = locate_v6(keys, k)
        if not f: keys.insert(pos, k)
    sessions += 1
    if keys != sorted(keys) or len(set(keys)) != len(keys): unsorted += 1
    if any(not locate_v6(keys, k)[1] for k in keys): missed += 1
print(f"{sessions} sessions: keys out of order or duplicated in {unsorted}, a present key not found in {missed}")
