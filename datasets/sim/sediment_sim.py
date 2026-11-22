#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SINO-Sediment 水库清淤决策数据集 —— 公开层仿真验证引擎

工程定位：为数据集八项决策能力提供可复现的计算依据，把「仅凭规则条文判定」
升级为「按工况档位逐条计算判定」。

保密边界（Principle Zero）：
  - 输入全部为语义档位枚举，不含任何物理量数值、材料构成或控制律；
  - 输出仅为布尔判定与规则锚点，不反推任何受控实现层参数；
  - 模型为档位化工程近似，用于判定逻辑可复现性验证，
    不作为工程设计、结构安全或竣工验收依据。

八模型（对应数据集决策一至八 / 规则 R1-R18）：
  M1 dredging_window_ok          清淤窗口期决策   决策一 / R8
  M2 tech_effective_ok           工艺有效性决策   决策二 / R3 R5 R7
  M3 route_compliant_ok          输送去向合规     决策四 / R4 R9 R10 R12
  M4 eco_compliant_ok            淤泥去向合规     决策五 / R1 R2 R12
  M5 dual_effect_verified_ok     双效果归因       决策三 / R6 R11
  M6 float_carrier_ok            浮体前置筛查     决策六 / R13 R14 R15 R16 R18
  M7 height_error_controlled_ok  高度误差受控     决策七 / R16 R17
  M8 service_life_match_ok       服役周期匹配     决策八 / R17 R18

所有函数纯函数、零外部依赖，第三方可逐条独立复算。
"""

from itertools import product

# ───────────────────────── 工况枚举域 ─────────────────────────
BODY_TIER = [
    "薄层-测量标注齐",      # 淤积薄、方法与精度已标注
    "中层-测量标注齐",
    "厚层-测量标注齐",
    "任意层-混级统计",      # R8：禁止混级统计
]
BACKFILL = ["低回淤", "高回淤"]                       # RESERVOIR.backfill_tendency
TECH_CONFIG = [
    "射流-交集足-搭接足-浓度达标",                    # 正常射流虹吸
    "射流-无交集",                                    # R3 自动否决
    "射流-搭接不足",                                  # 圆面扫掠漏清
    "射流-浓度低于基准",                              # R5 过水非清淤
]
ROUTE = [
    "水头足-容量足-分流匹配-台账闭合",
    "水头不足",                                       # R4
    "容量不足-分流超限",                              # R9 R10
    "台账缺失",                                       # R12
]
ECO = [
    "无超标-TSS未超",
    "重金属超标",                                     # R1
    "有机质超标",                                     # R2
    "TSS重度超标",                                    # 排放管控预警
]
EFFECT = [
    "双达标-实测值",
    "坝基未达标-固结龄期不足",                        # R6
    "下游减淤-设计值",                                # R11
    "双未达标",
]
FLOAT_SCHEME = [
    "储备足-冗余足-误差覆盖-无共振-试验检漏齐",
    "浮力储备不足",                                   # R14
    "共振风险-误差超预算",                            # R15 R16
    "单舱冗余不足-检漏缺失",                          # R13 R18
]

DIMS = [
    ("body_tier", BODY_TIER),
    ("backfill_tendency", BACKFILL),
    ("tech_config", TECH_CONFIG),
    ("route_state", ROUTE),
    ("eco_state", ECO),
    ("effect_state", EFFECT),
    ("float_scheme", FLOAT_SCHEME),
]

BOOL_COLS = [
    "dredging_window_ok",
    "tech_effective_ok",
    "route_compliant_ok",
    "eco_compliant_ok",
    "dual_effect_verified_ok",
    "float_carrier_ok",
    "height_error_controlled_ok",
    "service_life_match_ok",
]


def m1_dredging_window(inp):
    """决策一：测量数据可用 + 达到需清淤的厚度/回淤条件，才进入清淤窗口。"""
    b, back = inp["body_tier"], inp["backfill_tendency"]
    anchors = ["R8", "决策一"]
    if b == "任意层-混级统计":
        return False, anchors + ["R8-混级统计不可用"]
    if b == "薄层-测量标注齐" and back == "低回淤":
        return False, anchors + ["窗口未到"]      # 薄层低回淤，暂缓清淤
    return True, anchors


def m2_tech_effective(inp):
    """决策二：悬浮交集、搭接率、泥浆浓度三项共同决定工艺是否有效。"""
    t = inp["tech_config"]
    anchors = ["决策二"]
    if t == "射流-无交集":
        return False, anchors + ["R3"]
    if t == "射流-搭接不足":
        return False, anchors + ["漏清预警"]
    if t == "射流-浓度低于基准":
        return False, anchors + ["R5"]
    return True, anchors + ["R7"]                 # 通过时排除原因字段须量化可查


def m3_route_compliant(inp):
    """决策四：水头、受纳容量、分流比、台账联单四项闭合。"""
    r = inp["route_state"]
    anchors = ["决策四"]
    if r == "水头不足":
        return False, anchors + ["R4"]
    if r == "容量不足-分流超限":
        return False, anchors + ["R9", "R10"]
    if r == "台账缺失":
        return False, anchors + ["R12"]
    return True, anchors


def m4_eco_compliant(inp):
    """决策五：重金属/有机质污染刚性匹配处置去向，TSS 不得超限排放。"""
    e = inp["eco_state"]
    anchors = ["决策五"]
    if e == "重金属超标":
        return False, anchors + ["R1"]
    if e == "有机质超标":
        return False, anchors + ["R2"]
    if e == "TSS重度超标":
        return False, anchors + ["R12"]
    return True, anchors


def m5_dual_effect(inp):
    """决策三：坝基加固与下游减淤双目标独立验收，减淤量禁用水文设计值。"""
    e = inp["effect_state"]
    anchors = ["决策三"]
    if e == "坝基未达标-固结龄期不足":
        return False, anchors + ["R6"]
    if e == "下游减淤-设计值":
        return False, anchors + ["R11"]
    if e == "双未达标":
        return False, anchors + ["R6", "R11"]
    return True, anchors


def m6_float_carrier(inp):
    """决策六：浮体三项前置筛查——浮力储备、单舱冗余、共振/误差预算。"""
    f = inp["float_scheme"]
    anchors = ["决策六"]
    if f == "浮力储备不足":
        return False, anchors + ["R14"]
    if f == "共振风险-误差超预算":
        return False, anchors + ["R15", "R16"]
    if f == "单舱冗余不足-检漏缺失":
        return False, anchors + ["R13", "R18"]
    return True, anchors


def m7_height_error_controlled(inp):
    """决策七：误差可归因且处于受控状态；超预算或冗余失效须整改后再作业。"""
    f = inp["float_scheme"]
    anchors = ["决策七", "R16"]
    if f == "共振风险-误差超预算":
        return False, anchors + ["R15", "桁架挠曲归因"]  # 可归因但未受控
    if f == "单舱冗余不足-检漏缺失":
        return False, anchors + ["R18", "吃水漂移归因"]
    if f == "浮力储备不足":
        return False, anchors + ["R14", "吃水变化归因"]
    return True, anchors + ["R17"]


def m8_service_life_match(inp):
    """决策八：高回淤频次对浮体服役衰减提出更高要求；低频工况容许储备档放宽。"""
    f, back = inp["float_scheme"], inp["backfill_tendency"]
    anchors = ["决策八", "R17"]
    if f == "储备足-冗余足-误差覆盖-无共振-试验检漏齐":
        return True, anchors
    if f == "浮力储备不足":
        # 低回淤工况作业次数少，衰减累积有限；高回淤工况不接受
        return (back == "低回淤"), anchors + ["R14"]
    return False, anchors + ["R18"]


def evaluate(inp):
    """单案例八模型全评估，返回八布尔 + 综合结论 + 规则锚点。"""
    vals = []
    anchors = []
    for fn in (m1_dredging_window, m2_tech_effective, m3_route_compliant,
               m4_eco_compliant, m5_dual_effect, m6_float_carrier,
               m7_height_error_controlled, m8_service_life_match):
        ok, a = fn(inp)
        vals.append(ok)
        anchors.extend(a)
    valid = all(vals)
    out = dict(zip(BOOL_COLS, vals))
    out.update({
        "cases_decision_valid": valid,
        "conclusion": "通过" if valid else "受限",
        "rule_anchors": ";".join(sorted(set(anchors))),
    })
    return out


def all_cases():
    """枚举 多个语义档位的组合 = 8192 例，逐条仿真。"""
    keys = [k for k, _ in DIMS]
    for values in product(*[dom for _, dom in DIMS]):
        inp = dict(zip(keys, values))
        yield inp, evaluate(inp)


# ───────────────────────── 负注入冒烟断言 ─────────────────────────
def smoke_tests():
    checks = [
        ("R3 悬浮无交集必须否决工艺",
         m2_tech_effective({"tech_config": "射流-无交集"})[0] is False),
        ("R5 浓度低于基准必须判无效作业",
         m2_tech_effective({"tech_config": "射流-浓度低于基准"})[0] is False),
        ("R6 固结龄期不足必须否决坝基验收",
         m5_dual_effect({"effect_state": "坝基未达标-固结龄期不足"})[0] is False),
        ("R11 下游减淤设计值必须被拦截",
         m5_dual_effect({"effect_state": "下游减淤-设计值"})[0] is False),
        ("R14 浮力储备不足必须否决浮体方案",
         m6_float_carrier({"float_scheme": "浮力储备不足"})[0] is False),
        ("R8 混级统计必须否决清淤窗口",
         m1_dredging_window({"body_tier": "任意层-混级统计", "backfill_tendency": "高回淤"})[0] is False),
        ("R4 水头不足必须否决输送路径",
         m3_route_compliant({"route_state": "水头不足"})[0] is False),
        ("R1 重金属超标必须否决固坝利用",
         m4_eco_compliant({"eco_state": "重金属超标"})[0] is False),
    ]
    for name, ok in checks:
        assert ok, f"负注入未被拦截: {name}"
    return len(checks)


if __name__ == "__main__":
    total = passed = 0
    for _, out in all_cases():
        total += 1
        passed += out["cases_decision_valid"]
    n = smoke_tests()
    print(f"SINO-Sediment 仿真引擎自检：枚举 {total} 例，综合通过 {passed} 例，"
          f"受限 {total - passed} 例")
    print(f"负注入冒烟断言 {n}/{n} 全部捕获")
