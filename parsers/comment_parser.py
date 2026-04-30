from bs4 import BeautifulSoup
import pandas as pd
import re

def parse_comment(html_content: str) -> pd.DataFrame:
    """
    厩舎（庁舎）コメントHTMLから指定の項目を抽出する。
    取得項目: 枠、馬番、馬名、コメント、評価
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    table = soup.find('table', class_=re.compile(r'Stable_Comment|Comment_Table'))
    
    if not table:
        return pd.DataFrame()
        
    data = []
    
    tbody = table.find('tbody')
    trs = tbody.find_all('tr') if tbody else table.find_all('tr')
    
    current_horse = {"waku": "", "umaban": "", "bamei": ""}
    
    for tr in trs:
        if not tr.find('td'):
            continue
            
        tds = tr.find_all('td')
        
        try:
            # 枠
            waku_td = tr.find('td', class_=re.compile(r'Waku\d|Waku'))
            if waku_td:
                current_horse["waku"] = waku_td.text.strip()
                
            # 馬番
            if len(tds) >= 2 and tds[1].text.strip().isdigit():
                current_horse["umaban"] = tds[1].text.strip()
            umaban_td_cls = tr.find('td', class_=re.compile(r'^Umaban\d*$')) # Wakuなど別のクラスに混ざっているケースを除去しUmabanで統一的に探す
            if umaban_td_cls:
                current_horse["umaban"] = umaban_td_cls.text.strip()
                
            # 馬名
            bamei_td = tr.find('td', class_='HorseName') or tr.find('td', class_='Horse_Name')
            if bamei_td:
                current_horse["bamei"] = bamei_td.text.strip()
                
            # コメント（改行コードを削除・置換する）
            comment_td = tr.find('td', class_='txt_l') or tr.find('td', class_=re.compile(r'StableComment|Comment'))
            comment_val = ""
            if comment_td:
                p_tag = comment_td.find('p')
                # ユーザー要件: コメント内の改行を半角スペースに置換
                if p_tag:
                    texts = [text for text in p_tag.stripped_strings]
                    comment_val = " ".join(texts)
                else:
                    texts = [text for text in comment_td.stripped_strings]
                    comment_val = " ".join(texts)
            
            # 評価のセル（画像クラスから独自の記号へ置換）
            eval_td = tr.find('td', class_=re.compile(r'Eval|Hyoka'))
            eval_val = ""
            if eval_td:
                # まずテキストがあればそれを採用
                eval_val = eval_td.text.strip()
                # テキストが無く、画像がある場合クラス名から記号を判定
                if not eval_val:
                    span = eval_td.find('span', class_=re.compile(r'Icon_Mark_\d+'))
                    if span:
                        cls_list = span.get('class', [])
                        if 'Icon_Mark_01' in cls_list:
                            eval_val = '◎'
                        elif 'Icon_Mark_02' in cls_list:
                            eval_val = '〇'
                        elif 'Icon_Mark_03' in cls_list:
                            eval_val = '△'
                            
            # ユーザー要件: 空コメント行が発生していた問題の修正。
            # 馬情報が取れた時点でデータ行を追加する（コメント・評価が空でも出力する）
            # 新しい馬の行であることの判定として、枠や馬名が取得できたタイミングで必ず追加する。
            if current_horse["waku"] and current_horse["bamei"]:
                # ただし、同じ馬の行を複数回追加しないようにする判定を入れる（通常1行1頭）
                data.append([
                    current_horse["waku"], 
                    current_horse["umaban"], 
                    current_horse["bamei"], 
                    comment_val, 
                    eval_val
                ])
                # 重複登録防止のためクリア（次の馬行までは保持させない方針に変更）
                current_horse = {"waku": "", "umaban": "", "bamei": ""}
                
        except Exception:
            pass

    columns = ['枠', '馬番', '馬名', 'コメント', '評価']
    df = pd.DataFrame(data, columns=columns)
    
    df = df.replace('---', '').replace('--', '')
    
    return df
