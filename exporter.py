import io
import json
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

    if config.GOOGLE_SERVICE_ACCOUNT_JSON and config.GOOGLE_DRIVE_FOLDER_ID:
        _upload_to_drive(file_path, file_name, folder_name)


def _get_drive_service():
    from googleapiclient.discovery import build
    from google.oauth2 import service_account

    creds_info = json.loads(config.GOOGLE_SERVICE_ACCOUNT_JSON)
    creds = service_account.Credentials.from_service_account_info(
        creds_info,
        scopes=["https://www.googleapis.com/auth/drive"]
    )
    return build("drive", "v3", credentials=creds)


def _get_or_create_folder(service, folder_name: str, parent_id: str) -> str:
    safe_name = folder_name.replace("'", "\\'")
    query = (
        f"name='{safe_name}' and mimeType='application/vnd.google-apps.folder' "
        f"and '{parent_id}' in parents and trashed=false"
    )
    results = service.files().list(q=query, fields="files(id)").execute()
    files = results.get("files", [])
    if files:
        return files[0]["id"]

    metadata = {
        "name": folder_name,
        "mimeType": "application/vnd.google-apps.folder",
        "parents": [parent_id],
    }
    folder = service.files().create(body=metadata, fields="id").execute()
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
        metadata = {"name": file_name, "parents": [subfolder_id]}
        service.files().create(body=metadata, media_body=media).execute()
        logging.info(f"Google Driveへのアップロード完了: {file_name}")
    except Exception as e:
        logging.error(f"Google Driveへのアップロードに失敗しました ({file_name}): {e}")
