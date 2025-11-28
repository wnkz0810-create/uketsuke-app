import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="キャッシュ削除＆再接続")
st.title("🧹 キャッシュお掃除モード")

if st.button("キャッシュをクリアして再接続する", type="primary"):
    # 1. 記憶（キャッシュ）を全消去
    st.cache_resource.clear()
    st.cache_data.clear()
    st.success("✨ キャッシュを削除しました！")
    
    # 2. 新しく接続しなおす
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        
        # 3. ちゃんとロボットとしてつながったか確認
        # (open_by_url はロボットにしかできない技です)
        url = st.secrets["connections"]["gsheets"]["spreadsheet"]
        conn.client.open_by_url(url)
        
        st.balloons()
        st.success("✅ 完璧です！ロボット認証に成功しました！")
        st.info("これで本番コードに戻しても動きます。")
        
    except AttributeError:
        st.error("❌ まだ「鍵なし（Public）」として認識されています...")
        st.write("対策：ブラウザのタブを閉じて、もう一度開き直してみてください。")
    except Exception as e:
        st.error(f"❌ 別のエラー：{e}")

st.write("👆 上のボタンを押して、風船が飛べば成功です！")
