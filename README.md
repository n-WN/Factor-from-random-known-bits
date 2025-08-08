# Factor from (Random) Known Bits

> Python with GMP, inspired by @y011d4

[English README](README_EN.md) | [中文说明文档](README.md)

这是一个基于 Python 和 `gmpy2` 实现的工具，用于高效地分解一个大合数 $n = p \cdot q$，尤其适用于当我们已知 `p` 和 `q` 的部分比特信息（随机分布）的场景。此工具在 CTF 竞赛中的密码学挑战（特别是关于部分密钥泄露的 RSA 问题）中非常有用。

## 功能特性

- **部分信息分解**：核心功能，根据 `p` 和 `q` 的已知比特恢复完整的因子。
- **多种输入格式**：支持通过字符串（例如 `"101_01?"`）或整数列表/向量（例如 `[1, 0, 1, -1, 0, 1]`）来指定比特信息。
- **高性能算术**：利用 `gmpy2` 库进行任意精度整数运算，确保处理大数时的性能。
- **高效剪枝算法**：底层采用深度优先搜索（DFS）和逐位模运算检查，能有效剪枝，大幅缩减搜索空间。
- **增强的错误反馈**：提供详细的搜索进度、剪枝信息和故障排除建议。
- **自动端序处理**：自动检测并尝试大端序和小端序比特模式，提高成功率。
- **向后兼容性**：保持原有 API 不变，同时提供增强功能的新 API。

## 安装与环境要求

本项目需要 Python 3 和 `gmpy2` 库。

1. 安装 `gmpy2`：

   ```bash
   pip install gmpy2
   ```

2. 获取代码：将项目中的 `factor_known_bits.py` 文件下载或复制到您的工作目录中。

3. **测试（可选）**：如果您想运行测试用例，需要安装 `pytest`。

   ```bash
   pip install pytest
   ```

## 使用方法

将 `factor_known_bits.py` 放在您的项目目录下，然后像普通 Python 模块一样导入并使用。

### 基础用法（向后兼容）

#### 示例 1：通过字符串输入

```python
# main.py
import factor_known_bits

# n = 91, p = 13 (1101), q = 7 (0111)
n = 91
p_bits_str = "110_"  # _ 或 ? 代表未知位
q_bits_str = "0__1"

result = factor_known_bits.from_str(n, p_bits_str, q_bits_str)

if result:
    p, q = result
    print(f"分解成功: p = {p}, q = {q}")
else:
    print("分解失败。")

# 输出:
# 分解成功: p = 13, q = 7
```

#### 示例 2：通过向量输入

```python
# main.py
import factor_known_bits

n = 91
# -1 代表未知位
p_bits_vec = [1, 1, 0, -1]
q_bits_vec = [0, -1, -1, 1]

result = factor_known_bits.from_vector(n, p_bits_vec, q_bits_vec)

if result:
    p, q = result
    print(f"分解成功: p = {p}, q = {q}")
else:
    print("分解失败。")

# 输出:
# 分解成功: p = 13, q = 7
```

### 增强 API（推荐）

新的增强 API 提供更详细的错误信息、自动端序检测和搜索进度跟踪。

#### 示例 3：增强字符串 API

```python
import factor_known_bits

n = 91
p_bits_str = "110_"
q_bits_str = "011_"

# 使用增强 API
result = factor_known_bits.from_str_enhanced(n, p_bits_str, q_bits_str)

if result.success:
    p, q = result.factors
    print(f"分解成功: p = {p}, q = {q}")
    print(f"搜索深度: {result.error_info['progress']['max_depth_reached']}")
    print(f"探索节点: {result.error_info['progress']['total_nodes_explored']}")
else:
    print("分解失败")
    print(f"错误信息: {result.error_info}")

# 输出:
# 分解成功: p = 13, q = 7
# 搜索深度: 4
# 探索节点: 5
```

#### 示例 4：自动端序检测

```python
import factor_known_bits

n = 91
# 错误的端序（小端序），但程序会自动检测并修正
p_bits_str = "_011"  # 应该是 13 的小端序表示
q_bits_str = "111_"  # 应该是 7 的小端序表示

result = factor_known_bits.from_str_enhanced(n, p_bits_str, q_bits_str)

if result.success:
    p, q = result.factors
    print(f"分解成功: p = {p}, q = {q}")
    print(f"建议: {result.error_info.get('suggestion', '无')}")
else:
    print("分解失败")

# 输出:
# 分解成功: p = 13, q = 7
# 建议: Solution found with reversed bit order
```

#### 示例 5：详细错误反馈

```python
import factor_known_bits

n = 91
# 使用不可能的比特模式
p_bits_str = "000_"
q_bits_str = "000_"

# 启用详细模式
result = factor_known_bits.from_str_enhanced(n, p_bits_str, q_bits_str, verbose=True)

# 这将输出详细的错误分析信息
```

### API 参数说明

#### 增强 API 参数

- `try_reverse` (bool, 默认 True): 是否自动尝试反向端序
- `verbose` (bool, 默认 False): 是否打印详细的错误反馈信息

#### FactorResult 类

增强 API 返回 `FactorResult` 对象，包含以下属性：

- `success` (bool): 分解是否成功
- `factors` (Tuple[int, int] 或 None): 分解得到的因子 (p, q)
- `error_info` (Dict): 详细的错误信息和搜索统计

## 算法解析与设计思考

### 核心算法：带剪枝的深度优先搜索 (DFS)

本工具的核心是一种深度优先搜索（DFS）策略，它从最低有效位（LSB，第 0 位）开始，逐位向上构建可能的 `p` 和 `q`。

其效率的关键在于 **剪枝（Pruning）**。利用数学关系 $p \cdot q = n$，我们可以推断出：若 `p` 和 `q` 的前 `k` 位是正确的，则它们的乘积模 $2^k$ 必须等于 $n$ 模 $2^k$，即：

$$(p \bmod 2^k) \cdot (q \bmod 2^k) \equiv n \pmod{2^k}$$

在搜索到第 `k` 位时，会立即检查该条件；任何不满足该条件的比特组合所构成的搜索分支都会被立即放弃，从而避免对巨大无效空间的盲目搜索。

### 关于 RSA 场景与最低有效位 (LSB) 的思考

在典型的 RSA 场景中，模数 `n` 是两个大素数 `p` 和 `q` 的乘积。除了素数 2 之外，所有素数都是奇数，故其二进制最低有效位 (LSB) 始终为 `1`。

因此，`p` 与 `q` 的第 0 位都必须是 `1`。

这一先验知识可以并入算法：在搜索第 `k = 0` 位时，直接将 `(p_bit, q_bit)` 固定为 `(1,1)`，而无需测试其余 3 组组合。

然而，此特定优化 **并未在当前代码中实现**，其考虑如下：

1. **通用性**：当前代码也适用于 `p` 或 `q` 为偶数（尽管标准 RSA 不会出现）的更一般情况。
2. **性能影响**：该优化仅剪掉搜索树在第一层的 4 个分支中的 3 个；对于一棵深度与宽度和问题规模相关的搜索树而言，这种仅在根节点做一次剪枝带来的性能提升微乎其微。

为了保持代码的简洁性与更广泛适用性，我们省去这一非常小的优化。

## 运行测试

项目包含一个使用 `pytest` 的测试套件。将 `factor_known_bits.py` 与 `test_factor.py` 放在同一目录，然后执行：

```bash
pytest -v
```

其中 `-v` 参数可显示更详细的输出。

若您想跳过耗时较长的大数测试，可用如下命令过滤：

```bash
pytest -v -m "not slow"
```

## 示例演示

项目包含一个增强功能演示脚本 `demo_enhanced.py`，展示了所有新特性的使用方法：

```bash
python demo_enhanced.py
```

该演示脚本包含：
- 基础用法示例
- 增强 API 的成功案例
- 自动端序修正功能
- 详细错误反馈
- 禁用自动重试的选项
