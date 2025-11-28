import streamlit as st
import pandas as pd
import time
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# --- 設定 ---
ALERT_MINUTES = 5 
STORES = ["渋谷店", "新宿店", "池袋店"]

# --- パスワード認証 ---
def check_password():
    if "password_correct" not in st.session_state:
        st.session_state.password_correct = False
    if st.session_state.password_correct:
        return True
    
    # ローカル開発時などのエラー回避
    if "PASSWORD" not in st.secrets:
        return True 

    st.text_input("パスワード", type="password", key="password_input", on_change=password_entered)
    return False

def password_entered():
    if st.session_state["password_input"] == st.secrets["PASSWORD"]:
        st.session_state.password_correct = True
        del st.session_state["password_input"]
    else:
        st.error("パスワードが違います")

if not check_password():
    st.stop()

# --- アプリ本体 ---
st.set_page_config(page_title="クラウド受付", layout="centered")
st.markdown("""<style>div.stButton > button { width: 100%; height: 3em; font-weight: bold; }</style>""", unsafe_allow_html=True)

# === データベース接続 ===
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    try:
        # シート名ではなく「0番目（一番左）」を指定して読み込む（名前間違い防止）
        df = conn.read(worksheet=0)
        
        # 必要な列がなければ作る（空シート対策）
        required_cols = ["店舗名", "受付番号", "受付時間", "ステータス"]
        for col in required_cols:
            if col not in df.columns:
                df[col] = ""
        # 空欄を埋めてエラー防止
        return df.fillna("")
    except Exception:
        # 読み込み失敗時（初回など）は空のデータを作る
        return pd.DataFrame(columns=["店舗名", "受付番号", "受付時間", "ステータス"])

# 店舗選択
current_store = st.sidebar.selectbox("🏠 店舗を選択", STORES)
st.title(f"📱 {current_store} 受付")

# 更新ボタン（キャッシュクリア付き）
if st.button("データ更新 🔄"):
    st.cache_data.clear()
    st.rerun()

df = load_data()
df_store = df[df["店舗名"] == current_store]

tab1, tab2 = st.tabs(["🖊️ 受付", "📋 一覧"])

# === タブ1：受付 ===
with tab1:
    waiting_count = len(df_store[df_store["ステータス"] == "準備中"])
    st.info(f"{current_store}の待ち： **{waiting_count}** 人")

    with st.form("entry_form", clear_on_submit=True):
        number = st.text_input("受付番号", placeholder="例：101")
        submitted = st.form_submit_button("登録する")

        if submitted and number:
            new_data = pd.DataFrame({
                "店舗名": [current_store],
                "受付番号": [number],
                "受付時間": [datetime.now().strftime("%H:%M:%S")],
                "ステータス": ["準備中"]
            })
            updated_df = pd.concat([df, new_data], ignore_index=True)
            
            # 書き込み：0番目のシートを指定
            conn.update(worksheet=0, data=updated_df)
            
            st.toast(f"✅ {number}番 を登録しました！", icon="🎉")
            time.sleep(1)
            st.rerun()

# === タブ2：一覧 ===
with tab2:
    pending_df = df_store[df_store["ステータス"] == "準備中"]

    if pending_df.empty:
        st.success("待機列はありません 🎉")
    else:
        now = datetime.now()
        for index, row in pending_df.iterrows():
            original_index = index
            reg_time_str = str(row['受付時間'])
            
            # 時間計算
            try:
                reg_time = datetime.strptime(reg_time_str, "%H:%M:%S")
                reg_time = reg_time.replace(year=now.year, month=now.month, day=now.day)
                diff_minutes = (now - reg_time).total_seconds() / 60
            except:
                diff_minutes = 0

            # 表示切り替え
            if diff_minutes >= ALERT_MINUTES:
                container = st.error()
                icon = "🔥"
            else:
                container = st.container(border=True)
                icon = "📦"

            with container:
                c1, c2 = st.columns([2, 1])
                with c1:
                    st.markdown(f"### {icon} **{row['受付番号']}**")
                    st.caption(f"受付: {reg_time_str}")
                with c2:
                    st.write("") 
                    if st.button("完了", key=f"btn_{original_index}", type="primary"):
                        df.at[original_index, "ステータス"] = "完了"
                        # 完了状態を書き込み
                        conn.update(worksheet=0, data=df)
                        
                        st.toast(f"👋 {row['受付番号']}番、完了！")
                        time.sleep(0.5)
                        st.rerun()

