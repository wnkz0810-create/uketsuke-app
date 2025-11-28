import streamlit as st
from streamlit_gsheets import GSheetsConnection

st.title("💥 書き込みテスト")

# 接続
conn = st.connection("gsheets", type=GSheetsConnection)
url = st.secrets["connections"]["gsheets"]["spreadsheet"]

try:
    # Streamlitの便利機能を使わず、直接「生」の命令で書き込んでみる
    # A10セルに「テスト」と書き込む実験
    st.write("書き込みテスト中...")
    
    # シートを開く
    book = conn.client.open_by_url(url)
    sheet = book.get_worksheet(0) # 0番目のシート
    
    # 書き込み実行
    sheet.update_acell('E1', 'Test') 
    
    st.success("✅ 書き込み成功！権限は正常です。")
    st.info("原因はコード側の『データフレームの形式』かもしれません。")

except Exception as e:
    st.error("❌ 書き込み失敗！本当のエラー原因はこちら：")
    st.code(e) # ここに出る英語のエラーが重要です
