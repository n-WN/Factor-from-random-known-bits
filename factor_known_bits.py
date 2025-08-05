# 文件: factor_known_bits.py
import gmpy2
import sys
from typing import List, Optional, Tuple

# 将 gmpy2 的整数类型别名为 Int，方便阅读
Int = gmpy2.mpz

def _factor_dfs(
    n: Int,
    p_bits: List[int],
    q_bits: List[int],
    bit_len: int,
    k: int,
    p_so_far: Int,
    q_so_far: Int,
) -> Optional[Tuple[Int, Int]]:
    """内部DFS辅助函数"""
    if k == bit_len:
        if p_so_far * q_so_far == n:
            return p_so_far, q_so_far
        return None
    if k >= len(p_bits):
        return None

    p_k, q_k = p_bits[k], q_bits[k]
    p_choices = [0, 1] if p_k == -1 else [p_k]
    q_choices = [0, 1] if q_k == -1 else [q_k]
    k_power_of_2 = Int(1) << k
    mask = (Int(1) << (k + 1)) - 1
    n_masked = n & mask

    for p_choice in p_choices:
        p_next = p_so_far + p_choice * k_power_of_2
        for q_choice in q_choices:
            q_next = q_so_far + q_choice * k_power_of_2
            if (p_next * q_next) & mask == n_masked:
                result = _factor_dfs(n, p_bits, q_bits, bit_len, k + 1, p_next, q_next)
                if result:
                    return result
    return None

def _prepare_and_run(n_int: int, p_bits_be: List[int], q_bits_be: List[int]) -> Optional[Tuple[int, int]]:
    """准备并运行DFS的核心逻辑"""
    n = gmpy2.mpz(n_int)
    bit_len = (n.bit_length() + 1) // 2
    
    p_padded = [0] * (bit_len - len(p_bits_be)) + p_bits_be
    q_padded = [0] * (bit_len - len(q_bits_be)) + q_bits_be

    p_bits_le = p_padded[::-1]
    q_bits_le = q_padded[::-1]

    current_limit = sys.getrecursionlimit()
    if bit_len + 50 > current_limit:
        sys.setrecursionlimit(bit_len + 50)

    result_mpz = _factor_dfs(n, p_bits_le, q_bits_le, bit_len, 0, gmpy2.mpz(0), gmpy2.mpz(0))

    if result_mpz:
        p, q = result_mpz
        if p * q == n:
            return int(p), int(q)
        elif q * p == n:
            return int(q), int(p)
    return None

def from_vector(n: int, p_bits: List[int], q_bits: List[int]) -> Optional[Tuple[int, int]]:
    """通过比特向量分解 n"""
    return _prepare_and_run(n, p_bits, q_bits)

def from_str(n: int, p_bits_str: str, q_bits_str: str) -> Optional[Tuple[int, int]]:
    """通过比特字符串分解 n"""
    def parse_str(s: str) -> List[int]:
        return [0 if c == '0' else 1 if c == '1' else -1 for c in s]
    return _prepare_and_run(n, parse_str(p_bits_str), parse_str(q_bits_str))
