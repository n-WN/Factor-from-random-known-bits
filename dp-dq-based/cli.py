from __future__ import annotations

import argparse
import multiprocessing as mp
import os
import sys

try:
    # 作为包运行：python -m dp_dq_based.cli（若目录重命名为下划线）
    from .solver import run_search, E as DEFAULT_E, N as DEFAULT_N, CIPHERTEXT as DEFAULT_C
except Exception:
    # 作为脚本直跑：python dp-dq-based/cli.py
    import os
    import sys
    import importlib.util

    here = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, here)
    try:
        from solver import run_search, E as DEFAULT_E, N as DEFAULT_N, CIPHERTEXT as DEFAULT_C
    except Exception:
        # 终极兜底：按绝对路径加载 solver.py
        solver_path = os.path.join(here, "solver.py")
        spec = importlib.util.spec_from_file_location("solver", solver_path)
        solver = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(solver)
        run_search = solver.run_search
        DEFAULT_E = solver.E
        DEFAULT_N = solver.N
        DEFAULT_C = solver.CIPHERTEXT


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="RSA dp/dq optimized bit-search solver")
    parser.add_argument("--k1-min", type=int, default=55000)
    parser.add_argument("--k1-max", type=int, default=56000)
    parser.add_argument("--k2-min", type=int, default=49000)
    parser.add_argument("--k2-max", type=int, default=50000)
    parser.add_argument("--workers", type=int, default=int(os.environ.get("WORKERS", os.cpu_count() or 1)))
    parser.add_argument("--e", type=lambda s: int(s, 0), default=None, help="Public exponent (int, supports 0x base)")
    parser.add_argument("--n", type=lambda s: int(s, 0), default=None, help="Modulus N (int)")
    parser.add_argument("--c", type=lambda s: int(s, 0), default=None, help="Ciphertext C (int)")
    parser.add_argument("--dp", type=str, default=None, help="dp bit pattern (LSB-last string with ?)")
    parser.add_argument("--dq", type=str, default=None, help="dq bit pattern (LSB-last string with ?)")
    args = parser.parse_args(argv)

    try:
        mp.set_start_method("spawn", force=True)
    except RuntimeError:
        pass

    # Choose parameters (CLI overrides defaults)
    e = args.e if args.e is not None else DEFAULT_E
    n = args.n if args.n is not None else DEFAULT_N
    c = args.c if args.c is not None else DEFAULT_C
    dp_pattern = args.dp if args.dp is not None else None
    dq_pattern = args.dq if args.dq is not None else None

    result = run_search(
        k1_min=args.k1_min,
        k1_max=args.k1_max,
        k2_min=args.k2_min,
        k2_max=args.k2_max,
        workers=args.workers,
        e=e,
        n=n,
        c=c,
        dp_pattern=dp_pattern if dp_pattern is not None else None,
        dq_pattern=dq_pattern if dq_pattern is not None else None,
    )

    if result is None:
        print("No solution found in the given k1/k2 ranges.")
        return 1

    p, q, plaintext = result
    print(f"p = {p}")
    print(f"q = {q}")
    try:
        decoded = plaintext.decode()
    except Exception:
        decoded = repr(plaintext)
    print(f"plaintext = {decoded}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
