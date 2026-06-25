"""盤中即時報價迴圈 — 在本機(這台電腦)每隔 N 秒抓 Yahoo 報價並 push quotes.json 到 GitHub。

為什麼不用 GitHub Actions 排程：GitHub 對高頻 cron(*/10 這種)會大量略過/延遲，
實測整個上午一次都沒跑，導致首頁價格卡住。本機迴圈才可靠。

限制：需要這台電腦在盤中開著(本來就會開著跑 bot)。
用法：python quote_loop.py   (建議背景常駐)
"""
import subprocess, time, datetime, sys, os

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = os.path.dirname(os.path.abspath(__file__))
INTERVAL = 120          # 盤中每 2 分鐘更新一次
OFF_SLEEP = 300         # 非盤中每 5 分鐘檢查一次


DAILY_STAMP = os.path.join(HERE, "_last_daily.txt")   # 記錄每日更新最後跑的日期


def tw_now():
    return datetime.datetime.utcnow() + datetime.timedelta(hours=8)


def is_market_hours(t):
    if t.weekday() >= 5:                         # 週六日
        return False
    mins = t.hour * 60 + t.minute
    return 9 * 60 <= mins <= 13 * 60 + 35        # 09:00–13:35 (含尾盤)


def daily_done_today(t):
    try:
        return open(DAILY_STAMP, encoding="utf-8").read().strip() == t.strftime("%Y-%m-%d")
    except Exception:
        return False


def run(cmd):
    return subprocess.run(cmd, cwd=HERE, shell=True, capture_output=True, text=True)


def run_daily_update(t):
    """盤後(收盤後)本機跑一次完整每日更新並 push，不等 GitHub 傍晚排程。"""
    print(f"[{t:%m-%d %H:%M}] 盤後每日更新開始…", flush=True)
    run("python update_all.py")
    run("git add -A")
    if run("git diff --staged --quiet").returncode == 0:
        open(DAILY_STAMP, "w", encoding="utf-8").write(t.strftime("%Y-%m-%d"))
        print(f"[{t:%m-%d %H:%M}] 每日更新無變動", flush=True)
        return
    run(f'git commit -q -m "本機盤後每日更新 {t:%Y-%m-%d}"')
    run("git pull --rebase --autostash -q")
    p = run("git push -q")
    open(DAILY_STAMP, "w", encoding="utf-8").write(t.strftime("%Y-%m-%d"))
    print(f"[{t:%m-%d %H:%M}] 每日更新 {'push 成功' if p.returncode == 0 else 'push 失敗:'+(p.stderr or '')[:120]}", flush=True)


def push_quotes():
    run("python gen_quote.py")
    run("git add -- quotes.json")
    if run("git diff --staged --quiet").returncode == 0:
        return "no-change"
    run('git commit -q -m "intraday quotes (local loop)"')
    run("git pull --rebase --autostash -q")
    p = run("git push -q")
    return "pushed" if p.returncode == 0 else f"push-fail: {(p.stderr or '')[:120]}"


def main():
    print(f"quote_loop 啟動 (盤中每 {INTERVAL}s 更新)")
    while True:
        t = tw_now()
        if is_market_hours(t):
            try:
                r = push_quotes()
            except Exception as e:
                r = f"error: {e}"
            print(f"[{t:%m-%d %H:%M}] {r}", flush=True)
            time.sleep(INTERVAL)
        else:
            # 收盤後(平日 13:36 起)當天還沒跑過 → 自動補今天的每日更新(僅一次)
            mins = t.hour * 60 + t.minute
            if t.weekday() < 5 and mins >= 13 * 60 + 36 and not daily_done_today(t):
                try:
                    run_daily_update(t)
                except Exception as e:
                    print(f"[{t:%m-%d %H:%M}] 每日更新錯誤: {e}", flush=True)
            else:
                print(f"[{t:%m-%d %H:%M}] 非盤中，休息", flush=True)
            time.sleep(OFF_SLEEP)


if __name__ == "__main__":
    main()
