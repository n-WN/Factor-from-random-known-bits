# 文件: factor_known_bits.py
import gmpy2
import sys
from typing import List, Optional, Tuple, Dict, Any

# 将 gmpy2 的整数类型别名为 Int，方便阅读
Int = gmpy2.mpz

class FactorResult:
    """结果类，包含分解结果和详细的错误信息"""
    def __init__(self, factors: Optional[Tuple[int, int]] = None, 
                 success: bool = False, 
                 error_info: Optional[Dict[str, Any]] = None):
        self.factors = factors
        self.success = success
        self.error_info = error_info or {}
    
    def __bool__(self):
        return self.success
    
    def __iter__(self):
        if self.factors:
            return iter(self.factors)
        return iter(())

def _factor_dfs(
    n: Int,
    p_bits: List[int],
    q_bits: List[int],
    bit_len: int,
    k: int,
    p_so_far: Int,
    q_so_far: Int,
    progress_tracker: Dict[str, Any]
) -> Optional[Tuple[Int, Int]]:
    """内部DFS辅助函数，增加了搜索进度追踪"""
    # 更新最大搜索深度
    progress_tracker['max_depth_reached'] = max(progress_tracker.get('max_depth_reached', 0), k)
    progress_tracker['total_nodes_explored'] = progress_tracker.get('total_nodes_explored', 0) + 1
    
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
                result = _factor_dfs(n, p_bits, q_bits, bit_len, k + 1, p_next, q_next, progress_tracker)
                if result:
                    return result
            else:
                # 记录在哪个位置发生了剪枝
                progress_tracker['pruned_at_depths'] = progress_tracker.get('pruned_at_depths', [])
                progress_tracker['pruned_at_depths'].append(k)
    return None

def _prepare_and_run(n_int: int, p_bits_be: List[int], q_bits_be: List[int], 
                    try_reverse: bool = True) -> FactorResult:
    """准备并运行DFS的核心逻辑，增加了错误追踪和自动重试功能"""
    n = gmpy2.mpz(n_int)
    bit_len = (n.bit_length() + 1) // 2
    
    def _try_factorization(p_bits: List[int], q_bits: List[int], endianness: str) -> FactorResult:
        """尝试分解，返回详细结果"""
        progress_tracker = {
            'max_depth_reached': 0,
            'total_nodes_explored': 0,
            'pruned_at_depths': [],
            'endianness': endianness
        }
        
        p_padded = [0] * (bit_len - len(p_bits)) + p_bits
        q_padded = [0] * (bit_len - len(q_bits)) + q_bits

        p_bits_le = p_padded[::-1]
        q_bits_le = q_padded[::-1]

        current_limit = sys.getrecursionlimit()
        if bit_len + 50 > current_limit:
            sys.setrecursionlimit(bit_len + 50)

        result_mpz = _factor_dfs(n, p_bits_le, q_bits_le, bit_len, 0, 
                                gmpy2.mpz(0), gmpy2.mpz(0), progress_tracker)

        if result_mpz:
            p, q = result_mpz
            if p * q == n:
                return FactorResult(factors=(int(p), int(q)), success=True, 
                                  error_info={'progress': progress_tracker})
            elif q * p == n:
                return FactorResult(factors=(int(q), int(p)), success=True,
                                  error_info={'progress': progress_tracker})
        
        # 分解失败，返回详细的错误信息
        error_info = {
            'progress': progress_tracker,
            'bit_length': bit_len,
            'search_completed': progress_tracker['max_depth_reached'] == bit_len,
            'endianness_tried': endianness
        }
        
        return FactorResult(success=False, error_info=error_info)
    
    # 首先尝试原始bit顺序
    result = _try_factorization(p_bits_be, q_bits_be, 'big-endian')
    
    if result.success:
        return result
    
    # 如果失败且允许尝试反向，则尝试反向endianness
    if try_reverse:
        p_bits_reversed = p_bits_be[::-1]
        q_bits_reversed = q_bits_be[::-1]
        
        result_reversed = _try_factorization(p_bits_reversed, q_bits_reversed, 'little-endian (reversed)')
        
        if result_reversed.success:
            result_reversed.error_info['suggestion'] = 'Solution found with reversed bit order'
            return result_reversed
        
        # 两种尝试都失败了，合并错误信息
        combined_error = {
            'attempts': [
                {'endianness': 'big-endian', 'result': result.error_info},
                {'endianness': 'little-endian (reversed)', 'result': result_reversed.error_info}
            ],
            'suggestion': 'No solution found with either bit order. Please check your input data.',
            'max_depth_reached_overall': max(
                result.error_info['progress']['max_depth_reached'],
                result_reversed.error_info['progress']['max_depth_reached']
            )
        }
        
        return FactorResult(success=False, error_info=combined_error)
    
    return result

def from_vector(n: int, p_bits: List[int], q_bits: List[int]) -> Optional[Tuple[int, int]]:
    """通过比特向量分解 n（向后兼容接口）"""
    result = from_vector_enhanced(n, p_bits, q_bits)
    return result.factors if result.success else None

def from_str(n: int, p_bits_str: str, q_bits_str: str) -> Optional[Tuple[int, int]]:
    """通过比特字符串分解 n（向后兼容接口）"""
    result = from_str_enhanced(n, p_bits_str, q_bits_str)
    return result.factors if result.success else None

def from_vector_enhanced(n: int, p_bits: List[int], q_bits: List[int], 
                        try_reverse: bool = True, verbose: bool = False) -> FactorResult:
    """通过比特向量分解 n，返回增强的结果信息"""
    result = _prepare_and_run(n, p_bits, q_bits, try_reverse)
    
    if verbose and not result.success:
        _print_error_feedback(result.error_info)
    
    return result

def from_str_enhanced(n: int, p_bits_str: str, q_bits_str: str, 
                     try_reverse: bool = True, verbose: bool = False) -> FactorResult:
    """通过比特字符串分解 n，返回增强的结果信息"""
    def parse_str(s: str) -> List[int]:
        return [0 if c == '0' else 1 if c == '1' else -1 for c in s.replace('_', '?')]
    
    result = _prepare_and_run(n, parse_str(p_bits_str), parse_str(q_bits_str), try_reverse)
    
    if verbose and not result.success:
        _print_error_feedback(result.error_info)
    
    return result

def _print_error_feedback(error_info: Dict[str, Any]) -> None:
    """打印详细的错误反馈信息"""
    print("=== Factor-from-random-known-bits Error Feedback ===")
    
    if 'attempts' in error_info:
        # 多次尝试的情况
        print(f"Tried {len(error_info['attempts'])} different bit orderings:")
        for i, attempt in enumerate(error_info['attempts'], 1):
            progress = attempt['result']['progress']
            print(f"  Attempt {i} ({attempt['endianness']}):")
            print(f"    - Maximum search depth reached: {progress['max_depth_reached']}")
            print(f"    - Total nodes explored: {progress['total_nodes_explored']}")
            print(f"    - Search completed: {attempt['result']['search_completed']}")
        
        print(f"\nOverall maximum depth reached: {error_info['max_depth_reached_overall']}")
        print(f"Suggestion: {error_info['suggestion']}")
    else:
        # 单次尝试的情况
        progress = error_info['progress']
        print(f"Endianness tried: {error_info['endianness_tried']}")
        print(f"Maximum search depth reached: {progress['max_depth_reached']} / {error_info['bit_length']}")
        print(f"Total nodes explored: {progress['total_nodes_explored']}")
        print(f"Search completed: {error_info['search_completed']}")
        
        if not error_info['search_completed']:
            print("\nSuggestion: The search terminated early due to pruning.")
            print("This might indicate incorrect bit patterns or wrong endianness.")
            print("Try reversing the bit order of your input patterns.")
        else:
            print("\nSuggestion: Search was completed but no solution found.")
            print("Please verify your input data is correct.")
