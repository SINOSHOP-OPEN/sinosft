#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SINOSHOP–SinoSFT 海洋家园工程能源系统 —— 公开层仿真验证引擎

工程定位：
规范列出的 12 项能源技术若按"设备清单"并列登记，会掩盖真正的验收瓶颈：
能源采集必须服从"结构—能源—稳性—消防—通航"五约束，且主力能源、
补充回收能源、研发示范能源不得混算。本引擎把八个硬规则升级为按档位
可复算的五个布尔判定：

  net_available_power_valid        净可用功率有效（扣自耗/损耗/补偿后）
  stability_constraint_pass        稳性约束通过（吃水/倾角/共振未越限或已补偿）
  fire_safety_pass                 消防与隔离安全通过
  source_classification_valid      能源分层有效（研发项不冒充基荷）
  five_constraint_integration_pass 五约束集成通过

保密边界（Principle Zero）：
输入全部为语义档位，不含任何裸米制尺寸、材料构成、控制律或标定数值；
输出仅为布尔与规则锚点，不反推受控实现层参数。
模型为档位化工程近似，用于判定逻辑可复现性验证，
不作为结构设计、消防验收或并网友好性论证的直接依据。

八条硬规则锚点：R-SFT-EN-01 ~ R-SFT-EN-08，补充储能规则 R-SFT-EN-09
"""

from itertools import product

SEA_STATE = ["实测完备", "仅有设计边界", "数据缺失"]
FLOAT_REF = ["潮汐压载传感三绑定", "部分绑定", "未绑定"]
TIDAL_SEG = ["逐段核验", "笼统全程"]
CAVITATION = ["受控", "超阈值"]
WAVE_GRADE = ["达标", "低于设计值"]
ATTENUATION = ["达标", "功能降级"]
ISOLATION = ["可靠隔离", "混腔无隔离"]
BALLAST_COMP = ["有补偿", "无补偿"]
H2_INTERLOCK = ["联锁完备", "联锁缺失"]
DEEP_SEA = ["研发示范", "冒充基荷"]
VIBRATION = ["可用平均口径", "仅瞬时峰值口径"]
LOAD_CANCEL = ["控制优先", "发电优先"]
THERMAL_STORE = ["电热闭环可控", "无闭环"]

DIMS = [
    ("sea_state", SEA_STATE),
    ("float_reference", FLOAT_REF),
    ("tidal_segment", TIDAL_SEG),
    ("cavitation", CAVITATION),
    ("wave_grade", WAVE_GRADE),
    ("attenuation", ATTENUATION),
    ("storage_isolation", ISOLATION),
    ("ballast_comp", BALLAST_COMP),
    ("h2_interlock", H2_INTERLOCK),
    ("deep_sea_grade", DEEP_SEA),
    ("vibration_grade", VIBRATION),
    ("load_cancel", LOAD_CANCEL),
    ("thermal_store", THERMAL_STORE),
]

BOOL_COLS = [
    "net_available_power_valid",
    "stability_constraint_pass",
    "fire_safety_pass",
    "source_classification_valid",
    "five_constraint_integration_pass",
]


def m1_net_power(inp):
    """净可用功率：海域边界、浮体基准、分段核验、气蚀受控、波浪达标、振动口径同时成立。"""
    a = ["R-SFT-EN-01", "R-SFT-EN-06", "R-SFT-EN-07", "R-SFT-EN-08", "R-SFT-EN-09"]
    ok = (inp["sea_state"] != "数据缺失"
          and inp["float_reference"] == "潮汐压载传感三绑定"
          and inp["tidal_segment"] == "逐段核验"
          and inp["cavitation"] == "受控"
          and inp["wave_grade"] == "达标"
          and inp["vibration_grade"] == "可用平均口径"
          and inp["thermal_store"] == "电热闭环可控")
    if inp["sea_state"] == "仅有设计边界":
        a.append("设计值口径-不得计入可靠容量")
    return bool(ok), a


def m2_stability(inp):
    """稳性约束：压载补偿到位、消浪达标、载荷回收不损害控制目标。"""
    a = ["R-SFT-EN-02", "R-SFT-EN-03", "R-SFT-EN-08"]
    ok = (inp["ballast_comp"] == "有补偿"
          and inp["attenuation"] == "达标"
          and inp["load_cancel"] == "控制优先")
    if inp["load_cancel"] == "发电优先":
        a.append("回收收益侵占控制目标")
    return bool(ok), a


def m3_fire_safety(inp):
    """消防与隔离：储能舱与消防舱可靠隔离，制氢安全联锁完备。"""
    a = ["R-SFT-EN-04", "R-SFT-EN-05"]
    ok = (inp["storage_isolation"] == "可靠隔离"
          and inp["h2_interlock"] == "联锁完备")
    if inp["storage_isolation"] == "混腔无隔离":
        a.append("消防水可用性风险")
    return bool(ok), a


def m4_classification(inp):
    """能源分层：主力有实测边界，研发项不得冒充基荷，振动按可用平均口径。"""
    a = ["R-SFT-EN-01", "R-SFT-EN-06", "R-SFT-EN-07"]
    ok = (inp["sea_state"] == "实测完备"
          and inp["deep_sea_grade"] == "研发示范"
          and inp["vibration_grade"] == "可用平均口径")
    if inp["deep_sea_grade"] == "冒充基荷":
        a.append("研发项越级计入基荷")
    return bool(ok), a


def m5_five_constraints(inp, v1, v2, v3, v4):
    """五约束集成：四项判定全部成立，且浮体基准三绑定。"""
    a = ["R-SFT-EN-02", "R-SFT-EN-08"]
    ok = v1 and v2 and v3 and v4 and inp["float_reference"] == "潮汐压载传感三绑定"
    if inp["float_reference"] != "潮汐压载传感三绑定":
        a.append("恒定浮体基准未闭环")
    return bool(ok), a


def evaluate(inp):
    v1, a1 = m1_net_power(inp)
    v2, a2 = m2_stability(inp)
    v3, a3 = m3_fire_safety(inp)
    v4, a4 = m4_classification(inp)
    v5, a5 = m5_five_constraints(inp, v1, v2, v3, v4)
    vals = (v1, v2, v3, v4, v5)
    out = dict(zip(BOOL_COLS, vals))
    out.update({
        "cases_energy_valid": all(vals),
        "conclusion": "通过" if all(vals) else "受限",
        "rule_anchors": ";".join(sorted(set(a1 + a2 + a3 + a4 + a5))),
    })
    return out


def all_cases():
    """枚举全部档位组合：海域三档、基准三档、其余十一维各两档，共 18432 例。"""
    keys = [k for k, _ in DIMS]
    for values in product(*[dom for _, dom in DIMS]):
        inp = dict(zip(keys, values))
        yield inp, evaluate(inp)


def smoke_tests():
    base = {
        "sea_state": "实测完备", "float_reference": "潮汐压载传感三绑定",
        "tidal_segment": "逐段核验", "cavitation": "受控",
        "wave_grade": "达标", "attenuation": "达标",
        "storage_isolation": "可靠隔离", "ballast_comp": "有补偿",
        "h2_interlock": "联锁完备", "deep_sea_grade": "研发示范",
        "vibration_grade": "可用平均口径", "load_cancel": "控制优先",
        "thermal_store": "电热闭环可控",
    }
    checks = []

    def v(**kw):
        x = dict(base)
        x.update(kw)
        return evaluate(x)

    checks.append(("R01 数据缺失必须拦截", v(sea_state="数据缺失")["net_available_power_valid"] is False))
    checks.append(("R01 仅设计边界不得计可靠容量", v(sea_state="仅有设计边界")["source_classification_valid"] is False))
    checks.append(("R02 无压载补偿必须拦截", v(ballast_comp="无补偿")["stability_constraint_pass"] is False))
    checks.append(("R02 消浪功能降级必须拦截", v(attenuation="功能降级")["stability_constraint_pass"] is False))
    checks.append(("R03 发电优先侵占控制目标必须拦截", v(load_cancel="发电优先")["stability_constraint_pass"] is False))
    checks.append(("R04 储能消防混腔必须拦截", v(storage_isolation="混腔无隔离")["fire_safety_pass"] is False))
    checks.append(("R05 制氢联锁缺失必须拦截", v(h2_interlock="联锁缺失")["fire_safety_pass"] is False))
    checks.append(("R06 研发项冒充基荷必须拦截", v(deep_sea_grade="冒充基荷")["source_classification_valid"] is False))
    checks.append(("R07 仅瞬时峰值口径必须拦截", v(vibration_grade="仅瞬时峰值口径")["net_available_power_valid"] is False))
    checks.append(("R08 浮体基准未绑定必须拦截", v(float_reference="未绑定")["five_constraint_integration_pass"] is False))
    checks.append(("R08 笼统全程虹吸必须拦截", v(tidal_segment="笼统全程")["net_available_power_valid"] is False))
    checks.append(("气蚀超阈值必须拦截", v(cavitation="超阈值")["net_available_power_valid"] is False))
    checks.append(("R09 电热储能无闭环必须拦截", v(thermal_store="无闭环")["net_available_power_valid"] is False))
    for name, ok in checks:
        assert ok, f"负注入未被拦截: {name}"
    return len(checks)


if __name__ == "__main__":
    total = passed = 0
    for _, out in all_cases():
        total += 1
        passed += out["cases_energy_valid"]
    n = smoke_tests()
    print(f"SINOSFT 工程能源仿真自检：枚举 {total} 例，综合通过 {passed} 例，"
          f"受限 {total - passed} 例")
    print(f"负注入冒烟断言 {n}/{n} 全部捕获")
