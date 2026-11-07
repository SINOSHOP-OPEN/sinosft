# -*- coding: utf-8 -*-
"""
宏观物理逻辑 · 自洽性断言（B 类验证）

★ 技术受控，仅作理论仿真交流。
本脚本只验证教科书级通用关系彼此自洽，不代表任何工程系统的验证结论。
退出码：0 = 全部断言通过；非 0 = 失败项数。
--selftest：故意注入错误样本，验证断言具备鉴别力。

设计哲学：人可以写文案，但不能写 PASS。
"""
import math
import sys

from force_balance import (
    buoyancy_equals_weight,
    displacement_transmissibility,
    equilibrium_submerged_ratio,
    feedforward_residual,
    is_isolation_band,
    solve_by_bisection,
)
from pascal_membrane import (
    distribute_force,
    equal_pressure_check,
    force_conservation_error,
    pressure,
)


def collect():
    """返回 (通过项, 失败项)。所有判据均为无量纲通用关系。"""
    ok, fail = [], []

    def chk(cond, msg):
        (ok if cond else fail).append(msg)

    # ── 受力平衡 ──────────────────────────────────────────
    for rho in (0.25, 0.5, 0.8):
        analytic = equilibrium_submerged_ratio(rho)
        numeric = solve_by_bisection(rho)
        chk(abs(analytic - numeric) < 1e-8,
            f"平衡浸没占比：解析解与二分法一致（相对密度 {rho}）")
        chk(abs(buoyancy_equals_weight(rho, analytic)) < 1e-9,
            f"平衡态合外力为零（相对密度 {rho}）")

    chk(abs(feedforward_residual(0.6, 0.6)) < 1e-12,
        "前馈补偿完全贴合时合力残差为零")
    chk(abs(feedforward_residual(0.6, 0.3)) > abs(feedforward_residual(0.6, 0.58)),
        "补偿越贴合，残差越小")

    # ── 频率隔离 ──────────────────────────────────────────
    t_near = displacement_transmissibility(0.95, 0.2)
    t_far = displacement_transmissibility(3.20, 0.2)
    chk(t_far < t_near, "远离共振区后位移传递率下降")
    chk(is_isolation_band(3.20) and not is_isolation_band(0.95),
        "隔震区判据落在 r > sqrt(2)")
    chk(t_far < 1.0 and t_near > 1.0,
        "隔震区传递率小于一、共振区大于一")

    # ── 帕斯卡传压 ────────────────────────────────────────
    areas = [1.0, 1.5, 2.0, 0.5]
    ps = equal_pressure_check(2.0, areas)
    chk(max(ps) - min(ps) < 1e-12, "同一密闭流体内各腔压强等值")
    chk(abs(ps[0] - pressure(2.0, 1.0)) < 1e-12, "压强等于力与面积之比")
    chk(force_conservation_error(2.0, areas) < 1e-12, "按面积分配后合力守恒")
    parts = distribute_force(2.0, areas)
    chk(all(p > 0 for p in parts), "各腔分配力均为正")
    chk(abs(parts[2] / parts[3] - areas[2] / areas[3]) < 1e-12,
        "分配力之比等于面积之比")

    return ok, fail


def selftest():
    """鉴别力：把 collect() 实际调用的函数逐条破坏，断言必须抓到。

    注意：collect() 用的是本模块通过 from-import 绑定的全局名字，
    因此必须 patch 本模块 globals()，patch 原模块不会生效（会让鉴别力变成假的）。
    """
    G = globals()
    cases = []

    def case(name, key, bad_impl):
        def run():
            orig = G[key]
            G[key] = bad_impl
            try:
                _, f = collect()
                return len(f) > 0
            finally:
                G[key] = orig
        cases.append((name, run))

    case("让二分法返回错误解", "solve_by_bisection", lambda r: r + 0.2)
    case("让各腔压强不等", "equal_pressure_check", lambda f, a: [f / x for x in a])
    case("让传递率恒为一", "displacement_transmissibility", lambda r, z: 1.0)
    case("让补偿失效", "feedforward_residual", lambda l, c: l + c)

    caught = 0
    for name, run in cases:
        hit = run()
        caught += int(hit)
        print(f"  注入[{name}] -> {'抓到' if hit else '漏检'}")
    print(f"鉴别力：{caught}/{len(cases)} 抓到")
    return 0 if caught == len(cases) else 1


def main():
    if "--selftest" in sys.argv:
        return selftest()
    ok, fail = collect()
    for line in ok:
        print("  PASS  " + line)
    for line in fail:
        print("  FAIL  " + line)
    print(f"\n宏观逻辑自洽断言：{len(ok)} 通过 / {len(fail)} 失败")
    print("声明：本结果只说明通用物理关系自洽，不构成任何工程验证结论。")
    return len(fail)


if __name__ == "__main__":
    sys.exit(main())
