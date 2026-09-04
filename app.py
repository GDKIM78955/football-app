import streamlit as st
import pandas as pd
import requests
import json
from datetime import datetime

# 1. 페이지 기본 설정 (가장 먼저 실행되어야 함)
st.set_page_config(
    page_title="축구 이적시장 12대 가중치 분석 & FotMob 프로젝션 Pro",
    page_icon="⚽",
    layout="wide"
)

# 2. 구글 시트 연동 URL 및 ID
GOOGLE_SHEET_WEBAPP_URL = "https://script.google.com/macros/s/AKfycbwUX4diDBw2jD8WufrSa_0PejibYm7tIfyf1ia7O-QTfj1Ae6SQb3bZZ9pmNvDUAT6C/exec"
SPREADSHEET_ID = "16CeAQp1-xqc-mhtvlP0vLlQu5k1pg8DW5A-m29WCFdw"

# 🌟 1번 탭(메인 히스토리) 데이터 로드 함수 (캐시 즉시 갱신)
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

# 🌟 2번 탭(검증데이터) 데이터 로드 함수
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

# 데이터프레임 미리 로드
history_df = fetch_sheet_history()
validation_df = fetch_validation_data()

# 3. 🌟 Session State 초기화 (버그 원천 차단용 안전 키 설정)
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

# FotMob 기본 스탯 초기값 설정
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

# 앱 타이틀
st.title("⚽ 프로페셔널 축구 이적시장 12대 가중치 분석 & 스카우팅 데이터룸")

# 4. 6개 탭 파일 임포트 및 연결
# (tabs 폴더 내의 파일들을 안전하게 임포트합니다)
try:
    from tabs import tab1_eval, tab2_fotmob, tab3_comps, tab4_validation, tab5_benchmark, tab6_analytics
except ImportError as e:
    st.error(f"⚠️ 탭 모듈을 불러오는 중 오류가 발생했습니다. `tabs/` 폴더 내에 파일들이 모두 있는지 확인해주세요. 상세 오류: {e}")
    st.stop()

# 5. 상단 탭 구성
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "💰 적정 이적료 평가", 
    "📱 FotMob 시즌 성적 & 이적 예측 (13대 풀 스탯)",
    "🔍 과거 유사 이적 사례 비교 (Comps TOP 5 & 10)",
    "🎯 이적 첫 시즌 실제 성적 입력 & 모델 검증",
    "👥 신규 이적생 vs 과거 유사 선수 다각도 벤치마크",
    "🏆 이적시장 구단/리그별 종합 결산 & 데이터룸"
])

with tab1:
    tab1_eval.render(history_df, GOOGLE_SHEET_WEBAPP_URL)

with tab2:
    tab2_fotmob.render(GOOGLE_SHEET_WEBAPP_URL)

with tab3:
    tab3_comps.render(history_df)

with tab4:
    tab4_validation.render(validation_df, GOOGLE_SHEET_WEBAPP_URL)

with tab5:
    tab5_benchmark.render(history_df)

with tab6:
    tab6_analytics.render(history_df, GOOGLE_SHEET_WEBAPP_URL)
