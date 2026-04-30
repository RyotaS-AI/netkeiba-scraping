import os
from datetime import datetime
from parsers.oikiri_parser import parse_oikiri
from parsers.comment_parser import parse_comment
from parsers.past_race_parser import parse_past_race
from parsers.yahoo_denma_parser import parse_yahoo_denma
from parsers.yahoo_odds_parser import (
    parse_tansho, parse_fukusho, parse_wakuren,
    parse_umatan, parse_umaren, parse_wide, parse_sanrenpuku
)
from exporter import save_to_csv


def test_local_parsing():
    print("=== ローカルHTMLパーステスト ===")
    race_id = "test_2026"
    race_name = "テスト用サンプルレース"

    # 1. 中間追い切り
    try:
        html = open(r'docs\中間追い切りHTML.txt', 'r', encoding='utf-8', errors='ignore').read()
        df = parse_oikiri(html)
        print("\n--- 中間追い切りデータ ---")
        print(df.head())
        save_to_csv(df, race_id, race_name, "中間追い切り")
    except Exception as e:
        print(f"中間追い切りパースエラー: {e}")

    # 2. 最終追い切り
    try:
        html = open(r'docs\最終追い切りHTML.txt', 'r', encoding='utf-8', errors='ignore').read()
        df = parse_oikiri(html, is_final=True)
        print("\n--- 最終追い切りデータ ---")
        print(df.head())
        save_to_csv(df, race_id, race_name, "最終追い切り")
    except Exception as e:
        print(f"最終追い切りパースエラー: {e}")

    # 3. 厩舎コメント
    try:
        html = open(r'docs\庁舎コメントHTML.txt', 'r', encoding='utf-8', errors='ignore').read()
        df = parse_comment(html)
        print("\n--- 厩舎コメントデータ ---")
        print(df.head())
        save_to_csv(df, race_id, race_name, "厩舎コメント")
    except Exception as e:
        print(f"厩舎コメントパースエラー: {e}")

    # 4. 馬柱データ(5走)
    # ログイン済みで保存したHTMLがあればそちらを優先する（test_past_race.py で生成）
    try:
        html_path = r'docs\馬柱データHTML_login.txt'
        enc = 'utf-8'
        if not os.path.exists(html_path):
            html_path = r'docs\馬柱データHTML.txt'
            enc = 'euc-jp'
        html = open(html_path, 'r', encoding=enc, errors='ignore').read()
        df = parse_past_race(html)
        print("\n--- 馬柱データ(5走) ---")
        print(df.to_string())
        save_to_csv(df, race_id, race_name, "馬柱データ")
    except Exception as e:
        print(f"馬柱データパースエラー: {e}")

    # 5. Yahoo出馬表
    try:
        html = open(r'docs\v_test_yahoo_denma.html', 'r', encoding='utf-8', errors='ignore').read()
        df = parse_yahoo_denma(html)
        print("\n--- Yahoo出馬表データ ---")
        print(df.head())
        save_to_csv(df, race_id, race_name, f"yahoo_出馬表_{datetime.now().strftime('%Y%m%d')}")
    except Exception as e:
        print(f"Yahoo出馬表パースエラー: {e}")

    # 6. Yahoo単勝・複勝・枠連
    try:
        html = open(r'docs\v_test_yahoo_tfw.html', 'r', encoding='utf-8', errors='ignore').read()

        df = parse_tansho(html)
        print("\n--- Yahoo単勝データ ---")
        print(df.head())
        save_to_csv(df, race_id, race_name, "yahoo_単勝")

        df = parse_fukusho(html)
        print("\n--- Yahoo複勝データ ---")
        print(df.head())
        save_to_csv(df, race_id, race_name, "yahoo_複勝")

        df = parse_wakuren(html)
        print("\n--- Yahoo枠連データ ---")
        print(df.head())
        save_to_csv(df, race_id, race_name, "yahoo_枠連")
    except Exception as e:
        print(f"Yahoo単勝・複勝・枠連パースエラー: {e}")

    # 7. Yahoo馬単
    try:
        html = open(r'docs\v_test_yahoo_ut.html', 'r', encoding='utf-8', errors='ignore').read()
        df = parse_umatan(html)
        print("\n--- Yahoo馬単データ ---")
        print(df.head())
        save_to_csv(df, race_id, race_name, "yahoo_馬単")
    except Exception as e:
        print(f"Yahoo馬単パースエラー: {e}")

    # 8. Yahoo馬連
    try:
        html = open(r'docs\v_test_yahoo_ur.html', 'r', encoding='utf-8', errors='ignore').read()
        df = parse_umaren(html)
        print("\n--- Yahoo馬連データ ---")
        print(df.head())
        save_to_csv(df, race_id, race_name, "yahoo_馬連")
    except Exception as e:
        print(f"Yahoo馬連パースエラー: {e}")

    # 9. Yahooワイド
    try:
        html = open(r'docs\v_test_yahoo_wide.html', 'r', encoding='utf-8', errors='ignore').read()
        df = parse_wide(html)
        print("\n--- Yahooワイドデータ ---")
        print(df.head())
        save_to_csv(df, race_id, race_name, "yahoo_ワイド")
    except Exception as e:
        print(f"Yahooワイドパースエラー: {e}")

    # 10. Yahoo3連複
    try:
        html = open(r'docs\v_test_yahoo_sf.html', 'r', encoding='utf-8', errors='ignore').read()
        df = parse_sanrenpuku(html)
        print("\n--- Yahoo3連複データ ---")
        print(df.head())
        save_to_csv(df, race_id, race_name, "yahoo_3連複")
    except Exception as e:
        print(f"Yahoo3連複パースエラー: {e}")


if __name__ == "__main__":
    test_local_parsing()
