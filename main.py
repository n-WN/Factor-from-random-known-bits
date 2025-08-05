import gmpy2
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
    """
    使用深度优先搜索（DFS）和剪枝来寻找 p 和 q。
    这是一个内部辅助函数。
    """
    # 基本情况：所有比特位都已处理
    if k == bit_len:
        if p_so_far * q_so_far == n:
            return p_so_far, q_so_far
        return None

    # 为了防止在超长时间的递归中堆栈溢出，可以设置一个实际的深度限制
    # 对于这个大数例子，Python的默认递归限制（通常是1000）可能不够
    if k >= bit_len:
         # 确保不会超出 p_bits/q_bits 的索引
         return None

    # 确定当前比特位的可能取值
    p_k = p_bits[k]
    q_k = q_bits[k]

    p_choices = [0, 1] if p_k == -1 else [p_k]
    q_choices = [0, 1] if q_k == -1 else [q_k]
    
    # 2^k
    k_power_of_2 = Int(1) << k

    for p_choice in p_choices:
        for q_choice in q_choices:
            p_next = p_so_far + p_choice * k_power_of_2
            q_next = q_so_far + q_choice * k_power_of_2

            # 剪枝关键步骤
            mask = (Int(1) << (k + 1)) - 1
            if (p_next * q_next) & mask == n & mask:
                # 如果条件满足，则递归到下一个比特位
                result = _factor_dfs(n, p_bits, q_bits, bit_len, k + 1, p_next, q_next)
                if result:
                    return result

    return None

def _prepare_and_run(n_int: int, p_bits_be: List[int], q_bits_be: List[int]) -> Optional[Tuple[int, int]]:
    """
    准备输入并启动 DFS 搜索的核心逻辑。
    """
    n = gmpy2.mpz(n_int)
    
    # --- 关键修正 ---
    # 使用 n 的比特长度来确定 p 和 q 的比特长度，这更鲁棒
    bit_len = (n.bit_length() + 1) // 2
    
    # 填充较短的列表，使其与正确的 bit_len 匹配（在大端序前端填充0）
    p_padded = [0] * (bit_len - len(p_bits_be)) + p_bits_be
    q_padded = [0] * (bit_len - len(q_bits_be)) + q_bits_be

    # 将比特列表反转为小端序（LSB-first），方便从第0位开始处理
    p_bits_le = p_padded[::-1]
    q_bits_le = q_padded[::-1]

    # 初始的 p 和 q 值为 0
    p_initial = gmpy2.mpz(0)
    q_initial = gmpy2.mpz(0)

    # 增加Python的递归深度限制以处理高比特长度
    import sys
    # current_limit = sys.getrecursionlimit()
    # if bit_len + 50 > current_limit:
    #     sys.setrecursionlimit(bit_len + 50)

    result_mpz = _factor_dfs(n, p_bits_le, q_bits_le, bit_len, 0, p_initial, q_initial)

    if result_mpz:
        p, q = result_mpz
        if p * q == n:
            return int(p), int(q)
        elif q * p == n:
            return int(q), int(p)
    
    return None

def from_vector(n: int, p_bits: List[int], q_bits: List[int]) -> Optional[Tuple[int, int]]:
    return _prepare_and_run(n, p_bits, q_bits)

def from_str(n: int, p_bits_str: str, q_bits_str: str) -> Optional[Tuple[int, int]]:
    def parse_str(s: str) -> List[int]:
        bits = []
        for char in s:
            if char == '0':
                bits.append(0)
            elif char == '1':
                bits.append(1)
            else: # '_' or '?'
                bits.append(-1)
        return bits

    p_bits_vec = parse_str(p_bits_str)
    q_bits_vec = parse_str(q_bits_str)
    
    return _prepare_and_run(n, p_bits_vec, q_bits_vec)

# --- 以下是示例和测试 ---
if __name__ == '__main__':
    # 增加递归深度限制
    import sys
    sys.setrecursionlimit(2000)

    print("--- Running examples from the prompt ---")
    
    # 示例 1: from_str
    n1 = 91
    p_str1 = "110_"  # p=13 -> 1101
    q_str1 = "0__1"  # q=7  -> 0111
    result1 = from_str(n1, p_str1, q_str1)
    print(f"factor.from_str({n1}, \"{p_str1}\", \"{q_str1}\")")
    if result1:
        p, q = result1
        print(f"  -> ({p}, {q})")
        assert p * q == n1
    else:
        print("  -> Not found")
    print("-" * 20)

    # 示例 2: from_vector
    n2 = 91
    p_vec2 = [1, 1, 0, -1]
    q_vec2 = [0, -1, -1, 1]
    result2 = from_vector(n2, p_vec2, q_vec2)
    print(f"factor.from_vector({n2}, {p_vec2}, {q_vec2})")
    if result2:
        p, q = result2
        print(f"  -> ({p}, {q})")
        assert p * q == n2
    else:
        print("  -> Not found")
    print("-" * 20)
    # 示例 3: 更大的数字
    run_large_example = False
    if run_large_example:
        n3 = 104158954646372695568095796310479805403678314919693272509836778997179683485437763692891984254171869987446475357518587344178264028334102088429629785065036660148146855007349113784322098795994839040721664806905084554147298456659074384855277678993200563966327086005547016327991986225930798076081014377904788085807
        p_str3 = "1010101111000___11000___11100___11010___0___0___0___100110000___0___0___0___11000___0___0___110110010___11001100100111010___100011000___0___0___0___11111000111111100___1101110010000___0___0___0___10110___0___0___0___0___0___1100101111000___0___1001111011110___0___10000___0___0___11010___1010101110110___0___0___0___0___10010___1011101011100___110111010___0___0___0___101010110___0___10000___1000101011000___0___0___0___101010000___11010___111010000___0___11110___0___10010___111010010___0___0___10100___0___0___"
        q_str3 = "110111010___111011110___0___1000100110001110100111100___0___10110___11000___0___10110___11100___10000___0___0___11111100110010100___10000___11100___0___110010110___101110010___10010___11110___11110___0___1101111011000___101010110___10100___0___10100___1010101011010___0___0___100110110___0___10000___0___0___1000101110010___1111110010110___0___0___0___101110100___0___1100101111000___10100___0___0___0___0___0___0___10010___0___0___10100___10010___0___0___0___101011110___0___111110000___0___11110___0___10100___"
        
        print(f"Factoring large n (this will take a very long time in Python)...")
        print(f"Correct bit_len: {(n3.bit_length() + 1) // 2}")
        print(f"p unknown bits: {p_str3.count('_') + p_str3.count('?')}")
        print(f"q unknown bits: {q_str3.count('_') + q_str3.count('?')}")

        import time
        start_time = time.time()
        result3 = from_str(n3, p_str3, q_str3)
        end_time = time.time()
        
        if result3:
            p, q = result3
            print(f"  -> Found factors in {end_time - start_time:.2f} seconds.")
            assert p * q == n3 or q*p==n3
        else:
            print(f"  -> Not found after {end_time - start_time:.2f} seconds.")
    else:
        print("Skipping large example due to performance reasons in Python.")
