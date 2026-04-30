import os
from dotenv import load_dotenv

# .env ファイルがあれば読み込む
load_dotenv()

NETKEIBA_LOGIN_ID = os.environ.get("NETKEIBA_LOGIN_ID", "")
NETKEIBA_PASSWORD = os.environ.get("NETKEIBA_PASSWORD", "")

OUTPUT_DIR = "output"

GOOGLE_SERVICE_ACCOUNT_JSON = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "")
GOOGLE_DRIVE_FOLDER_ID = os.environ.get("GOOGLE_DRIVE_FOLDER_ID", "")
