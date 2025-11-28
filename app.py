import streamlit as st
import json
import pandas as pd
from google.oauth2 import service_account
import gspread

st.set_page_config(page_title="強制接続テスト")
st.title("🛡️ 最終手段：直接接続テスト")

try:
    # 1. Secretsからデータを取得（ここが読み込めればSecretsは合っている）
    if "connections" not in st.secrets or "gsheets" not in st.secrets["connections"]:
        st.error("❌ Secretsの設定が見つかりません。")
        st.stop()

    json_str = st.secrets["connections"]["gsheets"]["service_account"]
    url = st.secrets["connections"]["gsheets"]["spreadsheet"]

    # 2. JSONを辞書データに変換
    creds_dict = json.loads(json_str)

    # 3. 直接認証を行う（Streamlitの機能を介さない）
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = service_account.Credentials.from_service_account_info(creds_dict, scopes=scopes)
    client = gspread.authorize(creds)

    # 4. シートを開いてみる
    sh = client.open_by_url(url)
    worksheet = sh.get_worksheet(0) # 0番目（一番左）のシート
    
    st.success(f"✅ つながりました！ シート名: **{sh.title}**")
    st.balloons()
    
    # 5. 書き込みテスト
    st.write("書き込みテスト中...")
    worksheet.update_acell('E1', 'ConnectionOK')
    st.success("✅ 書き込みも成功しました！")
    
    st.info("このコードで成功したら、この方式を使った「完成版」をお渡しします。")

except Exception as e:
    st.error("❌ エラーが発生しました")
    st.code(e)
    st.write("エラー内容を教えてください！")
