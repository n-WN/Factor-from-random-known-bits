from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Iterable, List, Optional, Sequence, Tuple



# Input constants from the original script
E = 0x10001
DP_PATTERN = (
    "??101101110001101000??????0???????1111?0??10?0??0?00?0??????01??1?00??1?011?11?0?10110????010??00?1?10?000????0??0?01??0???00??01?01?100?00110?0??0111?1???0110??00??????1?10?00?0?1????10110??0??110?0?001?????0110??00?01??11?00????000???0?????1?0???1?1??1?10????000?1??????01?10??1?0?0?11????1?00?001???1??1?????1011?0?1?????????0?1???111?01?010?0???10?00?0???00?1??1???00?10????111?0?1???11?110?0?????00110??000100?1????0???1?111010001?1?1???00?11???0?0?1?011?0??011?0???????1??0011100?1???1?1??1??00???0101???0?"
)
DQ_PATTERN = (
    "10??????????????????111011?1101100????0?01??1?01?0??0?000110??10?0??11?0???0??0?0?????1110???11??0?1??0???1101?10?0??10?010??11??0??0???0?????1?00????1?110????01??110101?0??1??1?1?0000?????01?11???1?0???11110????10??1??10??0??1011???000?11000?1?001?0?00?0??0000???0?010011??1??10?1?0?1??1101?1??1???111?00?00011????1?1?000000010?1?000???0??1???1?011??0??1?100??0?00?111??1??0010???1?0?110??1???1?00100?????10??????1?1101?111?0?????????1?1?001??1??110?1?1?1???1?10???0?0111000?10???????0?100?1?10?00??111????010?1"
)
N = 77956713622979317783761595054903981958011751094595501314491177382757729657611095418895882363723936522303701334485645032785352259197556402990449635873300021669658762637882700434079432155768745388920298118803003827231120408576526258417243630568234643852227224535788863216313553066059331134379012412201880568839
CIPHERTEXT = 6373402478226200743899445696426483055555702880465073264671889716957511631194331218010680752909232089491297245558959594952484242066243487601985639038704149982643910363538066540137001662216910771688217243126636396444036372309819771474215211720377034865803003448233174429246078453845273054750113438198122744673


# Utility functions
def int_to_bytes(n: int) -> bytes:
    n = int(n)
    if n == 0:
        return b"\x00"
    length = (n.bit_length() + 7) // 8
    return n.to_bytes(length, "big")


def parse_bits_lsb_first(pattern: str) -> List[int]:
    # Return list of bits (0/1) or -1 for unknown, LSB at index 0
    bits = []
    for ch in pattern[::-1]:  # reverse => LSB first
        if ch == "?":
            bits.append(-1)
        elif ch in ("0", "1"):
            bits.append(1 if ch == "1" else 0)
        else:
            raise ValueError(f"Invalid bit char: {ch}")
    return bits


@dataclass
class SearchConfig:
    e: int
    n: int
    c: int
    dp_bits: Sequence[int]
    dq_bits: Sequence[int]
    k1_min: int
    k1_max: int
    k2_min: int
    k2_max: int
    workers: int


def _dfs_search_for_kpair(
    e: int,
    n: int,
    c: int,
    dp_bits: Sequence[int],
    dq_bits: Sequence[int],
    k1: int,
    k2: int,
) -> Optional[Tuple[int, int, bytes]]:
    """Depth-first search over the dp/dq bit patterns for fixed k1/k2.

    Uses incremental updates under modulo 2^i to prune early.
    Returns (p, q, plaintext) on success or None.
    """

    L = min(len(dp_bits), len(dq_bits))
    if L < 2:
        return None

    # dp[0] and dq[0] must be 1 (odd). Enforce/validate against known bits.
    if (dp_bits[0] != -1 and dp_bits[0] != 1) or (dq_bits[0] != -1 and dq_bits[0] != 1):
        return None

    # Precompute masks
    masks = [0] * (L + 1)
    for i in range(1, L + 1):
        masks[i] = (1 << i) - 1

    # Precompute RHS mods via a single product
    k12n = (k1 * k2) * n
    rhs_mods = [0] * (L + 1)
    for i in range(1, L + 1):
        rhs_mods[i] = k12n & masks[i]

    # Initialize at i=1 with dp0=dq0=1
    i0 = 1
    dp_partial = 1
    dq_partial = 1
    A = (e * dp_partial - 1 + k1) & masks[i0]
    B = (e * dq_partial - 1 + k2) & masks[i0]

    # Quick reject for the first step (rarely prunes, but keep symmetry)
    if (A * B) & masks[i0] != rhs_mods[i0]:
        return None

    stack: List[Tuple[int, int, int, int, int]] = [(i0, dp_partial, dq_partial, A, B)]

    while stack:
        i, dp_part, dq_part, Ai, Bi = stack.pop()

        # Prune at current depth
        if (Ai * Bi) & masks[i] != rhs_mods[i]:
            continue

        if i == L:
            # Candidate complete dp/dq
            dp_true = dp_part
            dq_true = dq_part

            # Compute p, q from k1, k2
            num_p = e * dp_true - 1
            num_q = e * dq_true - 1
            if num_p % k1 != 0 or num_q % k2 != 0:
                continue
            p = num_p // k1 + 1
            q = num_q // k2 + 1
            if p <= 1 or q <= 1:
                continue
            if p * q != n:
                continue

            phi = (p - 1) * (q - 1)
            try:
                d = pow(e, -1, phi)
            except ValueError:
                continue
            m = pow(c, d, n)
            return (int(p), int(q), int_to_bytes(m))

        # Next bit index = i (0-based)
        idx = i
        mask_next = masks[i + 1]

        dp_opts = [dp_bits[idx]] if dp_bits[idx] != -1 else [0, 1]
        dq_opts = [dq_bits[idx]] if dq_bits[idx] != -1 else [0, 1]

        # Try combinations; push children onto stack
        for bdp in dp_opts:
            for bdq in dq_opts:
                dp_next = dp_part | (bdp << idx)
                dq_next = dq_part | (bdq << idx)
                # Recompute A, B at width i+1 to include carry contributions
                Ai_next = (e * dp_next - 1 + k1) & mask_next
                Bi_next = (e * dq_next - 1 + k2) & mask_next
                stack.append((i + 1, dp_next, dq_next, Ai_next, Bi_next))

    return None


_G_DP_BITS: Tuple[int, ...] | None = None
_G_DQ_BITS: Tuple[int, ...] | None = None
_G_E: int | None = None
_G_N: int | None = None
_G_C: int | None = None


def _init_worker(dp_bits: Tuple[int, ...], dq_bits: Tuple[int, ...], e: int, n: int, c: int) -> None:
    global _G_DP_BITS, _G_DQ_BITS, _G_E, _G_N, _G_C
    _G_DP_BITS = dp_bits
    _G_DQ_BITS = dq_bits
    _G_E = e
    _G_N = n
    _G_C = c


def _search_worker_k1(args: Tuple[int, int, int]) -> Optional[Tuple[int, int, bytes]]:
    k1, k2_min, k2_max = args
    dp_bits = _G_DP_BITS
    dq_bits = _G_DQ_BITS
    e = _G_E
    n = _G_N
    c = _G_C
    if dp_bits is None or dq_bits is None or e is None or n is None or c is None:
        return None
    try:
        for k2 in range(k2_min, k2_max + 1):
            res = _dfs_search_for_kpair(e, n, c, dp_bits, dq_bits, k1, k2)
            if res is not None:
                return res
        return None
    except Exception:
        return None


def run_search(
    k1_min: int = 55000,
    k1_max: int = 56000,
    k2_min: int = 49000,
    k2_max: int = 50000,
    e: int = E,
    n: int = N,
    c: int = CIPHERTEXT,
    dp_pattern: Optional[str] = DP_PATTERN,
    dq_pattern: Optional[str] = DQ_PATTERN,
    workers: Optional[int] = None,
    prefer_fork: Optional[bool] = None,
) -> Optional[Tuple[int, int, bytes]]:
    if dp_pattern is None:
        dp_pattern = DP_PATTERN
    if dq_pattern is None:
        dq_pattern = DQ_PATTERN
    dp_bits = tuple(parse_bits_lsb_first(dp_pattern))
    dq_bits = tuple(parse_bits_lsb_first(dq_pattern))

    if workers is None:
        # Prefer performance-core count on macOS if available
        if sys_platform_is_macos():
            perf = detect_macos_perf_cores()
            if perf:
                workers = perf
            else:
                workers = max(1, int(os.environ.get("WORKERS", os.cpu_count() or 1)))
        else:
            workers = max(1, int(os.environ.get("WORKERS", os.cpu_count() or 1)))

    # Prepare tasks grouped by k1; each task iterates k2 range internally to avoid 1e6 futures
    tasks: List[Tuple[int, int, int]] = []
    for k1 in range(k1_min, k1_max + 1):
        tasks.append((k1, k2_min, k2_max))

    # Parallel map; stop at first success
    from concurrent.futures import ProcessPoolExecutor, as_completed
    import multiprocessing as mp

    # Choose start method
    if prefer_fork is None:
        prefer_fork = os.environ.get("RSA_FORK", "0") == "1"
    try:
        mp_ctx = mp.get_context("fork" if (prefer_fork and sys_platform_is_macos()) else None)
    except ValueError:
        mp_ctx = mp.get_context(None)

    with ProcessPoolExecutor(
        max_workers=min(workers, max(1, k1_max - k1_min + 1)),
        mp_context=mp_ctx,
        initializer=_init_worker,
        initargs=(dp_bits, dq_bits, e, n, c),
    ) as ex:
        futs = [ex.submit(_search_worker_k1, t) for t in tasks]
        for fut in as_completed(futs):
            res = fut.result()
            if res is not None:
                # Cancel outstanding work
                for f in futs:
                    if not f.done():
                        f.cancel()
                return res
    return None


def sys_platform_is_macos() -> bool:
    try:
        import sys
        return sys.platform == "darwin"
    except Exception:
        return False


def detect_macos_perf_cores() -> Optional[int]:
    import subprocess
    for key in (
        "hw.perflevel0.logicalcpu",
        "hw.perflevel0.physicalcpu",
    ):
        try:
            out = subprocess.check_output(["sysctl", "-n", key], text=True).strip()
            val = int(out)
            if val > 0:
                return val
        except Exception:
            continue
    return None
