import streamlit as st
import json

st.set_page_config(page_title="Secrets診断")
st.title("🔍 Secrets 診断ツール")

st.write("あなたのSecretsの設定状況をチェックします...")
st.write("---")

# 1. 見出しのチェック
if "connections" in st.secrets and "gsheets" in st.secrets["connections"]:
    st.success("✅ `[connections.gsheets]` セクションは見つかりました！")
    
    # 中身のチェック
    section = st.secrets["connections"]["gsheets"]
    
    # spreadsheetはあるか？
    if "spreadsheet" in section:
        st.success(f"✅ spreadsheet設定あり: `{section['spreadsheet']}`")
    else:
        st.error("❌ `spreadsheet = ...` の行が見つかりません。")

    # service_accountはあるか？
    if "service_account" in section:
        st.success("✅ `service_account` 設定あり")
        
        # JSONとして正しいか？
        try:
            sa_data = json.loads(section["service_account"], strict=False)
            email = sa_data.get("client_email", "不明")
            st.success(f"✅ JSONの読み込み成功！")
            st.info(f"🤖 ロボットのメール: `{email}`")
            st.write("ここまでOKなら、接続エラーの原因はコード側ではなくGoogle側のAPI設定です。")
        except json.JSONDecodeError as e:
            st.error("❌ `service_account` の中身が正しいJSONではありません。")
            st.error(f"エラー内容: {e}")
            st.warning("コピペする時に `{` や `}` が欠けていませんか？")
    else:
        st.error("❌ `service_account = ...` の行が見つかりません（または場所がズレています）。")
        st.warning("必ず `[connections.gsheets]` の行よりも **下** に書いてください。")

else:
    st.error("❌ `[connections.gsheets]` という見出しが見つかりません！")
    st.warning("Secretsの一番上に `[connections.gsheets]` と書いてあるか確認してください。")

st.write("---")
st.write("👇 **現在のSecretsのキー一覧（中身は隠しています）**")
st.write(st.secrets)
