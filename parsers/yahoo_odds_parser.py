import re
import pandas as pd

def parse_tansho(html_content: str) -> pd.DataFrame:
    from bs4 import BeautifulSoup
    import re
    data = []
    soup = BeautifulSoup(html_content, 'html.parser')
    for table in soup.find_all('table'):
        # 単勝・複勝が含まれるテーブルのヘッダーをチェック
        th_texts = [th.text for th in table.find_all('th') if th.text]
        if any('単勝' in t for t in th_texts):
            for tr in table.find_all('tr'):
                # 枠、馬番、馬名、単勝、複勝列(下限-上限)が存在する。
                # tbody内のtrにはtdやthが混ざっているが、順番に取得
                cells = [c.get_text(separator=' ', strip=True) for c in tr.find_all(['th', 'td'])]
                # 最低限、馬番とオッズが入る列数があればOK（通常は5列）
                if len(cells) >= 4:
                    umaban = cells[1]
                    tansho = cells[3]
                    if re.match(r'^\d+$', umaban) and tansho and tansho != '---' and tansho != '****':
                        data.append([umaban, tansho])
            # テーブルは1つ見つかれば十分
            break
            
    return pd.DataFrame(data, columns=["馬番", "単勝オッズ"]) if data else pd.DataFrame()

def parse_fukusho(html_content: str) -> pd.DataFrame:
    from bs4 import BeautifulSoup
    import re
    data = []
    soup = BeautifulSoup(html_content, 'html.parser')
    for table in soup.find_all('table'):
        th_texts = [th.text for th in table.find_all('th') if th.text]
        if any('複勝' in t for t in th_texts):
            for tr in table.find_all('tr'):
                cells = [c.get_text(separator=' ', strip=True) for c in tr.find_all(['th', 'td'])]
                if len(cells) >= 5:
                    umaban = cells[1]
                    fukusho_raw = cells[4] # "4.6 - 7.4" など
                    if re.match(r'^\d+$', umaban):
                        m = re.match(r'^([\d\.]+)\s*-\s*([\d\.]+)$', fukusho_raw)
                        if m:
                            data.append([umaban, m.group(1), m.group(2)])
            break

    return pd.DataFrame(data, columns=["馬番", "複勝オッズ_下限", "複勝オッズ_上限"]) if data else pd.DataFrame()

def extract_matrix_odds(html_content: str, is_wide: bool = False, is_sanrenpuku: bool = False) -> list:
    """枠連、ワイド、馬単、3連複などのマトリックス型レイアウトのオッズを抽出する共通関数"""
    data = []
    tr_regex = r'<tr[^>]*>([\s\S]*?)</tr>'
    cell_regex = r'<(th|td)[^>]*>([\s\S]*?)</\1\s*>'
    
    current_headers = []
    
    for tr_match in re.finditer(tr_regex, html_content, re.IGNORECASE):
        tr_html = tr_match.group(1)
        cells = []
        for cell_match in re.finditer(cell_regex, tr_html, re.IGNORECASE):
            text = re.sub(r'<[^>]+>', '', cell_match.group(2)).strip()
            text = re.sub(r'[－—–]', '-', text)
            text = re.sub(r'\s+', '', text)
            cells.append(text)
            
        if not cells:
            continue
            
        is_header_row = True
        has_header_format = False
        
        for cell in cells:
            if cell != "":
                if is_sanrenpuku:
                    if re.match(r'^\d+-\d+$', cell):
                        has_header_format = True
                    else:
                        is_header_row = False
                        break
                else:
                    if re.match(r'^\d+$', cell):
                        has_header_format = True
                    else:
                        is_header_row = False
                        break
                        
        if is_header_row and has_header_format and len(cells) > 0:
            current_headers = [c for c in cells if c != ""]
            continue
            
        if len(current_headers) > 0 and len(cells) >= 2:
            for i in range(0, len(cells)-1, 2):
                col2 = cells[i]
                odds_raw = cells[i + 1]
                
                if not odds_raw:
                    continue
                    
                if is_wide:
                    odds_match = re.match(r'^([\d\.]+)-([\d\.]+)$', odds_raw)
                    if odds_match and re.match(r'^\d+$', col2):
                        header_index = i // 2
                        if header_index < len(current_headers):
                            col1 = current_headers[header_index]
                            data.append([col1, col2, odds_match.group(1), odds_match.group(2)])
                else:
                    odds_match = re.match(r'^([\d\.]+)$', odds_raw)
                    if odds_match and re.match(r'^\d+$', col2):
                        header_index = i // 2
                        if header_index < len(current_headers):
                            col1 = current_headers[header_index]
                            if is_sanrenpuku:
                                parts = col1.split('-')
                                if len(parts) == 2:
                                    data.append([parts[0], parts[1], col2, odds_match.group(1)])
                            else:
                                data.append([col1, col2, odds_match.group(1)])
                                
    return data

def parse_wakuren(html_content: str) -> pd.DataFrame:
    data = extract_matrix_odds(html_content)
    return pd.DataFrame(data, columns=["枠番1", "枠番2", "枠連オッズ"]) if data else pd.DataFrame()

def parse_umatan(html_content: str) -> pd.DataFrame:
    data = extract_matrix_odds(html_content)
    return pd.DataFrame(data, columns=["1着馬番", "2着馬番", "馬単オッズ"]) if data else pd.DataFrame()

def parse_wide(html_content: str) -> pd.DataFrame:
    data = extract_matrix_odds(html_content, is_wide=True)
    return pd.DataFrame(data, columns=["馬番1", "馬番2", "ワイドオッズ_下限", "ワイドオッズ_上限"]) if data else pd.DataFrame()

def parse_sanrenpuku(html_content: str) -> pd.DataFrame:
    data = extract_matrix_odds(html_content, is_sanrenpuku=True)
    return pd.DataFrame(data, columns=["馬番1", "馬番2", "馬番3", "3連複オッズ"]) if data else pd.DataFrame()

def parse_umaren(html_content: str) -> pd.DataFrame:
    data = []
    # 1. 各「縦の列」を形成している個別のテーブル(hr-tableLeftTop--oddsW)をすべて抽出
    table_regex = r'<table[^>]*class="[^"]*hr-tableLeftTop--oddsW[^"]*"[^>]*>([\s\S]*?)</table>'
    
    for table_match in re.finditer(table_regex, html_content, re.IGNORECASE):
        table_content = table_match.group(1)
        
        # 2. そのテーブルのヘッダーから「馬番1」を取得 (thead内の th)
        horse1_match = re.search(r'<th[^>]*scope="col"[^>]*>(\d+)</th>', table_content, re.IGNORECASE)
        if not horse1_match:
            continue
        horse1 = horse1_match.group(1)
        
        # 3. tbody内の各行（馬番2 と オッズ）を順番に処理
        row_regex = r'<tr[^>]*>([\s\S]*?)</tr>'
        for row_match in re.finditer(row_regex, table_content, re.IGNORECASE):
            row_content = row_match.group(1)
            
            horse2_match = re.search(r'<th[^>]*scope="row"[^>]*>(\d+)</th>', row_content, re.IGNORECASE)
            odds_match = re.search(r'<td[^>]*>([\s\S]*?)</td>', row_content, re.IGNORECASE)
            
            if horse2_match and odds_match:
                horse2 = horse2_match.group(1)
                odds_val = re.sub(r'<[^>]+>', '', odds_match.group(1))
                odds_val = re.sub(r'\s+', '', odds_val).strip()
                
                # オッズが存在し、「---」や「****」でない場合のみ追加
                if odds_val and odds_val not in ["---", "****", ""]:
                    data.append([horse1, horse2, odds_val])
                    
    return pd.DataFrame(data, columns=["馬番1", "馬番2", "馬連オッズ"]) if data else pd.DataFrame()
