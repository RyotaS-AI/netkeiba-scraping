import re
import os
import glob
import config
from urllib.parse import urlparse, parse_qs

def extract_race_id(url: str) -> str:
    """
    URLからrace_idを抽出する
    netkeiba形式 (例: ...?race_id=202606020411) または
    Yahoo形式 (例: .../denma/2605010811) から取得可能
    """
    # 1. netkeiba形式のクエリパラメータから取得
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    if "race_id" in query:
        return query["race_id"][0]
    
    # 2. URLに直接含まれる netkeiba形式のパラメータを探す
    match = re.search(r'race_id=(\d+)', url)
    if match:
        return match.group(1)
        
    # 3. Yahoo形式のURLパスから取得 (例: /denma/2605010811)
    match = re.search(r'/(\d{10,12})(?:\?|$|/)', url)
    if match:
        return match.group(1)
        
    # 4. フォールバック: 文字列内の10〜12桁の数字
    match = re.search(r'(\d{10,12})', url)
    if match:
        return match.group(1)
        
    raise ValueError(f"URLからrace_idを取得できませんでした: {url}")

def format_race_id(race_id: str, to_yahoo: bool = False) -> str:
    """
    抽出したrace_idを指定モード向けにフォーマットする
    netkeiba用: 12桁 (先頭に20などを付加)
    Yahoo用: 10桁 (先頭の20を削る)
    """
    if to_yahoo:
        # Yahoo用: 12桁なら先頭の "20" を削る
        if len(race_id) == 12:
            return race_id[2:]
        return race_id
    else:
        # netkeiba用: 10桁なら先頭に "20" を付ける
        if len(race_id) == 10:
            return "20" + race_id
        return race_id

def get_shared_race_name(race_id_12: str, default_race_name: str) -> str:
    """
    指定した12桁のrace_idの出力フォルダが既に存在する場合、
    その既存フォルダからレース名を取得して統一する。
    存在しない場合は default_race_name を返す。
    """
    output_dir = getattr(config, 'OUTPUT_DIR', 'output')
    pattern = os.path.join(output_dir, f"{race_id_12}_*")
    existing_folders = glob.glob(pattern)
    for path in existing_folders:
        if os.path.isdir(path):
            folder_name = os.path.basename(path)
            prefix = f"{race_id_12}_"
            if folder_name.startswith(prefix):
                return folder_name[len(prefix):]
    return default_race_name
