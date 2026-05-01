import io
import os
import logging
import pandas as pd

import config


def save_to_csv(df: pd.DataFrame, race_id: str, race_name: str, file_suffix: str):
    """
    抽出したDataFrameを指定フォーマットでCSVに出力し、Google Driveにもアップロードする。
    保存先: output/{race_id}_{race_name}/{race_id}_{race_name}_{file_suffix}.csv
    """
    invalid_chars = r'<>:"/\|?*'
    for char in invalid_chars:
        race_name = race_name.replace(char, ' ')
    race_name = race_name.strip()

    folder_name = f"{race_id}_{race_name}"
    folder_path = os.path.join(config.OUTPUT_DIR, folder_name)
    os.makedirs(folder_path, exist_ok=True)

    file_name = f"{race_id}_{race_name}_{file_suffix}.csv"
    file_path = os.path.join(folder_path, file_name)

    try:
        df.to_csv(file_path, index=False, header=True, encoding='utf-8-sig')
        logging.info(f"CSV出力を完了しました: {file_path}")
    except Exception as e:
        logging.error(f"CSV出力中にエラーが発生しました ({file_path}): {e}")
        return

    drive_ready = (
        config.GOOGLE_OAUTH_CLIENT_ID
        and config.GOOGLE_OAUTH_CLIENT_SECRET
        and config.GOOGLE_OAUTH_REFRESH_TOKEN
        and config.GOOGLE_DRIVE_FOLDER_ID
    )
    if drive_ready:
        _upload_to_drive(file_path, file_name, folder_name)


def _get_drive_service():
    from googleapiclient.discovery import build
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request

    creds = Credentials(
        token=None,
        refresh_token=config.GOOGLE_OAUTH_REFRESH_TOKEN,
        client_id=config.GOOGLE_OAUTH_CLIENT_ID,
        client_secret=config.GOOGLE_OAUTH_CLIENT_SECRET,
        token_uri="https://oauth2.googleapis.com/token",
        scopes=["https://www.googleapis.com/auth/drive"],
    )
    creds.refresh(Request())
    return build("drive", "v3", credentials=creds)


def _get_or_create_folder(service, folder_name: str, parent_id: str) -> str:
    # race_id（アンダースコア前の部分）で前方一致検索
    race_id = folder_name.split("_")[0]
    safe_race_id = race_id.replace("'", "\\'")

    query = (
        f"name contains '{safe_race_id}' and mimeType='application/vnd.google-apps.folder' "
        f"and '{parent_id}' in parents and trashed=false"
    )
    results = service.files().list(q=query, fields="files(id, name)").execute()
    files = results.get("files", [])

    # race_idで始まるフォルダが存在すればそれを返す
    for f in files:
        if f["name"].startswith(race_id):
            logging.info(f"既存フォルダを使用します: {f['name']} (id={f['id']})")
            return f["id"]

    # 存在しなければ新規作成
    metadata = {
        "name": folder_name,
        "mimeType": "application/vnd.google-apps.folder",
        "parents": [parent_id],
    }
    folder = service.files().create(body=metadata, fields="id").execute()
    logging.info(f"新規フォルダを作成しました: {folder_name}")
    return folder["id"]


def _upload_to_drive(file_path: str, file_name: str, subfolder_name: str):
    from googleapiclient.http import MediaIoBaseUpload

    try:
        service = _get_drive_service()
        subfolder_id = _get_or_create_folder(
            service, subfolder_name, config.GOOGLE_DRIVE_FOLDER_ID
        )
        with open(file_path, "rb") as f:
            content = f.read()
        media = MediaIoBaseUpload(io.BytesIO(content), mimetype="text/csv")

        # 同名ファイルが既に存在するか確認
        safe_name = file_name.replace("'", "\\'")
        query = (
            f"name='{safe_name}' and '{subfolder_id}' in parents and trashed=false"
        )
        results = service.files().list(q=query, fields="files(id, name)").execute()
        existing_files = results.get("files", [])

        if existing_files:
            # 既存ファイルを上書き更新
            existing_file_id = existing_files[0]["id"]
            service.files().update(
                fileId=existing_file_id,
                media_body=media,
            ).execute()
            logging.info(f"Google Driveの既存ファイルを更新しました: {file_name}")
        else:
            # 新規作成
            metadata = {"name": file_name, "parents": [subfolder_id]}
            service.files().create(body=metadata, media_body=media).execute()
            logging.info(f"Google Driveへのアップロード完了: {file_name}")

    except Exception as e:
        logging.error(f"Google Driveへのアップロードに失敗しました ({file_name}): {e}")


def check_race_exists_on_drive(race_id: str) -> str:
    """
    Google Drive上にrace_idで始まるフォルダが存在するか確認し、
    存在すればレース名を返す。存在しなければ空文字を返す。
    """
    drive_ready = (
        config.GOOGLE_OAUTH_CLIENT_ID
        and config.GOOGLE_OAUTH_CLIENT_SECRET
        and config.GOOGLE_OAUTH_REFRESH_TOKEN
        and config.GOOGLE_DRIVE_FOLDER_ID
    )
    if not drive_ready:
        return ""

    try:
        service = _get_drive_service()
        safe_race_id = race_id.replace("'", "\\'")
        query = (
            f"name contains '{safe_race_id}' and "
            f"mimeType='application/vnd.google-apps.folder' and "
            f"'{config.GOOGLE_DRIVE_FOLDER_ID}' in parents and trashed=false"
        )
        results = service.files().list(q=query, fields="files(id, name)").execute()
        files = results.get("files", [])
        for f in files:
            if f["name"].startswith(race_id + "_"):
                # フォルダ名 "202605020211_フローラS" からレース名部分を返す
                return f["name"][len(race_id) + 1:]
        return ""
    except Exception as e:
        logging.warning(f"Google Driveのフォルダ確認に失敗しました: {e}")
        return ""

