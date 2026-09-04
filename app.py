import streamlit as st
import pandas as pd
import requests

st.set_page_config(
    page_title="축구 이적시장 분석 시스템",
    page_icon="⚽",
    layout="wide"
)

GOOGLE_SHEET_WEBAPP_URL = "https://script.google.com/macros/s/AKfycbwUX4diDBw2jD8WufrSa_0PejibYm7tIfyf1ia7O-QTfj1Ae6SQb3bZZ9pmNvDUAT6C/exec"
SPREADSHEET_ID = "16CeAQp1-xqc-mhtvlP0vLlQu5k1pg8DW5A-m29WCFdw"

@st.cache_data(ttl=0)
def load_data():
    try:
        url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv&gid=0"
        df = pd.read_csv(url)
        if not df.empty: return df
    except: pass
    return pd.DataFrame()

history_df = load_data()

# 세션 상태 초기화 (처음부터 다시 시작하는 클린 키)
if "edit_mode" not in st.session_state: st.session_state["edit_mode"] = False
if "target_row" not in st.session_state: st.session_state["target_row"] = None
if "form_vals" not in st.session_state:
    st.session_state["form_vals"] = {"name": "", "nat": "", "age": 28, "tm": 4500, "fee": 0}

st.title("⚽ 프로페셔널 축구 이적시장 분석 시스템 (Clean Build)")

from tabs import tab1_eval, tab2_fotmob, tab3_comps, tab4_validation, tab5_benchmark, tab6_analytics

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "💰 적정 이적료 평가", "📱 FotMob 프로젝션", "🔍 유사 사례 비교",
    "🎯 모델 사후 검증", "👥 벤치마크", "🏆 종합 결산"
])

with tab1: tab1_eval.render(history_df, GOOGLE_SHEET_WEBAPP_URL)
with tab2: tab2_fotmob.render(GOOGLE_SHEET_WEBAPP_URL)
with tab3: tab3_comps.render(history_df)
with tab4: tab4_validation.render(validation_df := pd.DataFrame(), GOOGLE_SHEET_WEBAPP_URL)
with tab5: tab5_benchmark.render(history_df)
with tab6: tab6_analytics.render(history_df, GOOGLE_SHEET_WEBAPP_URL)
