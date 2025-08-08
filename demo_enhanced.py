#!/usr/bin/env python3
"""
Demo script showing the enhanced error feedback and endianness handling features
"""

import factor_known_bits

def demo_basic_usage():
    """演示基本用法"""
    print("=== Demo 1: Basic Usage (Backward Compatible) ===")
    n = 91  # 91 = 7 * 13
    result = factor_known_bits.from_str(n, "110_", "011_")
    print(f"n = {n}")
    print(f"p_bits = '110_', q_bits = '011_'")
    print(f"Result: {result}")
    print()

def demo_enhanced_success():
    """演示增强功能 - 成功案例"""
    print("=== Demo 2: Enhanced API - Successful Factorization ===")
    n = 91
    result = factor_known_bits.from_str_enhanced(n, "110_", "011_", verbose=False)
    
    print(f"n = {n}")
    print(f"p_bits = '110_', q_bits = '011_'")
    print(f"Success: {result.success}")
    print(f"Factors: {result.factors}")
    print(f"Max depth reached: {result.error_info['progress']['max_depth_reached']}")
    print(f"Nodes explored: {result.error_info['progress']['total_nodes_explored']}")
    print()

def demo_endianness_auto_correction():
    """演示端序自动修正"""
    print("=== Demo 3: Automatic Endianness Correction ===")
    n = 91
    # 这些bit模式是小端序的，但程序会自动尝试修正
    result = factor_known_bits.from_str_enhanced(n, "_011", "111_", verbose=False)
    
    print(f"n = {n}")
    print(f"p_bits = '_011', q_bits = '111_' (wrong endianness)")
    print(f"Success: {result.success}")
    print(f"Factors: {result.factors}")
    if 'suggestion' in result.error_info:
        print(f"Suggestion: {result.error_info['suggestion']}")
    print()

def demo_detailed_error_feedback():
    """演示详细的错误反馈"""
    print("=== Demo 4: Detailed Error Feedback ===")
    n = 91
    # 使用不可能的bit模式
    result = factor_known_bits.from_str_enhanced(n, "000_", "000_", verbose=True)
    
    print(f"n = {n}")
    print(f"p_bits = '000_', q_bits = '000_' (impossible patterns)")
    print(f"Success: {result.success}")
    print()

def demo_disable_auto_retry():
    """演示禁用自动重试"""
    print("=== Demo 5: Disable Auto Retry ===")
    n = 91
    # 禁用自动重试，只尝试原始端序
    result = factor_known_bits.from_str_enhanced(n, "_011", "111_", try_reverse=False, verbose=True)
    
    print(f"n = {n}")
    print(f"p_bits = '_011', q_bits = '111_' (try_reverse=False)")
    print(f"Success: {result.success}")
    print()

if __name__ == "__main__":
    demo_basic_usage()
    demo_enhanced_success()
    demo_endianness_auto_correction()
    demo_detailed_error_feedback()
    demo_disable_auto_retry()