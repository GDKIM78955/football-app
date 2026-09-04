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

history_df = fetch_sheet_history()
validation_df = fetch_validation_data()

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

# ================= TAB 1: 적정 이적료 평가 =================
with tab1:
    st.subheader("💰 프로페셔널 적정 이적료 평가 시스템")
    st.markdown("선수의 기본 프로필과 계약 정보를 입력하여 12대 가중치 기반 적정 이적료를 산출합니다.")

    trade_type_choice = st.radio(
        "거래 유형 구분", 
        ["🔵 영입 (IN)", "🔴 방출 / 판매 (OUT)"], 
        index=0, 
        horizontal=True,
        key="main_trade_type"
    )
    is_out_trade = "방출" in trade_type_choice

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("##### 👤 선수 기본 정보")
        player_name = st.text_input("선수 이름", placeholder="예: 해리 케인", key="main_p_name")
        player_nat = st.text_input("국적", placeholder="예: 잉글랜드", key="main_p_nat")
        player_age = st.number_input("만 나이", min_value=15, max_value=45, value=25, key="main_p_age")
        
        main_position = st.selectbox(
            "주 포지션",
            [
                "스트라이커 / 센터포워드 (ST/CF, +2%)",
                "윙어 / 공격형 미드필더 (WG/CAM, +1%)",
                "중앙 / 수비형 미드필더 (CM/CDM, 기준)",
                "풀백 / 윙백 (RB/LB/WB, -1%)",
                "센터백 (CB, -1%)",
                "골키퍼 (GK, -3%)"
            ],
            index=0,
            key="main_p_pos"
        )

    with col2:
        st.markdown("##### 🏢 소속 및 시장가치 정보")
        
        league_options = [
            "잉글랜드 프리미어리그 (EPL 1부)",
            "스페인 라리가 (La Liga 1부)",
            "독일 분데스리가 (Bundesliga 1부)",
            "이탈리아 세리에 A (Serie A 1부)",
            "프랑스 리그 1 (Ligue 1 1부)",
            "기타 리그"
        ]
        selling_league = st.selectbox("원소속 리그 (보내는 리그)", league_options, key="main_selling_league")
        
        in_from_team = st.text_input("원소속팀명 (보내는 팀)", placeholder="예: 토트넘 홋스퍼", key="main_from_team")
        in_to_team = st.text_input("이적팀명 (영입 구단)", placeholder="예: 바이에른 뮌헨", key="main_to_team")
        
        tm_market_value = st.number_input(
            "Transfermarkt 시장가치 (만 유로, €)", 
            min_value=0, 
            value=5000, 
            step=100,
            key="main_tm_val",
            help="단위: 만 유로 (예: 5000 입력 시 5,000만 유로)"
        )

    st.markdown("---")
    
    if st.button("📊 기본 데이터 확인하기", type="primary", key="main_check_btn"):
        st.success(f"입력 완료! [{player_name} / 만 {player_age}세 / {main_position.split(' ')[0]} / TM 시장가: €{tm_market_value:,}만]")

# ================= TAB 2: FotMob 시즌 성적 =================
with tab2:
    st.subheader("📱 FotMob 시즌 성적 & 이적 예측 (13대 풀 스탯)")
    st.write("준비 중입니다.")

# ================= TAB 3: 과거 유사 이적 비교 =================
with tab3:
    st.subheader("🔍 과거 유사 이적 사례 비교 (Comps TOP 5 & 10)")
    st.write("준비 중입니다.")

# ================= TAB 4: 이적 첫 시즌 검증 =================
with tab4:
    st.subheader("🎯 이적 첫 시즌 실제 성적 입력 & 모델 검증")
    st.write("준비 중입니다.")

# ================= TAB 5: 신규 vs 과거 벤치마크 =================
with tab5:
    st.subheader("👥 신규 이적생 vs 과거 유사 선수 다각도 벤치마크")
    st.write("준비 중입니다.")

# ================= TAB 6: 구단/리그별 종합 결산 =================
with tab6:
    st.subheader("🏆 이적시장 구단/리그별 종합 결산 & 데이터룸")
    st.write("준비 중입니다.")
