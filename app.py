import streamlit as st
import pandas as pd
import requests

# 1. 페이지 기본 설정
st.set_page_config(
    page_title="축구 이적시장 12대 가중치 분석 & FotMob 프로젝션 Pro",
    page_icon="⚽",
    layout="wide"
)

GOOGLE_SHEET_WEBAPP_URL = "https://script.google.com/macros/s/AKfycbwUX4diDBw2jD8WufrSa_0PejibYm7tIfyf1ia7O-QTfj1Ae6SQb3bZZ9pmNvDUAT6C/exec"
SPREADSHEET_ID = "16CeAQp1-xqc-mhtvlP0vLlQu5k1pg8DW5A-m29WCFdw"

# 데이터 로드 함수
@st.cache_data(ttl=0)
def fetch_sheet_history():
    try:
        csv_url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv&gid=0"
        df = pd.read_csv(csv_url)
        if not df.empty: return df
    except Exception: pass
    return pd.DataFrame()

@st.cache_data(ttl=0)
def fetch_validation_data():
    try:
        val_url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv&gid=15389686"
        df = pd.read_csv(val_url)
        if not df.empty and "선수명" in df.columns: return df
    except Exception: pass
    return pd.DataFrame()

history_df = fetch_sheet_history()
validation_df = fetch_validation_data()

# 공통 세션 상태 초기화
if "last_saved_msg" not in st.session_state: st.session_state["last_saved_msg"] = None
if "edit_row_index" not in st.session_state: st.session_state["edit_row_index"] = None
for k in ["input_name", "input_nat", "input_from_team", "input_to_team", "input_notes"]:
    if k not in st.session_state: st.session_state[k] = ""
if "input_age" not in st.session_state: st.session_state["input_age"] = 28
if "input_tm" not in st.session_state: st.session_state["input_tm"] = 4500
if "input_fee" not in st.session_state: st.session_state["input_fee"] = 0
if "input_wage" not in st.session_state: st.session_state["input_wage"] = 0.0

st.title("⚽ 프로페셔널 축구 이적시장 12대 가중치 분석 & 스카우팅 데이터룸")

if st.session_state["last_saved_msg"]:
    st.success(st.session_state["last_saved_msg"])
    st.session_state["last_saved_msg"] = None

# 모듈화된 탭 파일들 임포트
try:
    from tabs import tab1_eval, tab2_fotmob, tab3_comps, tab4_validation, tab5_benchmark, tab6_analytics
except ImportError as e:
    st.error(f"⚠️ 탭 모듈을 불러오는 중 오류 발생: {e}. `tabs/` 폴더 안의 파일들을 확인해주세요.")
    st.stop()

# 6개 탭 구성
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "💰 적정 이적료 평가", 
    "📱 FotMob 시즌 성적 & 이적 예측",
    "🔍 과거 유사 이적 사례 비교",
    "🎯 이적 첫 시즌 실제 성적 & 모델 검증",
    "👥 신규 이적생 vs 과거 선수 벤치마크",
    "🏆 이적시장 구단/리그별 종합 결산 & 데이터룸"
])

with tab1: tab1_eval.render(history_df, GOOGLE_SHEET_WEBAPP_URL)
with tab2: tab2_fotmob.render(GOOGLE_SHEET_WEBAPP_URL)
with tab3: tab3_comps.render(history_df)
with tab4: tab4_validation.render(validation_df, GOOGLE_SHEET_WEBAPP_URL)
with tab5: tab5_benchmark.render(history_df)
with tab6: tab6_analytics.render(history_df, GOOGLE_SHEET_WEBAPP_URL)
