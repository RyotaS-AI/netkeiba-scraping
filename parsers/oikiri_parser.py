from bs4 import BeautifulSoup
import pandas as pd
import re

def parse_oikiri(html_content: str, is_final: bool = False) -> pd.DataFrame:
    """
    追い切りHTMLから指定の項目を抽出する。
    取得項目: 枠、馬番、馬名、日付、コース、(馬場※最終のみ)、乗り役、調教タイム、調教タイムラップ、脚色、評価_コメント、評価_ランク、(コメント※最終のみ)
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    table = soup.find('table', class_=re.compile(r'OikiriTable|nk_tb_common'))
    
    if not table:
        return pd.DataFrame()
        
    data = []
    current_horse = {"waku": "", "umaban": "", "bamei": "", "header_comment": ""}
    
    trs = table.find_all('tr')
    
    for tr in trs:
        if not tr.find('td'):
            continue
            
        tds = tr.find_all('td')
        
        # 馬情報行かどうかの判定
        waku_td = tr.find('td', class_=re.compile(r'Waku\d|Waku'))
        horse_td = tr.find('td', class_=re.compile(r'Horse_Info|HorseName'))
        
        if waku_td or horse_td:
            if waku_td:
                current_horse["waku"] = waku_td.text.strip()
            
            # 馬番
            if len(tds) >= 2 and tds[1].text.strip().isdigit():
                current_horse["umaban"] = tds[1].text.strip()
            else:
                um_td = tr.find('td', class_='Umaban')
                if um_td:
                    current_horse["umaban"] = um_td.text.strip()
                
            if horse_td:
                name_el = horse_td.find('a')
                if name_el:
                    current_horse["bamei"] = name_el.text.strip()
                else:
                    txt = horse_td.text.strip()
                    txt = re.sub(r'前走.*', '', txt).strip()
                    txt = txt.split('\n')[0].strip()
                    current_horse["bamei"] = txt
                    
            comment_td = tr.find('td', class_=re.compile(r'TrainingReview_Cell|Comment|TrainingReview'))
            if comment_td:
                current_horse["header_comment"] = comment_td.text.strip()
            continue

        if '取消' in tr.text or '除外' in tr.text:
            if is_final:
                 row = [current_horse["waku"], current_horse["umaban"], current_horse["bamei"], 
                        "", "", "", "", "", "", "", "", "", ""]  # 13項目
            else:
                 row = [current_horse["waku"], current_horse["umaban"], current_horse["bamei"], 
                        "", "", "", "", "", "", "", ""]  # 11項目
            data.append(row)
            continue
            
        # 追い切り履歴行の判定
        date_td = tr.find('td', class_='Training_Day') or tr.find('td', class_='Date')
        
        if date_td:
            date_val = date_td.text.strip()
            
            course_val, baba_val, jockey_val = "", "", ""
            
            if len(tds) >= 4:
                course_val = tds[1].text.strip()
                course_val = re.sub(r'一番時計|.*時計.*', '', course_val).strip()
                baba_val = tds[2].text.strip()
                jockey_val = tds[3].text.strip()
            
            # タイムとラップ
            time_td = tr.find('td', class_=re.compile(r'TrainingTimeData|Time'))
            time_val = ""
            lap_val = ""
            if time_td:
                html_strings = list(time_td.stripped_strings)
                upper_parts = []  # タイム値のリスト（例:["54.9","39.3",...]）
                lower_parts = []  # ラップ値のリスト（例:["15.6","14.6",...]）
                
                pattern = r'([^\(\)\s]+)?(?:\(([^\(\)]+)\))?'
                
                for s in html_strings:
                    s = s.strip()
                    if not s:
                        continue
                    if not re.search(r'[0-9\-\(\)]+', s):
                        continue
                    
                    matches = re.findall(pattern, s)
                    for main_val, bracket_val in matches:
                        m_val = main_val.strip()
                        b_val = bracket_val.strip()
                        
                        if m_val:
                            upper_parts.append(m_val)
                        if b_val:
                            lower_parts.append(b_val)

                # --- タイムの結合 ---
                # 期待値: "-|54.9|39.3|24.7|12.0" (中間) / "-|54.9|39.3|24.7|12.0|" (最終・先頭 - の場合)
                time_val = "|".join([u for u in upper_parts if u])
                # 最終追い切りで先頭が "-" の場合、ラップの方がタイムより1つ多い → 末尾に"|"を追加
                if is_final and upper_parts and upper_parts[0] == "-" and len(upper_parts) <= len(lower_parts):
                    time_val += "|"
                     
                # --- ラップの結合 ---
                # 先頭に続く「-」の個数を数える（例: ["-", "-", "52.1", ...] → 2つの(-)を補完）
                leading_dash_count = 0
                for u in upper_parts:
                    if u == "-":
                        leading_dash_count += 1
                    else:
                        break
                
                if leading_dash_count > 0:
                    # 先頭の「-」に対応するラップが存在しないので「(-)」を補完
                    lap_parts = ["(-)"] * leading_dash_count + [f"({v})" for v in lower_parts]
                else:
                    lap_parts = [f"({v})" for v in lower_parts]
                
                if is_final:
                    # 最終追い切り: スペース区切り、(-)の後ろもスペース
                    lap_val = " ".join(lap_parts)
                else:
                    # 中間追い切り: スペースなし（詰める）
                    lap_val = "".join(lap_parts)

            # 脚色
            state_td = tr.find('td', class_='TrainingLoad') or tr.find('td', class_='State')
            state_val = state_td.text.strip() if state_td else ""
            
            # 評価コメント
            eval_com_td = tr.find('td', class_='Training_Critic') or tr.find('td', class_='Eval')
            eval_comment = eval_com_td.text.strip() if eval_com_td else ""
            
            # 評価ランク
            eval_rank_td = tr.find('td', class_=re.compile(r'Rank_[A-Z]'))
            eval_rank = eval_rank_td.text.strip() if eval_rank_td else ""
            
            if is_final:
                row = [
                    current_horse["waku"], current_horse["umaban"], current_horse["bamei"],
                    date_val, course_val, baba_val, jockey_val, time_val, lap_val, state_val, eval_comment, eval_rank,
                    current_horse["header_comment"]
                ]
            else:
                row = [
                    current_horse["waku"], current_horse["umaban"], current_horse["bamei"],
                    date_val, course_val, jockey_val, time_val, lap_val, state_val, eval_comment, eval_rank
                ]
                
            data.append(row)

    if is_final:
        columns = [
            '枠', '馬番', '馬名', '日付', 'コース', '馬場', '乗り役', '調教タイム', '調教タイムラップ', 
            '脚色', '評価_コメント', '評価_ランク', 'コメント'
        ]
    else:
        columns = [
            '枠', '馬番', '馬名', '日付', 'コース', '乗り役', '調教タイム', '調教タイムラップ', 
            '脚色', '評価_コメント', '評価_ランク'
        ]
        
    df = pd.DataFrame(data, columns=columns)
    df = df.replace('---', '').replace('--', '')
    
    return df
