import streamlit as st
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="接続診断")
st.title("🕵️‍♀️ 接続診断モード")

# 接続を試みる
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    
    # SecretsからURLを取得して、直接スプレッドシートを開いてみる
    url = st.secrets["connections"]["gsheets"]["spreadsheet"]
    st.write("ターゲットURL:", url)
    
    # gspreadの機能を使って情報を取得
    sh = conn.client.open_by_url(url)
    st.success(f"✅ 成功！ スプレッドシート名: **{sh.title}**")
    
    st.write("---")
    st.write("🤖 ロボットが見えているシート一覧:")
    
    # 全シートの名前を表示
    worksheet_list = sh.worksheets()
    for ws in worksheet_list:
        st.info(f"📄 シート名: **{ws.title}** (ID: {ws.id})")

    st.warning("👆 コードの `SHEET_NAME` は、この「シート名」と完全に一致していますか？")

except Exception as e:
    st.error("❌ 接続エラーが発生しました")
    st.code(e)
    st.write("考えられる原因：")
    st.write("1. SecretsのJSON貼り付けミス")
    st.write("2. スプレッドシートの「共有」にロボットのメアドが入っていない")
    st.write("3. Google Drive API / Sheets API が無効")
