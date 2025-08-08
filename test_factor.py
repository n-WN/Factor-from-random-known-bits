# 文件: test_factor.py
import pytest
import gmpy2
import factor_known_bits  # 导入我们的模块

def test_from_str_small():
    """测试小数值和字符串输入"""
    n = 91
    p_str = "110_"
    q_str = "0__1"
    expected = (13, 7)
    
    result = factor_known_bits.from_str(n, p_str, q_str)
    assert result is not None
    # 结果的顺序可能是 (p,q) 或 (q,p)，都需要考虑
    assert set(result) == set(expected)

def test_from_vector_small():
    """测试小数值和向量输入"""
    n = 91
    p_vec = [1, 1, 0, -1]
    q_vec = [0, -1, -1, 1]
    expected = (13, 7)
    
    result = factor_known_bits.from_vector(n, p_vec, q_vec)
    assert result is not None
    assert set(result) == set(expected)

def test_no_solution_found():
    """测试一个已知无解的场景"""
    n = 91
    p_str = "000_" # 不可能的p (neither 7 nor 13 start with 000)
    q_str = "000_" # 不可能的q (neither 7 nor 13 start with 000)
    
    result = factor_known_bits.from_str(n, p_str, q_str)
    assert result is None

def test_endianness_big_endian():
    """测试大端序（正常情况）"""
    n = 91  # 91 = 7 * 13, where 7 = 0111, 13 = 1101
    p_str = "110_"  # 1101 -> 13 in big-endian  
    q_str = "011_"  # 0111 -> 7 in big-endian
    
    result = factor_known_bits.from_str(n, p_str, q_str)
    assert result is not None
    assert set(result) == {7, 13}

def test_endianness_little_endian():
    """测试小端序（需要自动反转）"""
    n = 91  # 91 = 7 * 13
    # 如果用户提供的是小端序的bit模式：
    # 7 = 0111, 反转后是 1110
    # 13 = 1101, 反转后是 1011
    p_str = "_011"  # 1011 reversed -> 1101 = 13
    q_str = "111_"  # 1110 reversed -> 0111 = 7
    
    result = factor_known_bits.from_str(n, p_str, q_str)
    assert result is not None
    assert set(result) == {7, 13}

def test_enhanced_api_with_success():
    """测试增强API - 成功案例"""
    n = 91
    p_str = "110_"
    q_str = "011_"
    
    result = factor_known_bits.from_str_enhanced(n, p_str, q_str)
    assert result.success
    assert result.factors is not None
    assert set(result.factors) == {7, 13}
    assert 'progress' in result.error_info

def test_enhanced_api_with_failure():
    """测试增强API - 失败案例"""
    n = 91
    p_str = "000_"
    q_str = "000_"
    
    result = factor_known_bits.from_str_enhanced(n, p_str, q_str)
    assert not result.success
    assert result.factors is None
    assert 'attempts' in result.error_info
    assert len(result.error_info['attempts']) == 2  # 两种endianness都尝试了

def test_enhanced_api_with_endianness_detection():
    """测试增强API - 端序自动检测"""
    n = 91
    # 提供错误的端序，但应该能自动检测并修正
    p_str = "_011"  # little-endian pattern for 13
    q_str = "111_"  # little-endian pattern for 7
    
    result = factor_known_bits.from_str_enhanced(n, p_str, q_str)
    assert result.success
    assert result.factors is not None
    assert set(result.factors) == {7, 13}
    assert 'suggestion' in result.error_info
    assert 'reversed bit order' in result.error_info['suggestion']

def test_vector_endianness():
    """测试向量形式的端序处理"""
    n = 91
    # 7 = 0111, 13 = 1101
    # 小端序: 7 reversed = [1,1,1,0], 13 reversed = [1,0,1,1]
    p_vec = [-1, 0, 1, 1]  # little-endian pattern for 13 (1101 -> [1,0,1,1])
    q_vec = [1, 1, 1, -1]  # little-endian pattern for 7 (0111 -> [1,1,1,0])
    
    result = factor_known_bits.from_vector_enhanced(n, p_vec, q_vec)
    assert result.success
    assert result.factors is not None
    assert set(result.factors) == {7, 13}

# 使用 pytest.mark.slow 来标记可能耗时较长的测试
@pytest.mark.slow
def test_large_example_from_prompt():
    """测试题目中的完整大数样例"""
    n = 104158954646372695568095796310479805403678314919693272509836778997179683485437763692891984254171869987446475357518587344178264028334102088429629785065036660148146855007349113784322098795994839040721664806905084554147298456659074384855277678993200563966327086005547016327991986225930798076081014377904788085807
    p_str = "1010101111000___11000___11100___11010___0___0___0___100110000___0___0___0___11000___0___0___110110010___11001100100111010___100011000___0___0___0___11111000111111100___1101110010000___0___0___0___10110___0___0___0___0___0___1100101111000___0___1001111011110___0___10000___0___0___11010___1010101110110___0___0___0___0___10010___1011101011100___110111010___0___0___0___101010110___0___10000___1000101011000___0___0___0___101010000___11010___111010000___0___11110___0___10010___111010010___0___0___10100___0___0___"
    q_str = "110111010___111011110___0___1000100110001110100111100___0___10110___11000___0___10110___11100___10000___0___0___11111100110010100___10000___11100___0___110010110___101110010___10010___11110___11110___0___1101111011000___101010110___10100___0___10100___1010101011010___0___0___100110110___0___10000___0___0___1000101110010___1111110010110___0___0___0___101110100___0___1100101111000___10100___0___0___0___0___0___0___10010___0___0___10100___10010___0___0___0___101011110___0___111110000___0___11110___0___10100___"
    
    result = factor_known_bits.from_str(n, p_str, q_str)
    assert result is not None
    p, q = result
    # 使用 gmpy2 进行大数乘法验证
    assert gmpy2.mpz(p) * gmpy2.mpz(q) == gmpy2.mpz(n)
