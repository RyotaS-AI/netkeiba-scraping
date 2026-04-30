import requests
import time
import logging
import random

class NetkeibaScraper:
    def __init__(self, login_id: str = "", password: str = ""):
        self.session = requests.Session()
        # ユーザーエージェントと実ブラウザに近い各種ヘッダーを設定する
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1"
        })
        self.login_id = login_id
        self.password = password
        
        if self.login_id and self.password:
            self._login()

    def _login(self):
        """netkeibaへのログイン処理を行う"""
        login_url = "https://regist.netkeiba.com/account/?pid=login"
        payload = {
            "login_id": self.login_id,
            "pswd": self.password,
            "pid": "login",
            "action": "auth"
        }
        
        logging.info("netkeibaへログインを試みます...")
        try:
            # ログインページへPOST
            response = self.session.post(login_url, data=payload, timeout=15)
            response.raise_for_status()
            
            # クッキーがセットされていれば成功とみなす（簡単なチェック）
            if "netkeiba" in str(self.session.cookies) or "Y_uid" in str(self.session.cookies):
                logging.info("ログイン処理が完了しました。")
            else:
                logging.warning("ログインが成功していない可能性があります。設定を確認するか、非ログイン状態で続行します。")
                
            sleep_time = round(random.uniform(3.0, 5.0), 1)
            time.sleep(sleep_time) # ログイン時の負荷軽減
        except Exception as e:
            logging.error(f"ログイン処理中にエラーが発生しました: {e}")

    def get_html(self, url: str) -> str:
        """指定されたURLからHTMLを取得し、必ず5秒待機する"""
        logging.info(f"アクセス中: {url}")
        
        try:
            response = self.session.get(url, timeout=15)
            # 文字化け防止のため、レスポンスのエンコーディングを自動判別
            response.encoding = response.apparent_encoding
            html_text = response.text
        except Exception as e:
            logging.error(f"HTMLの取得に失敗しました ({url}): {e}")
            html_text = ""
            
        sleep_time = round(random.uniform(3.0, 5.0), 1)
        logging.info(f"アクセス完了（{sleep_time}秒間スリープします）")
        time.sleep(sleep_time) # 仕様: ページ遷移ごとに3〜5秒スリープ
        return html_text

