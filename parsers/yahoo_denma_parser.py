import re
import pandas as pd
from bs4 import BeautifulSoup

def parse_yahoo_denma(html_content: str) -> pd.DataFrame:
    """
    Yahooスポーツナビ競馬の出馬表HTMLから指定の項目を抽出する。
    取得項目: 枠、馬番、馬名、性齢、斤量、騎手、馬体重、オッズ、人気
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    data = []
    
    trs = soup.find_all('tr')
    for tr in trs:
        cells = tr.find_all(['td', 'th'])
        if len(cells) < 3:
            continue
            
        tds = []
        for cell in cells:
            # <rt>タグ（ルビ）を除外
            for rt in cell.find_all('rt'):
                rt.decompose()
            # テキスト取得、改行やタブをスペースに置換して整形
            text = cell.get_text(separator=' ')
            text = re.sub(r'[\r\n\t]+', ' ', text)
            text = re.sub(r'\s{2,}', ' ', text).strip()
            tds.append(text)
            
        waku = ""
        umaban = ""
        waku_text = tds[0].strip()
        
        # 枠と馬番の判定
        if re.match(r'^[1-8]$', waku_text):
            waku = waku_text
            if len(tds) > 1 and re.match(r'^\d+$', tds[1].strip()):
                umaban = tds[1].strip()
        elif re.match(r'^[1-8]\s+\d+$', waku_text):
            parts = re.split(r'\s+', waku_text)
            waku = parts[0]
            umaban = parts[1]
        else:
            continue
            
        bamei = ""
        seirei = ""
        kinryo = ""
        kishu = ""
        bataiju = "計不"
        odds = ""
        ninki = ""
        
        for t in tds:
            # 馬名 (カタカナ2文字以上など)
            if not bamei:
                m = re.search(r'([\u30A0-\u30FF\[\]]{2,})', t)
                # 「降」などの例外文字が含まれる場合はマッチさせない
                if m and "降" not in t:
                    bamei = m.group(1).replace('[', '').replace(']', '')
                    
            # 性齢 (例: 牡4, 牝5, せん6, セ7)
            if not seirei:
                m = re.search(r'([牡牝セせん]+\d+)', t)
                if m and "降" not in t:
                    seirei = m.group(1)
                    
            # 斤量と騎手 (例: 57.0 武豊)
            if not kinryo:
                m = re.search(r'(\d{2}\.\d)', t)
                if m:
                    kinryo = m.group(1)
                    # 数字とドットを除去した残りを騎手名として扱う
                    j = re.sub(r'[\d\.]', '', t).strip()
                    if j:
                        kishu = j
                        
            # 馬体重
            if bataiju == "計不":
                m = re.search(r'(\d{3}\s*\([+-]?\d+\)|計不)', t)
                if m:
                    bataiju = m.group(1).replace(' ', '')
                    
            # オッズと人気 (例: 1 (1.5) または ** (---.-))
            m_odds = re.search(r'(\d+|\*\*)\s*\(\s*(\d+\.\d+|---\.-)\s*\)', t)
            if m_odds:
                ninki = m_odds.group(1)
                odds = m_odds.group(2)
                
        if bamei:
            data.append([waku, umaban, bamei, seirei, kinryo, kishu, bataiju, odds, ninki])
            
    columns = ["枠", "馬番", "馬名", "性齢", "斤量", "騎手", "馬体重", "単勝オッズ", "人気"]
    df = pd.DataFrame(data, columns=columns)
    
    # 欠損値の置換
    df = df.replace('---.-', '').replace('**', '').replace('計不', '')
    
    return df
