from bs4 import BeautifulSoup
import pandas as pd
import re
from datetime import datetime, date, timedelta


def _parse_date(date_str: str):
    """'2025.12.28' → date オブジェクト。失敗時は None。"""
    try:
        return datetime.strptime(date_str.strip(), "%Y.%m.%d").date()
    except Exception:
        return None


def _date_to_str(d) -> str:
    """date → '2025/12/28' 形式文字列。"""
    if d is None:
        return "-"
    return d.strftime("%Y/%m/%d")


def _to_race_sunday(d) -> date:
    """
    レース日付を「そのレース週の日曜日」に丸める。
    - 日曜: そのまま
    - 土曜: 翌日（日曜）  ← 土曜開催はその週末の日曜とみなす
    - 月曜: 前日（日曜）  ← 振替休日の月曜開催は同じ週末とみなす
    - 火〜金: 次の日曜   ← 海外レース等の平日開催
    """
    wd = d.weekday()  # Mon=0 ... Sun=6
    if wd == 6:    # 日曜
        return d
    elif wd == 5:  # 土曜 → 翌日の日曜
        return d + timedelta(days=1)
    elif wd == 0:  # 月曜（振替休日開催）→ 前日の日曜
        return d - timedelta(days=1)
    else:          # 火〜金（海外等）→ 次の日曜
        return d + timedelta(days=6 - wd)


def _calc_interval(prev_date, next_date) -> str:
    """
    2つのdateオブジェクトから「中n週」を計算する。
    prev_date < next_date の想定。
    両日付を「レース週の日曜日」に丸めてから週差を計算する。
    失敗 or いずれかが None の場合は '-' を返す。
    """
    if prev_date is None or next_date is None:
        return "-"
    try:
        sun1 = _to_race_sunday(prev_date)
        sun2 = _to_race_sunday(next_date)
        weeks = (sun2 - sun1).days // 7 - 1
        if weeks < 0:
            weeks = 0
        return f"中{weeks}週"
    except Exception:
        return "-"


def _parse_past_cell(cell) -> dict:
    """
    <td class="Past"> ひとつ分のデータを辞書で返す。
    データ欠損の場合は全フィールドを "-" にした辞書を返す。
    """
    empty = {
        "date_obj": None,
        "date": "-",
        "venue": "-",
        "race_name": "-",
        "course": "-",
        "distance": "-",
        "track": "-",
        "head_count": "-",
        "umaban": "-",
        "popular": "-",
        "time": "-",
        "agari_3f": "-",
        "rank": "-",
        "jockey_name": "-",
        "jockey_weight": "-",
        "corner": "-",
        "diff": "-",
        "horse_weight": "-",
        "is_kyuyo": False,
        "kyuyo_text": "-",
    }

    classes = cell.get("class") or []

    # Premium未ログイン or 該当レースなし
    if "Past5_Sample" in classes:
        return empty

    # --- Rest クラス: 休養セル ---
    if "Rest" in classes:
        # Data01 が複数存在する: 例「5ヵ月半休養」「鉄砲 [0.0.0.3]」「2走目 [0.0.0.2]」
        data01_texts = [d.get_text(strip=True) for d in cell.find_all(class_="Data01")]
        kyuyo_text = "/".join(data01_texts) if data01_texts else "-"
        result = dict(empty)
        result["is_kyuyo"] = True
        result["kyuyo_text"] = kyuyo_text
        return result

    if "Past" not in classes:
        return empty

    data_item = cell.find(class_="Data_Item")
    if not data_item:
        return empty

    # --- Data01: 日付・競馬場名・着順 ---
    data01 = data_item.find(class_="Data01")
    if not data01:
        return empty

    data01_text = data01.get_text(" ", strip=True)

    # 休養チェック（念のため Past セル内でも）
    if "休養" in data01_text:
        result = dict(empty)
        result["is_kyuyo"] = True
        result["kyuyo_text"] = data01_text
        return result

    # 日付・競馬場を span テキストから取得
    span_texts = [s.get_text(strip=True) for s in data01.find_all("span") if "Num" not in (s.get("class") or [])]
    venue_str = span_texts[0] if span_texts else ""
    # "2025.12.28 中山" → split by whitespace
    venue_parts = venue_str.split()
    date_obj = None
    venue = "-"
    if len(venue_parts) >= 2:
        date_obj = _parse_date(venue_parts[0])
        venue = venue_parts[1]
    elif len(venue_parts) == 1:
        date_obj = _parse_date(venue_parts[0])

    # 着順: Num span
    num_span = data01.find(class_="Num")
    rank_raw = num_span.get_text(strip=True) if num_span else "-"
    if rank_raw.lstrip("-").isdigit():
        rank = rank_raw + "着"
    else:
        rank = rank_raw if rank_raw else "-"

    # --- Data02: レース名 ---
    data02 = data_item.find(class_="Data02")
    race_name = "-"
    if data02:
        a_tag = data02.find("a")
        if a_tag:
            # アンカーのテキストからspanを除いた部分（グレード表記を除外）
            for sp in a_tag.find_all("span"):
                sp.decompose()
            race_name = a_tag.get_text(strip=True) or "-"

    # --- Data05: コース・距離・馬場・走破タイム ---
    data05 = data_item.find(class_="Data05")
    course = "-"
    distance = "-"
    track = "-"
    time = "-"
    if data05:
        # strongタグが馬場
        strong = data05.find("strong")
        track = strong.get_text(strip=True) if strong else "-"
        text05 = data05.get_text(" ", strip=True)
        # コース先頭文字（芝 or ダ）
        m_course = re.match(r"^([芝ダ障])", text05)
        if m_course:
            course = m_course.group(1)
            # 距離: コース文字の直後に続く 数字 + 任意の(外)/(内) など
            m_dist = re.match(r"^[芝ダ障](\d+(?:\([^)]*\))?)", text05)
            if m_dist:
                distance = m_dist.group(1)
        # 走破タイム: N:NN.N 形式
        m_time = re.search(r"(\d+:\d+\.\d+)", text05)
        if m_time:
            time = m_time.group(1)

    # --- Data03: 頭数・馬番・単勝人気・騎手名・斤量 ---
    data03 = data_item.find(class_="Data03")
    head_count = "-"
    umaban = "-"
    popular = "-"
    jockey_name = "-"
    jockey_weight = "-"
    if data03:
        text03 = data03.get_text(strip=True)
        m_hc = re.search(r"(\d+)頭", text03)
        if m_hc:
            head_count = m_hc.group(1) + "頭"
        m_ub = re.search(r"(\d+)番", text03)
        if m_ub:
            umaban = m_ub.group(1) + "番"
        m_pop = re.search(r"(\d+)人", text03)
        if m_pop:
            popular = m_pop.group(1)
        m_jw = re.search(r"(\d+\.\d+)\s*$", text03)
        if m_jw:
            jockey_weight = m_jw.group(1)
            # 斤量より前のトークンから騎手名を抽出
            # 「16頭 13番 9人 川田将雅」→ 末尾トークンが数字+頭/番/人でなければ騎手名
            before_weight = text03[:m_jw.start()].split()
            if before_weight:
                candidate = before_weight[-1]
                if not re.match(r"^\d+[頭番人]$", candidate):
                    jockey_name = candidate

    # --- Data06: 4角通過順・上がり3F・場体重 ---
    data06 = data_item.find(class_="Data06")
    corner = "-"
    agari_3f = "-"
    horse_weight = "-"
    if data06:
        text06 = data06.get_text(" ", strip=True)
        # 4角通過順: N-N-N-N 形式
        m_corner = re.search(r"(\d+(?:-\d+)+)", text06)
        if m_corner:
            corner = m_corner.group(1)
        # 上がり3F: 最初のカッコ内の数値
        m_agari = re.search(r"\(([0-9.]+)\)", text06)
        if m_agari:
            agari_3f = m_agari.group(1)
            if float(agari_3f) == 0.0:
                agari_3f = "-"
        # 場体重: 末尾の NNN(±N) または NNN(N) 形式
        m_hw = re.search(r"(\d{3,4}\([+-]?\d+\))\s*$", text06)
        if m_hw:
            horse_weight = m_hw.group(1)

    # --- Data07: 着差（カッコ内の数字）---
    # <a>タグが存在しテキストが空でない場合のみ着差を取得する
    # （海外レース等で1着馬名が空欄の場合は "-" とする）
    data07 = data_item.find(class_="Data07")
    diff = "-"
    if data07:
        a_tag = data07.find("a")
        if a_tag and a_tag.get_text(strip=True):
            text07 = data07.get_text(strip=True)
            m_diff = re.search(r"\(([+-]?\d+\.\d+)\)\s*$", text07)
            if m_diff:
                diff_val = m_diff.group(1)
                if float(diff_val) == 0.0 and corner == "-":
                    diff = "-"
                else:
                    diff = diff_val + "秒"

    return {
        "date_obj": date_obj,
        "date": _date_to_str(date_obj),
        "venue": venue,
        "race_name": race_name,
        "course": course,
        "distance": distance,
        "track": track,
        "head_count": head_count,
        "umaban": umaban,
        "popular": popular,
        "time": time,
        "agari_3f": agari_3f,
        "rank": rank,
        "jockey_name": jockey_name,
        "jockey_weight": jockey_weight,
        "corner": corner,
        "diff": diff,
        "horse_weight": horse_weight,
        "is_kyuyo": False,
        "kyuyo_text": "-",
    }


def _build_past_columns(parsed: dict, prefix: str, interval: str) -> dict:
    """パース済み辞書からCSVカラム辞書を組み立てる。"""
    if parsed["is_kyuyo"]:
        return {
            f"{prefix}日付": "-",
            f"{prefix}(前走間隔)": parsed["kyuyo_text"],
            f"{prefix}競馬場名": "-",
            f"{prefix}レース名": "-",
            f"{prefix}コース(芝/ダート)": "-",
            f"{prefix}距離": "-",
            f"{prefix}馬場": "-",
            f"{prefix}頭数": "-",
            f"{prefix}馬番": "-",
            f"{prefix}単勝人気": "-",
            f"{prefix}走破タイム": "-",
            f"{prefix}上がり3F": "-",
            f"{prefix}着順": "-",
            f"{prefix}騎手名": "-",
            f"{prefix}斤量": "-",
            f"{prefix}4角通過順": "-",
            f"{prefix}着差(秒)": "-",
            f"{prefix}場体重": "-",
        }
    return {
        f"{prefix}日付": parsed["date"],
        f"{prefix}(前走間隔)": interval,
        f"{prefix}競馬場名": parsed["venue"],
        f"{prefix}レース名": parsed["race_name"],
        f"{prefix}コース(芝/ダート)": parsed["course"],
        f"{prefix}距離": parsed["distance"],
        f"{prefix}馬場": parsed["track"],
        f"{prefix}頭数": parsed.get("head_count", "-"),
        f"{prefix}馬番": parsed.get("umaban", "-"),
        f"{prefix}単勝人気": parsed.get("popular", "-"),
        f"{prefix}走破タイム": parsed.get("time", "-"),
        f"{prefix}上がり3F": parsed.get("agari_3f", "-"),
        f"{prefix}着順": parsed["rank"],
        f"{prefix}騎手名": parsed["jockey_name"],
        f"{prefix}斤量": parsed["jockey_weight"],
        f"{prefix}4角通過順": parsed["corner"],
        f"{prefix}着差(秒)": parsed["diff"],
        f"{prefix}場体重": parsed["horse_weight"],
    }


def parse_past_race(html_content: str) -> pd.DataFrame:
    """
    馬柱データ (5走) ページの HTML を解析して DataFrame を返す。
    取得ページ: /race/shutuba_past_9.html?race_id={race_id}&rf=shutuba_submenu
    """
    soup = BeautifulSoup(html_content, "html.parser")
    horse_rows = soup.find_all("tr", class_="HorseList")

    # カラム定義（サンプルCSVの列順に準拠）
    prefixes = ["前走", "2走", "3走", "4走", "5走"]
    base_cols = ["枠", "馬番", "馬名", "今走(前走間隔)", "父名", "母父名", "脚質", "斤量"]
    past_sub = ["日付", "(前走間隔)", "競馬場名", "レース名", "コース(芝/ダート)",
                "距離", "馬場", "頭数", "馬番", "単勝人気", "走破タイム", "上がり3F",
                "着順", "騎手名", "斤量", "4角通過順", "着差(秒)", "場体重"]
    all_cols = base_cols.copy()
    for p in prefixes:
        for s in past_sub:
            all_cols.append(f"{p}{s}")

    records = []

    for tr in horse_rows:
        try:
            # --- 枠 ---
            waku_td = tr.find("td", class_=re.compile(r"^Waku\d+$"))
            waku = waku_td.get_text(strip=True) if waku_td else "-"

            # --- 馬番 ---
            umaban_td = tr.find("td", class_="Waku")
            umaban = umaban_td.get_text(strip=True) if umaban_td else "-"

            # 枠・馬番が両方なければ全項目ハイフン
            if waku == "-" and umaban == "-":
                row = {col: "-" for col in all_cols}
                records.append(row)
                continue

            # --- 馬名 (Horse02 の anchor テキスト) ---
            horse_info = tr.find("td", id="Horse_Info_Data")
            bamei = "-"
            if horse_info:
                horse02 = horse_info.find(class_="Horse02")
                if horse02:
                    a = horse02.find("a")
                    bamei = a.get_text(strip=True) if a else horse02.get_text(strip=True)

            # --- 今走(前走間隔): Horse06 fc から "中n週" を抽出 ---
            imahashiri = "-"
            if horse_info:
                horse06 = horse_info.find(class_="Horse06")
                if horse06:
                    text06 = horse06.get_text(strip=True)
                    m = re.search(r"中\d+週", text06)
                    imahashiri = m.group(0) if m else "-"

            # --- 父名: Horse01 テキスト ---
            chichi = "-"
            if horse_info:
                horse01 = horse_info.find(class_="Horse01")
                if horse01:
                    chichi = horse01.get_text(strip=True) or "-"

            # --- 母父名: Horse04 テキスト（カッコ除去）---
            haha_chichi = "-"
            if horse_info:
                horse04 = horse_info.find(class_="Horse04")
                if horse04:
                    raw = horse04.get_text(strip=True)
                    haha_chichi = re.sub(r"[()（）]", "", raw).strip() or "-"

            # --- 脚質: Horse06 > span.kyakusitu ---
            KYAKUSITU_MAP = {"大": "逃げ", "先": "先行", "差": "差し", "追": "追込"}
            kyakusitu = "-"
            if horse_info:
                horse06_ks = horse_info.find(class_="Horse06")
                if horse06_ks:
                    ks = horse06_ks.find(class_="kyakusitu")
                    if ks:
                        code = ks.get_text(strip=True)
                        kyakusitu = KYAKUSITU_MAP.get(code, "-")

            # --- 斤量: Jockey 内の最後の span ---
            jockey_td = tr.find("td", class_="Jockey")
            kinryo = "-"
            if jockey_td:
                spans = jockey_td.find_all("span")
                # 末尾のspanが斤量
                for sp in reversed(spans):
                    txt = sp.get_text(strip=True)
                    if re.match(r"^\d+\.\d+$", txt):
                        kinryo = txt
                        break

            # --- Past/Rest セルを順番通りに取得（5走分の出力 + 間隔計算用に6つ読む）---
            # ※ 休養は class="Rest" で表現されるため Past と Rest を両方取得する
            past_cells = tr.find_all(
                "td",
                class_=lambda c: c is not None and (
                    any(x in c for x in ["Past", "Rest"])
                ),
            )
            # ただし Past5_Sample 等ログイン不要ページのダミーセルは除外
            past_cells = [c for c in past_cells
                          if "Past5_Sample" not in (c.get("class") or [])]
            # 最大6走分のデータを解析（6走目の日付は5走(前走間隔)の計算に使う）
            n_read = min(len(past_cells), 6)
            parsed_list = []
            for i in range(n_read):
                parsed_list.append(_parse_past_cell(past_cells[i]))
            empty_cell = {
                "date_obj": None, "date": "-", "venue": "-", "race_name": "-",
                "course": "-", "distance": "-", "track": "-",
                "head_count": "-", "umaban": "-", "popular": "-", "time": "-", "agari_3f": "-",
                "rank": "-", "jockey_name": "-", "jockey_weight": "-", "corner": "-", "diff": "-",
                "horse_weight": "-", "is_kyuyo": False, "kyuyo_text": "-",
            }
            while len(parsed_list) < 6:
                parsed_list.append(empty_cell)

            # --- 前走間隔の計算（出力は前走〜5走の5件分） ---
            # n走(前走間隔): (n+1)走日付 → n走日付 の差（n+1走=parsed_list[n]、n走=parsed_list[n-1]）
            # 前走(前走間隔): parsed_list[1].date_obj → parsed_list[0].date_obj
            intervals = []
            for i in range(5):
                if parsed_list[i]["is_kyuyo"]:
                    # 休養の場合は間隔計算せず、後で kyuyo_text を使う
                    intervals.append(None)
                else:
                    # i+1番目のセル（次に古い走）の日付が起点
                    next_parsed = parsed_list[i + 1]
                    intervals.append(_calc_interval(next_parsed["date_obj"], parsed_list[i]["date_obj"]))

            # --- レコード組み立て ---
            row = {
                "枠": waku,
                "馬番": umaban,
                "馬名": bamei,
                "今走(前走間隔)": imahashiri,
                "父名": chichi,
                "母父名": haha_chichi,
                "脚質": kyakusitu,
                "斤量": kinryo,
            }
            for i, prefix in enumerate(prefixes):
                interval = intervals[i] if intervals[i] is not None else parsed_list[i]["kyuyo_text"]
                row.update(_build_past_columns(parsed_list[i], prefix, interval))

            records.append(row)

        except Exception:
            continue

    df = pd.DataFrame(records, columns=all_cols)
    return df
