"""
schedule.jsonを読み込み、現在時刻から30分以内に予定されているrace_idを実行する。
"""
import json
import subprocess
import sys
from datetime import datetime, timezone, timedelta

JST = timezone(timedelta(hours=9))
WINDOW_MINUTES = 30


def main():
    with open("schedule.json", encoding="utf-8") as f:
        schedule = json.load(f)

    now = datetime.now(JST)
    print(f"現在時刻 (JST): {now.strftime('%Y-%m-%d %H:%M')}")

    targets = []
    for entry in schedule:
        race_id = entry["race_id"]
        hh, mm = map(int, entry["jst"].split(":"))
        scheduled = now.replace(hour=hh, minute=mm, second=0, microsecond=0)
        diff = (now - scheduled).total_seconds()
        if 0 <= diff < WINDOW_MINUTES * 60:
            targets.append(race_id)
            print(f"実行対象: race_id={race_id} (予定時刻={entry['jst']})")

    if not targets:
        print("実行対象のrace_idはありません。")
        return

    for race_id in targets:
        print(f"\n=== race_id: {race_id} を実行中 ===")
        result = subprocess.run(["python", "main.py", race_id])
        if result.returncode != 0:
            print(f"エラー: race_id={race_id} の実行に失敗しました")
            sys.exit(1)


if __name__ == "__main__":
    main()
