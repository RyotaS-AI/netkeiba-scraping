import os
import sys
import re
from datetime import datetime
from bs4 import BeautifulSoup

import config
from utils import format_race_id, get_shared_race_name
from scraper import NetkeibaScraper
from parsers.oikiri_parser import parse_oikiri
from parsers.comment_parser import parse_comment
from parsers.past_race_parser import parse_past_race
from exporter import save_to_csv, check_race_exists_on_drive  # 追加

def run_netkeiba(race_id):
    """netkeibaからレース名を取得し、追い切り・厩舎コメント・馬柱データを取得・保存。
    レース名を返す。
    """
    scraper = NetkeibaScraper(config.NETKEIBA_LOGIN_ID, config.NETKEIBA_PASSWORD)

    # URL設定
    shutuba_url       = f"https://race.netkeiba.com/race/shutuba.html?race_id={race_id}&rf=race_submenu"
    oikiri_chukan_url = f"https://race.netkeiba.com/race/oikiri.html?race_id={race_id}&type=1&rf=shutuba_submenu"
    oikiri_saishu_url = f"https://race.netkeiba.com/race/oikiri.html?race_id={race_id}&type=2&rf=shutuba_submenu"
    comment_url       = f"https://race.netkeiba.com/race/comment.html?race_id={race_id}&rf=race_submenu"
    past_race_url     = f"https://race.netkeiba.com/race/shutuba_past_9.html?race_id={race_id}&rf=shutuba_submenu"

    # 出馬表HTMLからレース名を取得（CSV出力なし）
    print("netkeibaからレース名を取得中...")
    shutuba_html = scraper.get_html(shutuba_url)
    soup = BeautifulSoup(shutuba_html, 'html.parser')
    race_name_el = soup.find(class_='RaceName') or soup.find(class_='RaceList_NameBox')
    race_name = race_name_el.text.strip() if race_name_el else "不明なレース名"
    print(f"レース名: {race_name}")

    # 1. 中間追い切り
    print("\n[1/4] 中間追い切りデータの取得")
    oikiri_chukan_html = scraper.get_html(oikiri_chukan_url)
    df_chukan = parse_oikiri(oikiri_chukan_html)
    if not df_chukan.empty:
        save_to_csv(df_chukan, race_id, race_name, "中間追い切り")
    else:
        print("中間追い切りデータの抽出に失敗しました（データなし）")

    # 2. 最終追い切り
    print("\n[2/4] 最終追い切りデータの取得")
    oikiri_saishu_html = scraper.get_html(oikiri_saishu_url)
    df_saishu = parse_oikiri(oikiri_saishu_html, is_final=True)
    if not df_saishu.empty:
        save_to_csv(df_saishu, race_id, race_name, "最終追い切り")
    else:
        print("最終追い切りデータの抽出に失敗しました（データなし）")

    # 3. 厩舎コメント
    print("\n[3/4] 厩舎コメントデータの取得")
    comment_html = scraper.get_html(comment_url)
    df_comment = parse_comment(comment_html)
    if not df_comment.empty:
        save_to_csv(df_comment, race_id, race_name, "厩舎コメント")
    else:
        print("厩舎コメントデータの抽出に失敗しました（データなし）")

    # 4. 馬柱データ(5走)
    print("\n[4/4] 馬柱データ(5走)の取得")
    past_race_html = scraper.get_html(past_race_url)
    df_past = parse_past_race(past_race_html)
    if not df_past.empty:
        save_to_csv(df_past, race_id, race_name, "馬柱データ")
    else:
        print("馬柱データの抽出に失敗しました（データなし）")

    print("\nnetkeibaデータの抽出と保存が完了しました。")
    return race_name


def run_yahoo(race_id, race_name):
    """Yahooから出馬表・各種オッズを取得・保存"""
    print("\n=== Yahooスポーツナビ競馬データ取得 ===")

    today_str = datetime.now().strftime("%Y%m%d")
    yahoo_race_id = format_race_id(race_id, to_yahoo=True)  # アクセス用10桁
    print(f"Yahoo用 race_id: {yahoo_race_id}")

    # ログイン不要なため空文字で初期化し、スリープ機能のみを利用する
    scraper = NetkeibaScraper("", "")

    # URL定義
    base_url = "https://sports.yahoo.co.jp/keiba/race"
    urls = {
        "出馬表":        f"{base_url}/denma/{yahoo_race_id}",
        "単勝_複勝_枠連": f"{base_url}/odds/tfw/{yahoo_race_id}",
        "馬単":         f"{base_url}/odds/ut/{yahoo_race_id}?ninki=0",
        "馬連":         f"{base_url}/odds/ur/{yahoo_race_id}?ninki=0",
        "ワイド":        f"{base_url}/odds/wide/{yahoo_race_id}?ninki=0",
        "3連複":        f"{base_url}/odds/sf/{yahoo_race_id}?ninki=0"
    }

    from parsers.yahoo_denma_parser import parse_yahoo_denma
    from parsers.yahoo_odds_parser import (
        parse_tansho, parse_fukusho, parse_wakuren,
        parse_umatan, parse_umaren, parse_wide, parse_sanrenpuku
    )

    # 1. 出馬表
    print(f"\n[1/6] 出馬表データの取得: {urls['出馬表']}")
    html_denma = scraper.get_html(urls['出馬表'])
    df_denma = parse_yahoo_denma(html_denma)
    if not df_denma.empty:
        save_to_csv(df_denma, race_id, race_name, f"yahoo_出馬表_{today_str}")
    else:
        print("出馬表データの抽出に失敗しました（データなし）")

    # 2. 単勝・複勝・枠連 (tfw)
    print(f"\n[2/6] 単勝・複勝・枠連データの取得: {urls['単勝_複勝_枠連']}")
    html_tfw = scraper.get_html(urls['単勝_複勝_枠連'])

    df_tansho = parse_tansho(html_tfw)
    if not df_tansho.empty: save_to_csv(df_tansho, race_id, race_name, f"yahoo_単勝_{today_str}")

    df_fukusho = parse_fukusho(html_tfw)
    if not df_fukusho.empty: save_to_csv(df_fukusho, race_id, race_name, f"yahoo_複勝_{today_str}")

    df_wakuren = parse_wakuren(html_tfw)
    if not df_wakuren.empty: save_to_csv(df_wakuren, race_id, race_name, f"yahoo_枠連_{today_str}")

    # 3. 馬単
    print(f"\n[3/6] 馬単データの取得: {urls['馬単']}")
    html_ut = scraper.get_html(urls['馬単'])
    df_umatan = parse_umatan(html_ut)
    if not df_umatan.empty:
        save_to_csv(df_umatan, race_id, race_name, f"yahoo_馬単_{today_str}")

    # 4. 馬連
    print(f"\n[4/6] 馬連データの取得: {urls['馬連']}")
    html_ur = scraper.get_html(urls['馬連'])
    df_umaren = parse_umaren(html_ur)
    if not df_umaren.empty:
        save_to_csv(df_umaren, race_id, race_name, f"yahoo_馬連_{today_str}")

    # 5. ワイド
    print(f"\n[5/6] ワイドデータの取得: {urls['ワイド']}")
    html_wide = scraper.get_html(urls['ワイド'])
    df_wide = parse_wide(html_wide)
    if not df_wide.empty:
        save_to_csv(df_wide, race_id, race_name, f"yahoo_ワイド_{today_str}")

    # 6. 3連複
    print(f"\n[6/6] 3連複データの取得: {urls['3連複']}")
    html_sf = scraper.get_html(urls['3連複'])
    df_sanren = parse_sanrenpuku(html_sf)
    if not df_sanren.empty:
        save_to_csv(df_sanren, race_id, race_name, f"yahoo_3連複_{today_str}")

    print("\nすべてのYahooデータの抽出と保存が完了しました。")


def main():
    print("=== 競馬スクレイピングツール ===")
    if len(sys.argv) > 1:
        race_id = sys.argv[1].strip()
    else:
        race_id = input("対象レースのrace_id(12桁)を入力してください: ").strip()

    if not re.fullmatch(r'\d{12}', race_id):
        print("エラー: race_idは12桁の数値で入力してください。")
        sys.exit(1)

    # ローカルフォルダではなくGoogle Driveで初回/2回目を判定
    race_name = check_race_exists_on_drive(race_id)
    is_first_run = (race_name == "")

    if is_first_run:
        print(f"\n[初回処理] race_id: {race_id}")
        race_name = run_netkeiba(race_id)
        run_yahoo(race_id, race_name)
    else:
        print(f"\n[２回目以降処理] race_id: {race_id}, レース名: {race_name}")
        run_yahoo(race_id, race_name)

    print("\nすべての処理が完了しました。")


if __name__ == "__main__":
    main()
