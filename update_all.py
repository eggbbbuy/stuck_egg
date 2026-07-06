"""重新產生 stocks.txt 內所有股票的 技術面 + 基本面 JSON。
本機或 GitHub Actions 皆可跑：python update_all.py"""
import subprocess, sys, os

HERE = os.path.dirname(os.path.abspath(__file__))


def run(script, args):
    print("→", script, *args, flush=True)
    subprocess.run([sys.executable, os.path.join(HERE, script)] + args,
                   cwd=HERE, check=True)


def main():
    with open(os.path.join(HERE, "stocks.txt"), encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            code = parts[0]
            suf = parts[1] if len(parts) > 1 else "auto"
            try:
                run("gen_tech.py", [code, suf])
                run("gen_fund.py", [code])
                run("gen_val.py", [code, suf])
                run("gen_chip.py", [code])
                run("gen_events.py", [code])
            except Exception as e:
                print(f"!! {code} 失敗: {e}", flush=True)
    # 對應相關美股最近收盤（一次抓全部）
    try:
        run("gen_us.py", [])
    except Exception as e:
        print(f"!! gen_us 失敗: {e}", flush=True)
    # 美股資訊分頁(us.html) 的資料
    try:
        run("gen_usmkt.py", [])
    except Exception as e:
        print(f"!! gen_usmkt 失敗: {e}", flush=True)


if __name__ == "__main__":
    main()
