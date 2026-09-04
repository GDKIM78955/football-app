import streamlit as st
import pandas as pd

# 1. 페이지 기본 설정
st.set_page_config(
    page_title="축구 이적시장 12대 가중치 분석 & FotMob 프로젝션 Pro",
    page_icon="⚽",
    layout="wide"
)

# 구글 시트 및 상수 설정
GOOGLE_SHEET_WEBAPP_URL = "https://script.google.com/macros/s/AKfycbwUX4diDBw2jD8WufrSa_0PejibYm7tIfyf1ia7O-QTfj1Ae6SQb3bZZ9pmNvDUAT6C/exec"
SPREADSHEET_ID = "16CeAQp1-xqc-mhtvlP0vLlQu5k1pg8DW5A-m29WCFdw"

# 구글 시트 데이터 로드 함수
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
        if not df.empty:
            return df
    except Exception:
        pass
    return pd.DataFrame()

# 데이터 로드
history_df = fetch_sheet_history()
validation_df = fetch_validation_data()

# 메인 타이틀
st.title("⚽ 프로페셔널 축구 이적시장 12대 가중치 분석 & 스카우팅 데이터룸")

# 6개 탭 구조 정의
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "💰 적정 이적료 평가", 
    "📱 FotMob 시즌 성적 & 이적 예측 (13대 풀 스탯)",
    "🔍 과거 유사 이적 사례 비교 (Comps TOP 5 & 10)",
    "🎯 이적 첫 시즌 실제 성적 입력 & 모델 검증",
    "👥 신규 이적생 vs 과거 유사 선수 다각도 벤치마크",
    "🏆 이적시장 구단/리그별 종합 결산 & 데이터룸"
])

# ----------------- 탭 1: 적정 이적료 평가 -----------------
with tab1:
    st.subheader("💰 적정 이적료 평가")
    st.write("이곳에 첫 번째 기능을 차근차근 구축할 예정입니다.")

# ----------------- 탭 2: FotMob 시즌 성적 -----------------
with tab2:
    st.subheader("📱 FotMob 시즌 성적 & 이적 예측 (13대 풀 스탯)")
    st.write("이곳에 두 번째 기능을 구축할 예정입니다.")

# ----------------- 탭 3: 과거 유사 이적 사례 비교 -----------------
with tab3:
    st.subheader("🔍 과거 유사 이적 사례 비교 (Comps TOP 5 & 10)")
    st.write("이곳에 세 번째 기능을 구축할 예정입니다.")

# ----------------- 탭 4: 이적 첫 시즌 실제 성적 검증 -----------------
with tab4:
    st.subheader("🎯 이적 첫 시즌 실제 성적 입력 & 모델 검증")
    st.write("이곳에 네 번째 기능을 구축할 예정입니다.")

# ----------------- 탭 5: 신규 vs 과거 벤치마크 -----------------
with tab5:
    st.subheader("👥 신규 이적생 vs 과거 유사 선수 다각도 벤치마크")
    st.write("이곳에 다섯 번째 기능을 구축할 예정입니다.")

# ----------------- 탭 6: 구단/리그별 종합 결산 -----------------
with tab6:
    st.subheader("🏆 이적시장 구단/리그별 종합 결산 & 데이터룸")
    st.write("이곳에 여섯 번째 기능을 구축할 예정입니다.")
