# SINOSFT · 512 项物理断言与仿真验证框架（脱敏公开版）

> **人可以写文案，但不能写 PASS。** 本目录的每一个结论都由脚本实跑判定，
> 退出码 0 为唯一验收判据。任何人 clone 下来都能当场复现。

---

## 确权声明

> **SINOSFT 核心技术数据集已启动国家知识产权与数据资产合规登记
> （首单登记号 SZ2026110011630.1）。开源部分遵循 Apache-2.0 协议，核心机密数据受法律保护。**

本目录仅包含**验证框架与对外口径的仿真结果判据**。核心技术与机密数据不在
公开范围内，长期保密。本目录以 **Apache License 2.0** 授权，全文见 [`LICENSE`](LICENSE)。

---

## 这是什么

15 支相互独立的验证脚本，覆盖消浪、动态载荷抵消、恒定高度、材料、
缆索应力、泊位流、载荷传递、全生命周期经济性、压力卸载、频带分配、
载荷调度与 A×B 耦合等验证主线，合计 **512 项断言**。

脚本内建**红线自检**：对外表达中不得出现发电量绝对值、成本金额、
抗台风能力宣称、未标注出处的实测输入；任一违例即断言失败、退出码非 0。

| 脚本 | 断言 | 退出码 |
|---|---:|---:|
| `public_verify_01_wave_attenuation_381m.py` | 16 | 0 |
| `public_verify_02_lcs_load_cancellation.py` | 37 | 0 |
| `public_verify_03_tidal_height_constant.py` | 38 | 0 |
| `public_verify_04_wave_multilevel.py` | 19 | 0 |
| `public_verify_05_lcs_tonnage.py` | 43 | 0 |
| `public_verify_06_composite_material.py` | 25 | 0 |
| `public_verify_07_cable_stress.py` | 47 | 0 |
| `public_verify_08_tidal48.py` | 35 | 0 |
| `public_verify_09_bidirectional_berth_flow.py` | 51 | 0 |
| `public_verify_10_load_transfer.py` | 33 | 0 |
| `public_verify_11_economics_lcc.py` | 50 | 0 |
| `public_verify_12_pressure_unload.py` | 66 | 0 |
| `public_verify_13_band_allocation.py` | 19 | 0 |
| `public_verify_14_load_allocation.py` | 17 | 0 |
| `public_verify_15_ab_coupling.py` | 16 | 0 |
| **合计** | **512** | **0** |

> 依赖：Python 3.8+ 与 numpy。每支脚本独立运行，不需要其它脚本。

## 快速开始

```bash
pip install numpy
python run_all.py          # 统一运行 15 支并汇总
# 或单支运行
python public_verify_01_wave_attenuation_381m.py
echo $?                    # 0 = 全部断言通过
```

`run_all.py` 只做调用与汇总，不含任何判据逻辑；判据全部在各验证脚本内。
`SHA256SUMS.txt` 记录本目录全部文件的 SHA-256 与生成时间戳，按 **Git 仓库 blob（LF 规范字节）** 计算，跨平台一致，不受本地行尾转换影响；复核命令见该清单文件头。

## 诚实边界

- 这些脚本是**机理级（LEVEL-0）参数化筛选计算**，不替代物理模型缩尺试验与实测验证；
  段参数须以试验数据标定后方可作为工程依据引用。
- 假设项在脚本内以 `assumptions` 字段显式登记，段参数是**待标定的假设值**而非实测值。
- 准静态模型不解析路面局部弯曲、板块内应力分布与自由液面晃荡；
  行驶冲击线的动态残余为保守上界。
- 在极端微观交叉工况上，我们依然在通过开源仿真不断优化。
- **位移判据适用于准静态驻停**；行驶工况属平顺性域，评价指标为路面加速度，
  两者不可混用。我们主动把这一边界写进断言——用错判据比超出判据更危险。

## 我们也接受反驳

所有假设项都显式登记。若您认为某项判据不成立，请直接跑对应脚本、
指出具体断言，或提交 issue。开放验证的本意就是让结论经得起独立复核。

---

*本目录为 SINOSFT 公开验证件。核心技术与机密数据不在开源范围内。*
