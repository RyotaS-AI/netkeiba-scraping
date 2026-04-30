"""
Google Drive用のリフレッシュトークンを取得するスクリプト。
初回のみローカルで実行し、表示されたトークンをGitHub Secretsに登録する。

事前準備:
  pip install google-auth-oauthlib
  Google Cloud ConsoleでOAuth 2.0クライアントID（デスクトップアプリ）を作成し、
  credentials.jsonとしてこのファイルと同じフォルダに保存する。

実行:
  python get_refresh_token.py
"""

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/drive"]

flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
creds = flow.run_local_server(port=0)

print("\n===== GitHub Secretsに登録する値 =====")
print(f"GOOGLE_OAUTH_CLIENT_ID:     {creds.client_id}")
print(f"GOOGLE_OAUTH_CLIENT_SECRET: {creds.client_secret}")
print(f"GOOGLE_OAUTH_REFRESH_TOKEN: {creds.refresh_token}")
