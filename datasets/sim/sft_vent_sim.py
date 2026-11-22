#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SinoSFT 悬浮隧道通风导光消防系统 —— 公开层简化仿真验证引擎

工程定位：为数据集的五个独立布尔判定标记提供可复现的计算依据，
把「仅凭概念描述判定」升级为「按工况档位计算判定」。

保密边界（Principle Zero）：
  - 全部输入为枚举档位（0/1/2/3 或语义枚举），不含任何真实尺寸、材料配比、
    控制律、标定值；
  - 输出为布尔判定 + 触发规则锚点，不反推任何内控参数；
  - 模型为工程近似（grade-based feasibility model），非设计计算书，
    不得作为结构强度/消防验收依据。

五个模型（对应附件第七章五个布尔标记）：
  M1 ventilation_sustained       风量持续性      R-SFT-06/07/08
  M2 zone_contained              分区隔离        R-SFT-09/10/11
  M3 fire_suppression_ready      消防就绪        R-SFT-12/13/14/15
  M4 buoyancy_redundant          浮力冗余        R-SFT-01/03
  M5 system_valid_under_congestion 拥堵工况综合  第七章

所有函数纯函数、无外部依赖，便于第三方逐条独立复核。
"""

from itertools import product

# ───────────────────────── 工况枚举域 ─────────────────────────
SCENARIOS = ["正常通行", "拥堵停车", "局部火灾", "进水极端"]        # 第七章四类工况
TRAFFIC = ["正常", "拥堵", "停车"]                                  # 4.4 traffic_state
VENT_MODE = ["活塞为主", "机械兜底", "排烟控制"]                    # 4.2/4.3 impeller_mode
ZONE_STATE = ["待机", "主动分隔", "硬隔离闭合"]                     # 第五章风帘/水帘/封闭门
TANK_STATE = ["储备充足", "临界", "超储备告警"]                     # 6.3 消防储备/压载
BUOY_STATE = ["完好", "局部受损", "进水受损"]                       # 2.3 残余浮力比档
SMOKE = ["无烟", "有烟"]                                            # 5.2 smoke_spread_flag

# 维度顺序固定，供生成器枚举
DIMS = [
    ("scenario", SCENARIOS),
    ("traffic_state", TRAFFIC),
    ("vent_mode", VENT_MODE),
    ("zone_state", ZONE_STATE),
    ("tank_state", TANK_STATE),
    ("buoy_state", BUOY_STATE),
    ("smoke", SMOKE),
]

# ───────────────────────── 档位映射（语义→级数）─────────────────────────
# 说明：映射只为「相对可行性」服务，数值是序数量纲，不代表任何物理量。
_TRAFFIC_PISTON = {"正常": 3, "拥堵": 1, "停车": 0}     # 活塞效应随车流恶化骤降（4.1 局限）
_TRAFFIC_DEMAND = {"正常": 1, "拥堵": 2, "停车": 2}     # 需风档：拥堵/停车仍需维持换气
_SCENARIO_DEMAND_BOOST = {"正常通行": 0, "拥堵停车": 0, "局部火灾": 1, "进水极端": 0}
_VENT_SUPPLY = {"活塞为主": 0, "机械兜底": 2, "排烟控制": 2}  # 机械/排烟提供额外供风档
_ZONE_BARRIER = {"待机": 0, "主动分隔": 1, "硬隔离闭合": 2}  # 2=硬隔离（R-SFT-09 不可替代）
_TANK_RESERVE = {"储备充足": 3, "临界": 1, "超储备告警": 0}
_BUOY_RESIDUAL = {"完好": 3, "局部受损": 2, "进水受损": 1}


def m1_ventilation_sustained(inp):
    """M1 风量持续性：活塞 + 机械兜底/独立风道 ≥ 工况需风，且火灾烟控不冲突。

    R-SFT-06 拥堵/停车且活塞低 → 必须机械兜底
    R-SFT-07 火灾机械通风不得与烟控冲突
    R-SFT-08 风量/风压/换气绑定同一工况，不混用
    """
    s, tr, vm = inp["scenario"], inp["traffic_state"], inp["vent_mode"]
    piston = _TRAFFIC_PISTON[tr]
    # 拥堵/停车时活塞骤降，此时若仍选"活塞为主"则供风不足（R-SFT-06）
    supply = piston + _VENT_SUPPLY[vm]
    demand = _TRAFFIC_DEMAND[tr] + _SCENARIO_DEMAND_BOOST[s]
    ok = supply >= demand
    anchors = ["R-SFT-08"]
    if tr in ("拥堵", "停车") and piston < 2:
        anchors.append("R-SFT-06")
        if vm == "活塞为主":
            ok = False                      # 未启机械兜底 → 判定失效
    if s == "局部火灾":
        anchors.append("R-SFT-07")
        if vm == "活塞为主":
            ok = False                      # 火灾仍活塞送风 → 与烟控冲突
        elif vm == "排烟控制":
            ok = ok                          # 排烟控制与烟控一致
    return bool(ok), anchors


def m2_zone_contained(inp):
    """M2 分区隔离：主动分隔（风帘/水帘）不能替代硬隔离封闭门。

    R-SFT-09 风帘/水帘不替代耐火分隔，硬隔离须按时闭合
    R-SFT-10 水帘致路面/电气风险 → 排水/隔离/切换预案
    R-SFT-11 跨模块且封闭门未闭合 → 分区隔离不可为真
    """
    zs, smoke, s = inp["zone_state"], inp["smoke"], inp["scenario"]
    barrier = _ZONE_BARRIER[zs]
    hard = barrier >= 2
    anchors = ["R-SFT-09"]
    # 工程判定：分区隔离要求为「条件触发」——仅火灾或有烟跨区时需要有效隔离。
    # 正常通行/拥堵停车/进水极端且无烟时，分区处于待机是合理配置，不应判失效。
    needs_containment = (s == "局部火灾") or (smoke == "有烟")
    if not needs_containment:
        return True, anchors                  # 无跨区风险 → 隔离标记成立
    anchors.append("R-SFT-11")
    if not hard:
        if s == "局部火灾":
            anchors.append("R-SFT-10")
        return False, anchors                 # 风帘/水帘主动分隔不替代硬隔离（R-SFT-09）
    return True, anchors                      # 硬隔离闭合 → 成立


def m3_fire_suppression_ready(inp):
    """M3 消防就绪：淡化达标 + 储备足够 + 取水联动压载补偿 + 纵倾横倾达标。

    R-SFT-12 超储备取水未触发压载补偿 → 不得判安全
    R-SFT-13 淡化/过滤不合格 → 细水雾不就绪
    R-SFT-14 取水致纵倾/横倾超限 → 告警并补偿或降级
    R-SFT-15 污染超标水不得纳供，排放去向须记录
    """
    ts, s = inp["tank_state"], inp["scenario"]
    reserve = _TANK_RESERVE[ts]
    ok = reserve >= 1
    anchors = ["R-SFT-12", "R-SFT-13", "R-SFT-15"]
    if ts == "超储备告警":
        ok = False                           # 超储备取水未补偿 → 不就绪
    if s == "进水极端":
        anchors.append("R-SFT-14")
        if reserve < 2:
            ok = False                       # 进水叠加储备不足 → 稳性风险，降级
    return bool(ok), anchors


def m4_buoyancy_redundant(inp):
    """M4 浮力冗余：固体浮力独立于压载水，进水后残余比达标。

    R-SFT-01 浮力材料指标缺失/低于阈值 → 模块安全不可为真
    R-SFT-03 浮力冗余与压载水分开记录，不得用压载舱容积替代
    """
    bs, s = inp["buoy_state"], inp["scenario"]
    residual = _BUOY_RESIDUAL[bs]
    ok = residual >= 2
    anchors = ["R-SFT-01", "R-SFT-03"]
    if s == "进水极端":
        if residual < 2:
            ok = False                       # 进水且残余比不足 → 冗余失效
    return bool(ok), anchors


def m5_system_valid(inp, m1, m2, m3, m4):
    """M5 综合判定：四布尔按工况合成；拥堵场景额外要求机械兜底真启动。

    第七章：即使车流拥堵，系统仍可维持通风消防能力（须实测/仿真确认）。
    """
    s, vm, tr = inp["scenario"], inp["vent_mode"], inp["traffic_state"]
    ok = m1 and m2 and m3 and m4
    anchors = ["第七章"]
    if s == "拥堵停车":
        if tr in ("拥堵", "停车") and vm == "活塞为主":
            ok = False                       # 拥堵仅靠活塞 → 综合失效
    return bool(ok), anchors


def evaluate(inp):
    """单案例五模型全_evaluate，返回五个布尔 + 合并规则锚点 + 结论。"""
    v, a1 = m1_ventilation_sustained(inp)
    z, a2 = m2_zone_contained(inp)
    f, a3 = m3_fire_suppression_ready(inp)
    b, a4 = m4_buoyancy_redundant(inp)
    sv, a5 = m5_system_valid(inp, v, z, f, b)
    anchors = sorted(set(a1 + a2 + a3 + a4 + a5))
    conclusion = "通过" if sv else "受限"
    return {
        "ventilation_sustained": v,
        "zone_contained": z,
        "fire_suppression_ready": f,
        "buoyancy_redundant": b,
        "system_valid_under_congestion": sv,
        "conclusion": conclusion,
        "rule_anchors": ";".join(anchors),
    }


def all_cases():
    """枚举全部工况组合（多个语义档位的组合 = 1944），逐条仿真。"""
    for values in product(*[dom for _, dom in DIMS]):
        inp = dict(zip([k for k, _ in DIMS], values))
        yield inp, evaluate(inp)


if __name__ == "__main__":
    total = 0
    passed = 0
    for inp, out in all_cases():
        total += 1
        passed += out["system_valid_under_congestion"]
    print(f"SinoSFT 仿真引擎自检：枚举 {total} 例，综合通过 {passed} 例，"
          f"受限 {total - passed} 例")
    # 冒烟断言：拥堵+活塞为主必须失效；局部火灾+活塞为主必须失效
    a, _ = m1_ventilation_sustained({"scenario": "拥堵停车", "traffic_state": "拥堵", "vent_mode": "活塞为主"})
    assert a is False, "R-SFT-06 负注入未被识别"
    b, _ = m2_zone_contained({"zone_state": "主动分隔", "smoke": "有烟", "scenario": "局部火灾"})
    assert b is False, "R-SFT-09 负注入未被识别"
    print("冒烟断言通过：R-SFT-06 / R-SFT-09 负注入均被捕获")
