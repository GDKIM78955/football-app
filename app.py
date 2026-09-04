import streamlit as st
import pandas as pd
import requests
import json

# 1. 페이지 기본 설정
st.set_page_config(
    page_title="프로페셔널 축구 이적시장 분석 시스템",
    page_icon="⚽",
    layout="wide"
)

GOOGLE_SHEET_WEBAPP_URL = "https://script.google.com/macros/s/AKfycbwUX4diDBw2jD8WufrSa_0PejibYm7tIfyf1ia7O-QTfj1Ae6SQb3bZZ9pmNvDUAT6C/exec"
SPREADSHEET_ID = "16CeAQp1-xqc-mhtvlP0vLlQu5k1pg8DW5A-m29WCFdw"

# 2. 구글 시트 데이터 로드 함수
@st.cache_data(ttl=0)
def fetch_sheet_history():
    try:
        csv_url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv&gid=0"
        df = pd.read_csv(csv_url)
        if not df.empty:
            return df
    except Exception:
        pass
    return pd.DataFrame()

@st.cache_data(ttl=0)
def fetch_validation_data():
    try:
        val_url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv&gid=15389686"
        df = pd.read_csv(val_url)
        if not df.empty and "선수명" in df.columns:
            return df
    except Exception:
        pass
    return pd.DataFrame()

history_df = fetch_sheet_history()
val_df = fetch_validation_data()

# 3. 전역 세션 스테이트 초기화
if "form_key_id" not in st.session_state:
    st.session_state["form_key_id"] = 0
if "stat_key_id" not in st.session_state:
    st.session_state["stat_key_id"] = 0
if "last_saved_msg" not in st.session_state:
    st.session_state["last_saved_msg"] = None
if "edit_row_index" not in st.session_state:
    st.session_state["edit_row_index"] = None
if "custom_proj_mins" not in st.session_state:
    st.session_state["custom_proj_mins"] = 3000

default_stats = {
    "f_mins": 90, "f_goals": 0, "f_xg": 0.0, "f_assists": 0, "f_xa": 0.0,
    "f_rating": 6.50, "f_matches": 1, "f_starts": 0, "f_shots": 0, "f_sot": 0,
    "f_chances": 0, "f_dribbles": 0, "f_touches_box": 0, "f_tackles": 0,
    "f_gk_saves": 0, "f_gk_conceded": 0, "f_gk_prevented": 0.0,
    "f_gk_cs": 0, "f_gk_errors": 0, "f_gk_claims": 0,
    "f_big_chances": 0, "f_pk_goals": 0, "f_pass_pct": 0.0, "f_duels_pct": 0.0, "f_aerial_pct": 0.0
}
for k, v in default_stats.items():
    if k not in st.session_state:
        st.session_state[k] = v

st.title("⚽ 프로페셔널 축구 이적시장 12대 가중치 분석 & 스카우팅 데이터룸")

# 4. 6개의 모듈화된 탭 생성
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "💰 적정 이적료 평가", 
    "📱 FotMob 시즌 성적 & 이적 예측",
    "🔍 과거 유사 이적 사례 비교",
    "🎯 이적 첫 시즌 실제 성적 & 사후 검증",
    "👥 다각도 벤치마크",
    "🏆 종합 결산 & 데이터룸"
])

# 5. 각 부품 파일 임포트 및 탭 연결
from tabs import tab1_eval, tab2_fotmob, tab3_comps, tab4_validation, tab5_benchmark, tab6_analytics

with tab1:
    tab1_eval.render(history_df, GOOGLE_SHEET_WEBAPP_URL)

with tab2:
    tab2_fotmob.render()

with tab3:
    tab3_comps.render(history_df)

with tab4:
    tab4_validation.render(val_df, GOOGLE_SHEET_WEBAPP_URL)

with tab5:
    tab5_benchmark.render(history_df)

with tab6:
    tab6_analytics.render(history_df, GOOGLE_SHEET_WEBAPP_URL)
