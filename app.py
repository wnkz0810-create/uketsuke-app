import streamlit as st
import pandas as pd
import json
import time
from datetime import datetime
import gspread
from google.oauth2 import service_account

# --- 設定 ---
ALERT_MINUTES = 15
STORES = ["東金町", "新宿店", "池袋店"]
AUTO_REFRESH_INTERVAL = 15  # 自動更新の間隔（秒）。短すぎるとAPI制限にかかるので注意！

# --- 1. パスワード認証 ---
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

# --- 2. データベース接続（直接接続方式） ---
@st.cache_resource
def get_worksheet():
    """スプレッドシートに接続してシートオブジェクトを返す"""
    try:
        # Secretsから情報を取得
        json_str = st.secrets["connections"]["gsheets"]["service_account"]
        url = st.secrets["connections"]["gsheets"]["spreadsheet"]
        
        # 認証
        creds_dict = json.loads(json_str)
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = service_account.Credentials.from_service_account_info(creds_dict, scopes=scopes)
        client = gspread.authorize(creds)
        
        # シートを開く（0番目のシート）
        sh = client.open_by_url(url)
        return sh.get_worksheet(0)
    except Exception as e:
        st.error(f"接続エラー: {e}")
        return None

def load_data():
    """シートから全データを読み込んでDataFrameにする"""
    sheet = get_worksheet()
    if sheet is None:
        return pd.DataFrame()

    # 全データを取得（辞書形式のリスト）
    data = sheet.get_all_records()
    
    # データがない場合は空のDFを返す
    if not data:
        return pd.DataFrame(columns=["店舗名", "受付番号", "受付時間", "ステータス"])
    
    df = pd.DataFrame(data)
    
    # 列不足の補完
    required_cols = ["店舗名", "受付番号", "受付時間", "ステータス"]
    for col in required_cols:
        if col not in df.columns:
            df[col] = ""
            
    # 全て文字列として扱う（エラー防止）
    return df.astype(str)

def save_data(df):
    """DataFrameを丸ごとシートに上書き保存する"""
    sheet = get_worksheet()
    if sheet is None:
        return

    # データフレームをリスト形式に変換（ヘッダー付き）
    data_to_write = [df.columns.values.tolist()] + df.values.tolist()
    
    # シートをクリアして書き込み
    sheet.clear()
    sheet.update(data_to_write)

# --- 3. アプリ画面 ---
st.set_page_config(page_title="クラウド受付", layout="centered")
st.markdown("""<style>div.stButton > button { width: 100%; height: 3em; font-weight: bold; }</style>""", unsafe_allow_html=True)

# サイドバー：店舗選択
current_store = st.sidebar.selectbox("🏠 店舗を選択", STORES)
st.title(f"🍕{current_store} 受付")

# 更新ボタン
if st.button("データ更新 🔄"):
    st.cache_data.clear()
    st.rerun()

# データ読み込み
df = load_data()

# もし読み込み失敗などでDFが空なら空枠を作成
if df.empty:
    df = pd.DataFrame(columns=["店舗名", "受付番号", "受付時間", "ステータス"])

# 現在の店舗でフィルタリング
df_store = df[df["店舗名"] == current_store]

tab1, tab2 = st.tabs(["🖊️ 受付", "📋 一覧"])

# === タブ1：受付画面 ===
with tab1:
    waiting_count = len(df_store[df_store["ステータス"] == "準備中"])
    st.info(f"{current_store}の待ち： **{waiting_count}** 人")

    with st.form("entry_form", clear_on_submit=True):
        number = st.text_input("受付番号", placeholder="例：101")
        submitted = st.form_submit_button("登録する")

        if submitted and number:
            # 新しい行を作成
            new_row = pd.DataFrame({
                "店舗名": [current_store],
                "受付番号": [number],
                "受付時間": [datetime.now().strftime("%H:%M:%S")],
                "ステータス": ["準備中"]
            })
            
            # 結合
            updated_df = pd.concat([df, new_row], ignore_index=True)
            
            # 保存
            save_data(updated_df)
            
            st.toast(f"✅ {number}番 を登録しました！", icon="🎉")
            time.sleep(1)
            st.rerun()

# === タブ2：一覧画面 ===
with tab2:
    pending_df = df_store[df_store["ステータス"] == "準備中"]

    if pending_df.empty:
        st.success("待機列はありません 🎉")
    else:
        now = datetime.now()
      # リスト表示
        for index, row in pending_df.iterrows():
            # 全体データ(df)内でのインデックスを保持
            original_index = index 

            # 時間計算
            reg_time_str = str(row['受付時間'])
            try:
                reg_time = datetime.strptime(reg_time_str, "%H:%M:%S")
                reg_time = reg_time.replace(year=now.year, month=now.month, day=now.day)
                diff_minutes = (now - reg_time).total_seconds() / 60
            except:
                diff_minutes = 0

            # --- 修正箇所：ここから ---
            # デザインの分岐（赤枠か、普通の枠か）
            if diff_minutes >= ALERT_MINUTES:
                # 時間経過している場合：赤枠（エラー表示）を使う
                # メッセージとして経過時間を表示します
                box = st.error(f"🔥 {int(diff_minutes)}分経過しています")
                icon = "🔥"
            else:
                # 通常の場合：普通の枠線を使う
                box = st.container(border=True)
                icon = "📦"

            # 決まった枠（box）の中に書き込む
            with box:
                c1, c2 = st.columns([2, 1])
                with c1:
                    st.markdown(f"### {icon} **{row['受付番号']}**")
                    st.caption(f"受付: {reg_time_str}")
                with c2:
                    st.write("") 
                    if st.button("完了", key=f"btn_{original_index}", type="primary"):
                        # ステータスを変更
                        df_current = load_data() # 最新データを再取得
                        df_current.at[original_index, "ステータス"] = "完了"
                        
                        # 保存
                        save_data(df_current)
                        
                        st.toast(f"👋 {row['受付番号']}番、完了！")
                        time.sleep(0.5)
                        st.rerun()
            # --- 修正箇所：ここまで ---




