# -*- coding: utf-8 -*-
"""统一运行器：只做调用与汇总，不含任何判据逻辑。"""
import pathlib, re, subprocess, sys

HERE = pathlib.Path(__file__).resolve().parent
SCRIPTS = sorted(HERE.glob("public_verify_*.py"))
PATS = [r"断言脚本（(\d+) 项通过 / (\d+) 项失败）",
        r"断言：(\d+) 通过 / (\d+) 失败",
        r"断言脚本：(\d+) 通过 / (\d+) 失败",
        r"断言汇总：(\d+) 通过 / (\d+) 失败",
        r"断言\s*[:：]\s*(\d+)\s*通过"]

def main():
    total, bad = 0, 0
    print("SINOSFT · 512 项物理断言与仿真验证框架")
    print("-" * 68)
    for p in SCRIPTS:
        r = subprocess.run([sys.executable, p.name], cwd=str(HERE),
                           capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
        n = 0
        for pat in PATS:
            m = re.search(pat, r.stdout or "")
            if m:
                n = int(m.group(1)); break
        total += n
        bad += 1 if (r.returncode != 0 or n == 0) else 0
        print("  %-46s exit=%d  %3d 项" % (p.name, r.returncode, n))
    print("-" * 68)
    print("脚本 %d 支 | 断言合计 %d 项 | 异常 %d 支" % (len(SCRIPTS), total, bad))
    print("结论: " + ("全部通过" if bad == 0 else "存在失败项，请逐支排查"))
    return 0 if bad == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
