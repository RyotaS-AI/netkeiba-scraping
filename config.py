import os
from dotenv import load_dotenv

# .env ファイルがあれば読み込む
load_dotenv()

NETKEIBA_LOGIN_ID = os.environ.get("NETKEIBA_LOGIN_ID", "")
NETKEIBA_PASSWORD = os.environ.get("NETKEIBA_PASSWORD", "")

OUTPUT_DIR = "output"

GOOGLE_OAUTH_CLIENT_ID = os.environ.get("GOOGLE_OAUTH_CLIENT_ID", "")
GOOGLE_OAUTH_CLIENT_SECRET = os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET", "")
GOOGLE_OAUTH_REFRESH_TOKEN = os.environ.get("GOOGLE_OAUTH_REFRESH_TOKEN", "")
GOOGLE_DRIVE_FOLDER_ID = os.environ.get("GOOGLE_DRIVE_FOLDER_ID", "")
