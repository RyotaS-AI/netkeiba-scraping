from bs4 import BeautifulSoup
import pandas as pd
import re

def parse_shutuba(html_content: str) -> pd.DataFrame:
    """
    出馬表HTMLから指定の項目を抽出する。
    取得項目: 枠、馬番、馬名、性齢、斤量、騎手、庁舎、馬体重、オッズ、人気
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    table = soup.find('table', class_='Shutuba_Table')
    
    if not table:
        return pd.DataFrame()
        
    data = []
    
    rows = table.find_all('tr', class_='HorseList')
    for row in rows:
        cells = row.find_all('td')
        if not cells:
            continue
            
        # 「取消」や「除外」かどうかの判定
        is_canceled = False
        cancel_text = row.find(class_='Cancel_Txt')
        if cancel_text or '取消' in row.text or '除外' in row.text:
            is_canceled = True

        try:
            # 枠: 'Waku1', 'Waku2' などが存在するため正規表現で探索
            waku_td = row.find('td', class_=re.compile(r'^Waku\d*$'))
            waku = waku_td.text.strip() if waku_td else ""
            
            # 馬番: 'Umaban1', 'Umaban2' などのケース
            umaban_td = row.find('td', class_=re.compile(r'^Umaban\d*$'))
            umaban = umaban_td.text.strip() if umaban_td else ""
            
            # 馬名
            horse_name_el = row.find(class_='HorseInfo') or row.find(class_='HorseName')
            bamei = horse_name_el.text.strip() if horse_name_el else ""
            
            if is_canceled:
                data.append([waku, umaban, bamei, "", "", "", "", "", "", ""])
                continue
                
            # 性齢
            seirei_el = row.find(class_='Barei')
            seirei = seirei_el.text.strip() if seirei_el else ""
            
            # 斤量: td のクラス無し（Txt_Cのみだったり）の場合がある
            kinryo_td = row.find('td', class_='Jockey')
            kinryo = ""
            if kinryo_td:
                # 騎手要素の兄（前）の要素が斤量であることが多い
                prev_td = kinryo_td.find_previous_sibling('td')
                if prev_td and not prev_td.get('class') == ['Barei']: # 念のため
                    kinryo = prev_td.text.strip()
            # 正規表現で小数点(57.0等)のみのtdから取るアプローチ
            if not kinryo:
                for td in row.find_all('td', class_='Txt_C'):
                    if re.match(r'^\d{2}\.\d$', td.text.strip()):
                        kinryo = td.text.strip()
                        break
            
            # 騎手
            kishu = kinryo_td.text.strip() if kinryo_td else ""
            
            # 庁舎 (Trainer)
            trainer_el = row.find('td', class_='Trainer')
            chosha = trainer_el.text.strip().replace('\n', '') if trainer_el else ""
            chosha = re.sub(r'\s+', ' ', chosha).strip()
            
            # 馬体重
            weight_el = row.find('td', class_='Weight')
            bataiju = weight_el.text.strip() if weight_el else ""
            if bataiju in ['--', '---']:
                bataiju = ""
                
            # オッズ ('Txt_R' クラスなど)
            odds_tds = row.find_all('td', class_=re.compile(r'Txt_R|Popular'))
            odds = ""
            for td in odds_tds:
                txt = td.text.strip()
                if re.match(r'^\d+\.\d+$', txt): # 1.5 や 303.5 などの数値
                    odds = txt
                    break
            if not odds:
                odds_span = row.find('span', id=re.compile(r'^odds-'))
                odds = odds_span.text.strip() if odds_span else ""
            if odds in ['--', '---'] or not odds:
                odds = ""
                
            # 人気 ('Popular_Ninki' などのクラス)
            pop_td = row.find('td', class_=re.compile(r'Popular_Ninki')) or row.find('span', class_='OddsPeople')
            ninki = pop_td.text.strip() if pop_td else ""
            if not ninki:
                for td in odds_tds:
                    txt = td.text.strip()
                    if txt.isdigit(): # 人気は整数
                        ninki = txt
                        break
            if ninki in ['--', '---'] or not ninki:
                ninki = ""
            
            data.append([waku, umaban, bamei, seirei, kinryo, kishu, chosha, bataiju, odds, ninki])
            
        except Exception as e:
            data.append(["", "", "", "", "", "", "", "", "", ""])

    columns = ['枠', '馬番', '馬名', '性齢', '斤量', '騎手', '庁舎', '馬体重', 'オッズ', '人気']
    df = pd.DataFrame(data, columns=columns)
    
    df = df.replace('---', '').replace('--', '')
    
    return df
