"""
馬柱データ(5走) 機能テスト
race_id=202609011011 (阪神大賞典) を対象に、ログイン済みスクレイパーで
HTML を取得してパースし、output フォルダへ CSV を出力する。

実行方法:
    py test_past_race.py
"""
import logging
import config
from scraper import NetkeibaScraper
from parsers.past_race_parser import parse_past_race
from exporter import save_to_csv

logging.basicConfig(level=logging.INFO, format="%(message)s")

RACE_ID   = "202609011011"
RACE_NAME = "阪神大賞典"

def main():
    url = f"https://race.netkeiba.com/race/shutuba_past_9.html?race_id={RACE_ID}&rf=shutuba_submenu"

    print(f"=== 馬柱データ(5走) テスト ===")
    print(f"race_id : {RACE_ID}")
    print(f"URL     : {url}")
    print()

    scraper = NetkeibaScraper(config.NETKEIBA_LOGIN_ID, config.NETKEIBA_PASSWORD)

    print("HTMLを取得中...")
    html = scraper.get_html(url)
    if not html:
        print("ERROR: HTML の取得に失敗しました。")
        return

    # 取得した HTML をファイルに保存（次回以降のデバッグ用）
    with open("docs/馬柱データHTML_login.txt", "w", encoding="utf-8") as f:
        f.write(html)
    print("HTML を docs/馬柱データHTML_login.txt に保存しました。")

    print("パース中...")
    df = parse_past_race(html)

    if df.empty:
        print("ERROR: データの抽出に失敗しました（データなし）。")
        return

    print(f"\n--- パース結果（{len(df)} 頭） ---")
    # 幅が広いため基本情報と前走のみ表示
    cols_preview = ["枠", "馬番", "馬名", "今走(前走間隔)", "斤量",
                    "前走日付", "前走(前走間隔)", "前走競馬場名", "前走レース名",
                    "前走着順", "前走斤量", "前走4角通過順", "前走着差(秒)", "前走場体重"]
    print(df[cols_preview].to_string(index=False))

    save_to_csv(df, RACE_ID, RACE_NAME, "馬柱データ")
    print(f"\nCSV を output/{RACE_ID}_{RACE_NAME}_馬柱データ.csv に保存しました。")

if __name__ == "__main__":
    main()
