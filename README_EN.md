# Factor from (Random) Known Bits

> Python with GMP, inspired by @y011d4

[English README](README_EN.md) | [中文说明文档](README.md)

This is a Python tool based on `gmpy2` for efficiently factoring large composite numbers $n = p \cdot q$, especially when we have partial bit information (randomly distributed) about `p` and `q`. This tool is particularly useful in CTF cryptography challenges involving partial key leakage in RSA problems.

## Features

- **Partial Information Factorization**: Core functionality to recover complete factors from known bits of `p` and `q`.
- **Multiple Input Formats**: Support for specifying bit information via strings (e.g., `"101_01?"`) or integer lists/vectors (e.g., `[1, 0, 1, -1, 0, 1]`).
- **High-Performance Arithmetic**: Utilizes `gmpy2` library for arbitrary precision integer operations, ensuring performance when handling large numbers.
- **Efficient Pruning Algorithm**: Uses depth-first search (DFS) with bitwise modular arithmetic checks for effective pruning, significantly reducing search space.
- **Enhanced Error Feedback**: Provides detailed search progress, pruning information, and troubleshooting suggestions.
- **Automatic Endianness Handling**: Automatically detects and tries both big-endian and little-endian bit patterns to improve success rate.
- **Backward Compatibility**: Maintains original API while providing enhanced functionality through new APIs.

## Installation and Requirements

This project requires Python 3 and the `gmpy2` library.

1. Install `gmpy2`:

   ```bash
   pip install gmpy2
   ```

2. Get the code: Download or copy `factor_known_bits.py` to your working directory.

3. **Testing (Optional)**: If you want to run the test cases, install `pytest`:

   ```bash
   pip install pytest
   ```

## Usage

Place `factor_known_bits.py` in your project directory and import it like any regular Python module.

### Basic Usage (Backward Compatible)

#### Example 1: String Input

```python
# main.py
import factor_known_bits

# n = 91, p = 13 (1101), q = 7 (0111)
n = 91
p_bits_str = "110_"  # _ or ? represents unknown bits
q_bits_str = "0__1"

result = factor_known_bits.from_str(n, p_bits_str, q_bits_str)

if result:
    p, q = result
    print(f"Factorization successful: p = {p}, q = {q}")
else:
    print("Factorization failed.")

# Output:
# Factorization successful: p = 13, q = 7
```

#### Example 2: Vector Input

```python
# main.py
import factor_known_bits

n = 91
# -1 represents unknown bits
p_bits_vec = [1, 1, 0, -1]
q_bits_vec = [0, -1, -1, 1]

result = factor_known_bits.from_vector(n, p_bits_vec, q_bits_vec)

if result:
    p, q = result
    print(f"Factorization successful: p = {p}, q = {q}")
else:
    print("Factorization failed.")

# Output:
# Factorization successful: p = 13, q = 7
```

### Enhanced API (Recommended)

The new enhanced API provides detailed error information, automatic endianness detection, and search progress tracking.

#### Example 3: Enhanced String API

```python
import factor_known_bits

n = 91
p_bits_str = "110_"
q_bits_str = "011_"

# Use enhanced API
result = factor_known_bits.from_str_enhanced(n, p_bits_str, q_bits_str)

if result.success:
    p, q = result.factors
    print(f"Factorization successful: p = {p}, q = {q}")
    print(f"Search depth: {result.error_info['progress']['max_depth_reached']}")
    print(f"Nodes explored: {result.error_info['progress']['total_nodes_explored']}")
else:
    print("Factorization failed")
    print(f"Error info: {result.error_info}")

# Output:
# Factorization successful: p = 13, q = 7
# Search depth: 4
# Nodes explored: 5
```

#### Example 4: Automatic Endianness Detection

```python
import factor_known_bits

n = 91
# Wrong endianness (little-endian), but the program will auto-detect and correct
p_bits_str = "_011"  # Should be little-endian representation of 13
q_bits_str = "111_"  # Should be little-endian representation of 7

result = factor_known_bits.from_str_enhanced(n, p_bits_str, q_bits_str)

if result.success:
    p, q = result.factors
    print(f"Factorization successful: p = {p}, q = {q}")
    print(f"Suggestion: {result.error_info.get('suggestion', 'None')}")
else:
    print("Factorization failed")

# Output:
# Factorization successful: p = 13, q = 7
# Suggestion: Solution found with reversed bit order
```

#### Example 5: Detailed Error Feedback

```python
import factor_known_bits

n = 91
# Use impossible bit patterns
p_bits_str = "000_"
q_bits_str = "000_"

# Enable verbose mode
result = factor_known_bits.from_str_enhanced(n, p_bits_str, q_bits_str, verbose=True)

# This will output detailed error analysis information
```

### API Parameter Description

#### Enhanced API Parameters

- `try_reverse` (bool, default True): Whether to automatically try reversed endianness
- `verbose` (bool, default False): Whether to print detailed error feedback information

#### FactorResult Class

The enhanced API returns a `FactorResult` object with the following attributes:

- `success` (bool): Whether factorization was successful
- `factors` (Tuple[int, int] or None): The factored results (p, q)
- `error_info` (Dict): Detailed error information and search statistics

## Algorithm Analysis and Design Considerations

### Core Algorithm: Depth-First Search (DFS) with Pruning

The core of this tool is a depth-first search (DFS) strategy that starts from the least significant bit (LSB, bit 0) and builds possible `p` and `q` values bit by bit upward.

The key to its efficiency is **pruning**. Using the mathematical relationship $p \cdot q = n$, we can infer that if the first `k` bits of `p` and `q` are correct, then their product modulo $2^k$ must equal $n$ modulo $2^k$:

$$(p \bmod 2^k) \cdot (q \bmod 2^k) \equiv n \pmod{2^k}$$

When searching to the `k`-th bit, this condition is immediately checked; any bit combination that doesn't satisfy this condition has its search branch immediately abandoned, avoiding blind search of huge invalid spaces.

### About RSA Scenarios and Least Significant Bit (LSB) Considerations

In typical RSA scenarios, the modulus `n` is the product of two large primes `p` and `q`. Except for the prime 2, all primes are odd, so their binary least significant bit (LSB) is always `1`.

Therefore, both the 0th bits of `p` and `q` must be `1`.

This prior knowledge could be incorporated into the algorithm: when searching the `k = 0` bit, directly fix `(p_bit, q_bit)` to `(1,1)` instead of testing the other 3 combinations.

However, this specific optimization **is not implemented in the current code** for the following considerations:

1. **Generality**: The current code also applies to more general cases where `p` or `q` might be even (though this wouldn't occur in standard RSA).
2. **Performance Impact**: This optimization only prunes 3 out of 4 branches at the first level of the search tree; for a search tree whose depth and width relate to problem scale, this single pruning at the root node brings minimal performance improvement.

To maintain code simplicity and broader applicability, we omit this very minor optimization.

## Running Tests

The project includes a test suite using `pytest`. Place `factor_known_bits.py` and `test_factor.py` in the same directory, then run:

```bash
pytest -v
```

The `-v` parameter shows more detailed output.

If you want to skip time-consuming large number tests, you can filter with:

```bash
pytest -v -m "not slow"
```

## Example Demonstration

The project includes an enhanced feature demonstration script `demo_enhanced.py` that showcases all new features:

```bash
python demo_enhanced.py
```

The demo script includes:
- Basic usage examples
- Enhanced API success cases
- Automatic endianness correction functionality
- Detailed error feedback
- Options to disable automatic retry