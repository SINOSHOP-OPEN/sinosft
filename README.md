<div align="center">

![晨雾中的跨海大桥 · 长虹卧波](media/seascape/sft_bridge_dawn.jpg)

# SinoSFT —— 共建共享，海洋家园，众志成城。

### 跨海悬浮隧道浮桥 · 以数学为宪法，以代码为城墙

> **观天之道，执天之行。以术载道，造福众生。**

<br>

<div align="center">

*愿海如镜，人如舟。*

</div>

<br>

[![数学内核](https://img.shields.io/badge/数学内核-Lean%204%20%2B%20Z3%20SMT-2ea88c?style=flat-square&logo=lean&logoColor=white)](https://gitee.com/sinoshop/sinosft)

[![Apache-2.0 License](https://img.shields.io/badge/License-Apache--2.0-2ea88c?style=flat-square)](LICENSE)

</div>

---

## 三大版图矩阵

> SinoPORT（悬浮港）解决重载稳态，SinoSFT（跨海隧道）探索空间跨越，
> SINOSHOP（海洋城市）构建生态人居。**三者合一，拼凑出属于未来的海洋文明。**

| 版图 | 定位 | 主张 | 仓库 |
|:--|:--|:--|:--|
| **SinoPORT** | 悬浮港 | 无桩基超级刚体，重载交通下保持毫米级平顺作业面 | [gitee](https://gitee.com/sinoshop/SinoPORT) ｜ [GitHub](https://github.com/SINOSHOP-OPEN/SinoPORT) |
| **SinoSFT** | 跨海隧道 | 以数学为宪法，探索深海跨越的全新结构形态 | **本仓库** ｜ [GitHub](https://github.com/SINOSHOP-OPEN/sinosft) |
| **SINOSHOP** | 海洋城市 | 可移动、抗台风、人海和谐的生态花园社区 | [gitee](https://gitee.com/sinoshop/sinoshop-os) ｜ [GitHub](https://github.com/SINOSHOP-OPEN/SINOSHOP) |

---

## 卷首 · 海之底色

**探索深海跨越的全新结构形态，连接孤岛与大陆，以术载道，跨越天堑。**

海底隧道与跨海大桥，是人类跨越深水的两种经典答案。
前者埋入海床，受地质、断层与施工窗口的长期约束；后者架于水面，
受风浪、台风与航道净空的持续考验。

SinoSFT 探索第三条路 —— **悬浮**。
让隧道结构既不锚固于海床、也不完全暴露于水面，而是在特定水深带内
由浮力与系泊共同约束，**随载荷自适应地维持其形态**。

这条路的门槛不在工程，而在**数学**：
如果不能把这条结构的形式化性质写成可被机器证明的命题，
那么它就只是一张漂亮的示意图。因此我们以数学为宪法，以代码为城墙。

### 技术栈

`Z3 SMT` `Lean 4` `Python` `Monte Carlo` `FFT` `Tube-MPC` `JONSWAP` `SFT`

### 物理链条（概念示意）

```
极端外海涌浪 → 消浪与缓冲体系 → 港内平稳水域 → 结构自持平衡 → 轨道平顺度达标
```

---

## 中卷 · 四季流转

<div align="center">

![夏日波光](media/seascape/summer_sparkle.jpg)

</div>

### 已验证的公理

我们把关键的形式化性质交给证明器判定 —— 不是"我们认为成立"，
而是"机器已经确认成立"。

| 公理 | 方法 | 状态 |
|:--|:--|:--|
| 静力平衡 | Lean 4 | **PROVED** |
| 时滞鲁棒稳定性 | Z3 SMT | **PROVED** |
| 防波堤透射系数 | Z3 SMT | **PROVED** |
| 潮汐虹吸能量自持 | Z3 SMT | **PROVED** |
| 全系统耦合稳定性 | Monte Carlo | **PROVED** |

> **人可以写文案，但不能写 PASS。**
> 公理不是描述，是**判定结果** —— 证明器不接受近似，不接受人工修饰。

### 仓库结构

```
sinosft/
├── CONTRIBUTING.md      ← 参与方式 · 数字存证与共建共享
├── LICENSE
├── README.md            ← 本文件
└── README.en.md         ← English version
```

数学内核的完整形式化证明代码位于
**[sinosft-core-math](https://gitee.com/sinosft/sinosft-core-math)** ——
本仓库是**公开发布面**，呈现标准总入口与验证结论。

### 生态应用

基于 SinoSFT 定义的核心标准与物理架构，以下项目将理论应用于工程实践：

- **[SINOSHIP/sinoshop-openice](https://gitee.com/SINOSHIP/sinoshop-openice) — 极地氢能全链条仿真平台**
  完整遵循 SinoSFT 的物理基准，提供高保真仿真与算法验证环境。

- **[SINOSHIP/sinoship](https://gitee.com/SINOSHIP/sinoship) — 船舶设计与航运开源基础设施**
  面向船舶建模、仿真与优化的开源工具集，是 SinoSFT 架构在船舶工程领域的延伸应用。

- **[sinoshop/sinoshop-os](https://gitee.com/sinoshop/sinoshop-os) — 海洋城市**
  将跨越能力延伸为可居住的海上空间。

---

## 谁在推动

- **SINOSHOP** —— 设计与工程团队
- 开放协作：任何人都可以提交 issue、复现验证、提出改进
- 贡献即确权 —— 详见 [`CONTRIBUTING.md` 第七章](CONTRIBUTING.md)

---

## 许可与引用

代码与图面遵循本仓库 `LICENSE`（Apache-2.0）。
引用本项目时请注明出处。

---

## 尾卷 · 月夜归航

<div align="center">

![月光洒在海面上](media/seascape/moonlight_sea.jpg)

**共建共享，海洋家园，众志成城**

---

### 人可以写文案，但不能写 PASS。

*愿海如镜，人如舟。*

</div>
