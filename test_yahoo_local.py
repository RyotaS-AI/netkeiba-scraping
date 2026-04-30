import os
import glob
from parsers.yahoo_denma_parser import parse_yahoo_denma
from parsers.yahoo_odds_parser import (
    parse_tansho, parse_fukusho, parse_wakuren,
    parse_umatan, parse_umaren, parse_wide, parse_sanrenpuku
)

def test_yahoo_parsers_with_live_html():
    docs_dir = 'docs'
    print("=== Yahoo出馬表テスト ===")
    denma_file = os.path.join(docs_dir, 'v_test_yahoo_denma.html')
    if os.path.exists(denma_file):
        with open(denma_file, 'r', encoding='utf-8') as f:
            html = f.read()
        df = parse_yahoo_denma(html)
        print("出馬表データ (先頭5行):")
        print(df.head())
        print(f"Total rows: {len(df)}")
    
    html_tfw = ""
    tfw_file = os.path.join(docs_dir, 'v_test_yahoo_tfw.html')
    if os.path.exists(tfw_file):
        with open(tfw_file, 'r', encoding='utf-8') as f:
            html_tfw = f.read()
            
    print("\n=== 単勝テスト ===")
    if html_tfw:
        df = parse_tansho(html_tfw)
        print(df.head())
        print(f"Total rows: {len(df)}")
        
    print("\n=== 複勝テスト ===")
    if html_tfw:
        df = parse_fukusho(html_tfw)
        print(df.head())
        print(f"Total rows: {len(df)}")
        
    print("\n=== 枠連テスト ===")
    if html_tfw:
        df = parse_wakuren(html_tfw)
        print(df.head())
        print(f"Total rows: {len(df)}")
        
    print("\n=== 馬単テスト ===")
    file = os.path.join(docs_dir, 'v_test_yahoo_ut.html')
    if os.path.exists(file):
        with open(file, 'r', encoding='utf-8') as f:
            html = f.read()
        df = parse_umatan(html)
        print(df.head())
        print(f"Total rows: {len(df)}")
        
    print("\n=== 馬連テスト ===")
    file = os.path.join(docs_dir, 'v_test_yahoo_ur.html')
    if os.path.exists(file):
        with open(file, 'r', encoding='utf-8') as f:
            html = f.read()
        df = parse_umaren(html)
        print(df.head())
        print(f"Total rows: {len(df)}")
        
    print("\n=== ワイドテスト ===")
    file = os.path.join(docs_dir, 'v_test_yahoo_wide.html')
    if os.path.exists(file):
        with open(file, 'r', encoding='utf-8') as f:
            html = f.read()
        df = parse_wide(html)
        print(df.head())
        print(f"Total rows: {len(df)}")

    print("\n=== 3連複テスト ===")
    file = os.path.join(docs_dir, 'v_test_yahoo_sf.html')
    if os.path.exists(file):
        with open(file, 'r', encoding='utf-8') as f:
            html = f.read()
        df = parse_sanrenpuku(html)
        print(df.head())
        print(f"Total rows: {len(df)}")

if __name__ == '__main__':
    test_yahoo_parsers_with_live_html()
