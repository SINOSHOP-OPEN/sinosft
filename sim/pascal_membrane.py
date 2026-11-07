# -*- coding: utf-8 -*-
"""
宏观物理逻辑 · 帕斯卡膜传压（极简框架）

★ 技术受控，仅作理论仿真交流。
本文件只含教科书级的帕斯卡原理：密闭静止流体中，外加压强各向等值传递。
全部使用无量纲相对量；不含任何工程参数、膜材参数、结构尺寸或控制算法。

两条通用关系：
  1. 压强定义        p = F / A
  2. 等值传递        n 个腔体串联受压时，各腔压强相同；总力按面积比例分配
"""


def pressure(force: float, area: float) -> float:
    """相对形式的压强定义。area 必须为正的相对面积。"""
    if area <= 0.0:
        raise ValueError("area 必须为正的相对面积")
    return force / area


def equal_pressure_check(force: float, areas: list[float]) -> list[float]:
    """帕斯卡原理：同一密闭流体中，各腔压强应相等。

    返回各腔压强列表（相对量）。调用方可断言其离散度为零。
    """
    p = pressure(force, areas[0])
    return [p for _ in areas]


def distribute_force(force: float, areas: list[float]) -> list[float]:
    """按面积比例分配总力；合力守恒：sum(分配力) == force。"""
    total = sum(areas)
    if total <= 0.0:
        raise ValueError("面积之和必须为正")
    return [force * a / total for a in areas]


def force_conservation_error(force: float, areas: list[float]) -> float:
    """分配前后合力之差，用于自洽断言。"""
    return abs(sum(distribute_force(force, areas)) - force)


if __name__ == "__main__":
    # 纯无量纲演示，无任何工程含义
    areas = [1.0, 1.5, 2.0, 0.5]
    ps = equal_pressure_check(2.0, areas)
    parts = distribute_force(2.0, areas)
    print("各腔压强（相对量）:", [round(x, 6) for x in ps])
    print("按面积分配的力   :", [round(x, 6) for x in parts])
    print("合力守恒误差     :", round(force_conservation_error(2.0, areas), 12))
