#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SINOSFT 海面浮升疏散救生系统 —— 公开层仿真验证引擎

工程定位：
规范给出的静态容量（每公里理论承载）远大于疏散指标，真正的验收风险在
「动态时序 + 失效链路」。本引擎把五个核心布尔判定从条文升级为按档位可复算：
  evac_3min_km3000_valid           三分钟/km/3000人综合有效
  stair_no_block_flag              阶梯无拥堵核验
  cabin_passive_buoy_valid         无源浮力自救有效
  channel_seal_recovery_valid      破口自封复原有效
  full_scenario_self_rescue_valid  全工况自主逃生合格

保密边界（Principle Zero）：
输入全部为语义档位，不含任何裸米制尺寸、材料构成、控制律或标定数值；
输出仅为布尔 + 规则锚点，不反推受控实现层参数。
模型为档位化工程近似，用于判定逻辑可复现性验证，
不作为结构设计、消防验收或海上救生的直接依据。

八条硬规则锚点：R-SFT-EVAC-01 ~ R-SFT-EVAC-08
"""

from itertools import product

SCENARIOS = [
    "全管断电", "浓烟完全遮蔽", "车流完全拥堵", "局部模块火灾",
    "局部破损进水", "夜间零可视", "大风浪海面", "多模块连续事故",
]
STAIR = ["净宽达标", "净宽不足"]
CABIN = ["满配", "数量不足"]
BUOY = ["无源自主激发", "纯电控启动"]
SEAL = ["自动机械复位", "无自封能力"]
TIMING = ["四段全部达标", "前段超时", "末段超时"]
INTERCONNECT = ["互通完好", "互通缩减失效"]
GEOMETRY = ["固定折返几何", "几何变更未复算"]
CAPACITY = ["承载力达标", "承载力不足"]
BREATHING = ["独立呼吸管路", "集体供氧"]

DIMS = [
    ("scenario", SCENARIOS),
    ("stair_width", STAIR),
    ("cabin_count", CABIN),
    ("buoyancy_mode", BUOY),
    ("seal_mode", SEAL),
    ("timing_state", TIMING),
    ("interconnect", INTERCONNECT),
    ("geometry", GEOMETRY),
    ("capacity", CAPACITY),
    ("breathing", BREATHING),
]

BOOL_COLS = [
    "evac_3min_km3000_valid",
    "stair_no_block_flag",
    "cabin_passive_buoy_valid",
    "channel_seal_recovery_valid",
    "full_scenario_self_rescue_valid",
]


def m1_evac_3min(inp):
    """综合时序：分段时序、承载力、阶梯通行、折返几何四项同时成立。"""
    a = ["R-SFT-EVAC-05", "R-SFT-EVAC-08"]
    ok = inp["timing_state"] == "四段全部达标" and inp["capacity"] == "承载力达标"
    if inp["stair_width"] == "净宽不足":
        ok = False
        a.append("R-SFT-EVAC-01")
    if inp["geometry"] == "几何变更未复算":
        ok = False
        a.append("R-SFT-EVAC-07")
    return bool(ok), a


def m2_stair_no_block(inp):
    """阶梯无拥堵：净宽达标 + 固定折返几何；车流拥堵场景由独立人行通道隔离。"""
    a = ["R-SFT-EVAC-01", "R-SFT-EVAC-07"]
    ok = inp["stair_width"] == "净宽达标" and inp["geometry"] == "固定折返几何"
    if inp["scenario"] == "车流完全拥堵":
        a.append("车流与人流隔离")
    return bool(ok), a


def m3_passive_buoy(inp):
    """无源自救：满配舱位 + 无源浮力激发；断电/火灾/进水均不依赖外部能源。"""
    a = ["R-SFT-EVAC-02", "R-SFT-EVAC-03"]
    ok = inp["cabin_count"] == "满配" and inp["buoyancy_mode"] == "无源自主激发"
    if inp["scenario"] in ("全管断电", "局部模块火灾", "局部破损进水"):
        a.append("全工况无源校核")
    return bool(ok), a


def m4_seal_recovery(inp):
    """破口自封：上浮脱离后机械复位封闭，阻断倒灌与烟气外溢。"""
    a = ["R-SFT-EVAC-04"]
    ok = inp["seal_mode"] == "自动机械复位"
    if inp["scenario"] == "局部破损进水":
        a.append("进水工况自封校核")
    return bool(ok), a


def m5_full_scenario(inp, m1, m2, m3, m4):
    """全工况：前四项 + 跨管互通；浓烟工况必须独立呼吸管路。"""
    a = ["R-SFT-EVAC-06"]
    ok = m1 and m2 and m3 and m4 and inp["interconnect"] == "互通完好"
    if inp["scenario"] == "浓烟完全遮蔽":
        a.append("R-SFT-EVAC-03-呼吸独立")
        if inp["breathing"] != "独立呼吸管路":
            ok = False
    return bool(ok), a


def evaluate(inp):
    v1, a1 = m1_evac_3min(inp)
    v2, a2 = m2_stair_no_block(inp)
    v3, a3 = m3_passive_buoy(inp)
    v4, a4 = m4_seal_recovery(inp)
    v5, a5 = m5_full_scenario(inp, v1, v2, v3, v4)
    vals = (v1, v2, v3, v4, v5)
    out = dict(zip(BOOL_COLS, vals))
    out.update({
        "cases_evac_valid": all(vals),
        "conclusion": "通过" if all(vals) else "受限",
        "rule_anchors": ";".join(sorted(set(a1 + a2 + a3 + a4 + a5))),
    })
    return out


def all_cases():
    """枚举全部工况：8×2^8×3 = 6144 例。"""
    keys = [k for k, _ in DIMS]
    for values in product(*[dom for _, dom in DIMS]):
        inp = dict(zip(keys, values))
        yield inp, evaluate(inp)


def smoke_tests():
    base = {
        "scenario": "全管断电", "stair_width": "净宽达标", "cabin_count": "满配",
        "buoyancy_mode": "无源自主激发", "seal_mode": "自动机械复位",
        "timing_state": "四段全部达标", "interconnect": "互通完好",
        "geometry": "固定折返几何", "capacity": "承载力达标",
        "breathing": "独立呼吸管路",
    }
    checks = []

    def v(**kw):
        x = dict(base)
        x.update(kw)
        return evaluate(x)

    checks.append(("R-SFT-EVAC-01 净宽不足必须拦截", v(stair_width="净宽不足")["stair_no_block_flag"] is False))
    checks.append(("R-SFT-EVAC-02 舱位不足必须拦截", v(cabin_count="数量不足")["cabin_passive_buoy_valid"] is False))
    checks.append(("R-SFT-EVAC-03 纯电控启动必须拦截", v(buoyancy_mode="纯电控启动")["cabin_passive_buoy_valid"] is False))
    checks.append(("R-SFT-EVAC-04 无自封必须拦截", v(seal_mode="无自封能力")["channel_seal_recovery_valid"] is False))
    checks.append(("R-SFT-EVAC-05 时序超时必须拦截", v(timing_state="末段超时")["evac_3min_km3000_valid"] is False))
    checks.append(("R-SFT-EVAC-06 互通失效必须拦截", v(interconnect="互通缩减失效")["full_scenario_self_rescue_valid"] is False))
    checks.append(("R-SFT-EVAC-07 几何变更未复算必须拦截", v(geometry="几何变更未复算")["stair_no_block_flag"] is False))
    checks.append(("R-SFT-EVAC-08 承载力不足必须拦截", v(capacity="承载力不足")["evac_3min_km3000_valid"] is False))
    checks.append(("浓烟+集体供氧必须拦截", v(scenario="浓烟完全遮蔽", breathing="集体供氧")["full_scenario_self_rescue_valid"] is False))
    for name, ok in checks:
        assert ok, f"负注入未被拦截: {name}"
    return len(checks)


if __name__ == "__main__":
    total = passed = 0
    for _, out in all_cases():
        total += 1
        passed += out["cases_evac_valid"]
    n = smoke_tests()
    print(f"SINOSFT 疏散救生仿真自检：枚举 {total} 例，综合通过 {passed} 例，"
          f"受限 {total - passed} 例")
    print(f"负注入冒烟断言 {n}/{n} 全部捕获")
