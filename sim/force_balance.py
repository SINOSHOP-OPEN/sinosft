# -*- coding: utf-8 -*-
"""
宏观物理逻辑 · 受力平衡（极简框架）

★ 技术受控，仅作理论仿真交流。
本文件只含教科书级的通用物理关系，全部使用无量纲比值。
不含任何工程参数，也不含任何工程实现细节。

三条通用关系：
  1. 静力平衡    ΣF = 0   →  浮力 = 自重
  2. 前馈补偿    residual = load - compensation   →  合力波动趋小
  3. 频率隔离    T(r, ζ) = sqrt((1+(2ζr)²) / ((1-r²)²+(2ζr)²))

所有输入均为 0~1 之间的相对量或纯数，不代表任何真实工程尺寸。
"""
import math


def buoyancy_equals_weight(relative_density: float, submerged_ratio: float) -> float:
    """相对形式的静力平衡残差。

    relative_density : 浮体平均相对密度（相对流体，0~1）
    submerged_ratio  : 浸没体积占比（0~1）
    平衡时 submerged_ratio = relative_density，残差为 0。
    """
    return submerged_ratio - relative_density


def equilibrium_submerged_ratio(relative_density: float) -> float:
    """由平衡条件直接解出浸没占比。这里刻意保留解析解，说明逻辑可复算。"""
    if not 0.0 < relative_density <= 1.0:
        raise ValueError("relative_density 必须落在 (0, 1]，且仅为无量纲算例")
    return relative_density


def solve_by_bisection(relative_density: float, tol: float = 1e-10) -> float:
    """用二分法再解一次同一平衡，作为解析解的独立数值复核。"""
    lo, hi = 0.0, 1.0
    for _ in range(200):
        mid = (lo + hi) / 2.0
        if buoyancy_equals_weight(relative_density, mid) > 0:
            hi = mid
        else:
            lo = mid
        if hi - lo < tol:
            break
    return (lo + hi) / 2.0


def feedforward_residual(load: float, compensation: float) -> float:
    """前馈补偿后的合力残差（相对量）。补偿越贴合载荷，残差越小。"""
    return load - compensation


def displacement_transmissibility(r: float, zeta: float) -> float:
    """单自由度基底激励的位移传递率（通用教科书公式）。

    r    : 激励频率 / 固有频率
    zeta : 阻尼比
    r > sqrt(2) 时进入隔震区。
    """
    num = 1.0 + (2.0 * zeta * r) ** 2
    den = (1.0 - r * r) ** 2 + (2.0 * zeta * r) ** 2
    return math.sqrt(num / den)


def is_isolation_band(r: float) -> bool:
    """是否落在隔震区。"""
    return r > math.sqrt(2.0)


if __name__ == "__main__":
    # 纯无量纲演示，无任何工程含义
    for rho in (0.3, 0.5, 0.8):
        analytic = equilibrium_submerged_ratio(rho)
        numeric = solve_by_bisection(rho)
        print(f"相对密度 {rho:.2f} → 平衡浸没占比 解析 {analytic:.6f} / 数值 {numeric:.6f}")
    print(f"前馈补偿残差示例：{feedforward_residual(0.6, 0.58):+.4f}")
    for r in (0.95, 3.20):
        print(f"频率比 {r:.2f} → 传递率 {displacement_transmissibility(r, 0.2):.4f} "
              f"｜ 隔震区：{is_isolation_band(r)}")
