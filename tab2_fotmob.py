import streamlit as st
import pandas as pd
import numpy as np
import requests
import json
import plotly.graph_objects as go
from datetime import datetime

# 1. 페이지 기본 설정
st.set_page_config(
    page_title="축구 이적시장 12대 가중치 분석 & FotMob 프로젝션 Pro",
    page_icon="⚽",
    layout="wide"
)

GOOGLE_SHEET_WEBAPP_URL = "https://script.google.com/macros/s/AKfycbwUX4diDBw2jD8WufrSa_0PejibYm7tIfyf1ia7O-QTfj1Ae6SQb3bZZ9pmNvDUAT6C/exec"
SPREADSHEET_ID = "16CeAQp1-xqc-mhtvlP0vLlQu5k1pg8DW5A-m29WCFdw"

# 🌟 구글 시트 CSV Export 다이렉트 로드
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

history_df = fetch_sheet_history()

# 2번 탭(검증데이터) 데이터 로드용 함수
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

# 2. 가중치 딕셔너리
LEAGUE_WEIGHTS = {
    "잉글랜드 프리미어리그 (EPL 1부)": 1.00,
    "스페인 라리가 (La Liga 1부)": 0.92,
    "독일 분데스리가 (Bundesliga 1부)": 0.91,
    "이탈리아 세리에 A (Serie A 1부)": 0.90,
    "프랑스 리그 1 (Ligue 1 1부)": 0.88,
    "잉글랜드 챔피언십 (EFL 2부)": 0.80,
    "포르투갈 프리메이라리가 (1부)": 0.78,
    "네덜란드 에레디비시 (Eredivisie 1부)": 0.77,
    "벨기에 주필러 프로 리그 (1부)": 0.75,
    "브라질 세리에 A (Brasileirão 1부)": 0.68,
    "독일 2. 분데스리가 (2부)": 0.67,
    "스페인 라리가 2 (세군다 2부)": 0.66,
    "튀르키예 쉬페르리그 (1부)": 0.65,
    "이탈리아 세리에 B (2부)": 0.64,
    "미국 메이저리그사커 (MLS 1부)": 0.64,
    "멕시코 리가 MX (1부)": 0.63,
    "스위스 슈퍼리그 (1부)": 0.62,
    "오스트리아 분데스리가 (1부)": 0.62,
    "덴마크 수페르리가 (1부)": 0.61,
    "스코틀랜드 프리미어십 (1부)": 0.60,
    "아르헨티나 프리메라 디비시온 (1부)": 0.60,
    "폴란드 엑스트라클라사 (1부)": 0.55,
    "프랑스 리그 2 (2부)": 0.55,
    "그리스 슈퍼리그 (1부)": 0.54,
    "사우디 프로리그 (SPL 1부)": 0.52,
    "일본 J1리그 (1부)": 0.50,
    "대한민국 K리그1 (1부)": 0.48,
    "스웨덴 알스벤스칸 (1부)": 0.48,
    "노르웨이 엘리테세리엔 (1부)": 0.47,
    "일본 J2리그 (2부)": 0.35,
    "대한민국 K리그2 (2부)": 0.33,
    "기타 리그": 0.30
}

TRACKED_LEAGUE_NAMES = [
    "프리미어리그", "라리가", "분데스리가", "세리에 A", "리그 1",
    "에레디비시", "포르투갈", "벨기에", "튀르키예", "챔피언십"
]

CLUB_TIERS = {
    "Tier 1: 엘리트 메가클럽 (레알, 맨시티, 바이에른, PSG 등)": 1.05,
    "Tier 2: 빅클럽 (아스날, 리버풀, 첼시, 바르샤, 유벤투스 등)": 1.02,
    "Tier 3: 중상위권 클럽 (토트넘, AT마드리드, 도르트문트 등)": 1.00,
    "Tier 4: 중하위권 클럽 (EPL 중하위, 타 빅리그 중위권)": 0.98,
    "Tier 5: 소형/셀링 클럽 (중소리그, 2부리그, K/J리그)": 0.95
}

CONTRACT_WEIGHTS = {
    "6개월 이하 (FA 임박/겨울 이적, -20%)": 0.80,
    "1년 남음 (재계약 분기점, -8%)": 0.92,
    "2년 남음 (표준 계약 기준선, 1.00)": 1.00,
    "3년 남음 (구단 협상 우위, +2%)": 1.02,
    "4년 이상 (장기 계약/바이아웃, +4%)": 1.04
}

POSITION_WEIGHTS = {
    "스트라이커 / 센터포워드 (ST/CF, +2%)": 1.02,
    "윙어 / 공격형 미드필더 (WG/CAM, +1%)": 1.01,
    "중앙 / 수비형 미드필더 (CM/CDM, 기준)": 1.00,
    "풀백 / 윙백 (RB/LB/WB, -1%)": 0.99,
    "센터백 (CB, -1%)": 0.99,
    "골키퍼 (GK, -3%)": 0.97
}

VERSATILITY_WEIGHTS = {
    "단일 포지션 전담 (1개 포지션, 기준)": 1.00,
    "듀얼 롤 (2개 포지션 소화, +1%)": 1.01,
    "만능 유틸리티 (3개 이상 소화, +2%)": 1.02
}

REGISTRATION_WEIGHTS = {
    "일반 (EU 국적자 / 쿼터 이슈 없음, 기준)": 1.00,
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿 EPL 홈그로운 (Home-Grown 충족, +4%)": 1.04,
    "🏛️ 구단 자체 유스 출신 (Club-Trained, +2%)": 1.02,
    "🇪🇸🇮🇹 비EU 쿼터 소모 (Non-EU Quota, -2%)": 0.98
}

TRANSFER_TYPE_WEIGHTS = {
    "일반 완전 이적 (Permanent, 기준)": 1.00,
    "단순 1년 임대 (Simple Loan, 1년사용가치 20% 자동환산)": 0.20,
    "임대 후 의무 영입 (Loan w/ Obligation, +2%)": 1.02,
    "임대 후 선택 영입 (Loan w/ Option, 1년사용가치 기준)": 0.20,
    "바이백 조항 포함 이적 (Buy-back Clause, -5%)": 0.95,
    "셀온 지분 포함 이적 (Sell-on Clause, -3%)": 0.97,
    "비공개 이적 (Undisclosed, 시장적정가 1:1 수렴 추정)": 1.00,
    "FA 자유계약 영입 (Free Transfer, 계약금 기준)": 1.00
}

BIG_STAGE_WEIGHTS = {
    "🌟 UCL 본선 16강+ / 주요 A매치 핵심 주전 (+3%)": 1.03,
    "🔥 UEL/UECL 본선 또는 국대 A매치 주전 (+1%)": 1.01,
    "⚖️ 유럽대항전 / 메이저 국대 경험 없음 (기준)": 1.00
}

INJURY_WEIGHTS = {
    "🛡️ 철강왕 (최근 2년 결장 거의 없음, +1%)": 1.01,
    "⚖️ 일반적인 수준 (경미한 1~2주 결장, 기준)": 1.00,
    "⚠️ 잦은 근육/잔부상 (시즌당 4~6주 결장, -3%)": 0.97,
    "🚨 최근 2년 내 장기 부상 이력 (십자인대/골절, -6%)": 0.94
}

URGENCY_WEIGHTS = {
    "⚖️ 일반 보강 / 뎁스 자원 (기준)": 1.00,
    "🔥 최우선 보강 타겟 (선발진 명확한 취약, +4%)": 1.04,
    "🚨 비상사태 / 대체불가 타겟 (핵심이탈·패닉바이, +8%)": 1.08
}

def get_positional_age_weight(age, position_name):
    if "ST/CF" in position_name or "WG/CAM" in position_name:
        if age <= 19: return 1.05
        elif age <= 23: return 1.03
        elif age <= 27: return 1.00
        elif age <= 29: return 0.97
        elif age <= 31: return 0.90
        elif age <= 34: return 0.80
        else: return 0.65
    elif "GK" in position_name or "CB" in position_name:
        if age <= 19: return 1.01
        elif age <= 23: return 1.01
        elif age <= 27: return 1.00
        elif age <= 29: return 1.00
        elif age <= 31: return 0.96
        elif age <= 34: return 0.90
        else: return 0.78
    else:
        if age <= 19: return 1.03
        elif age <= 23: return 1.02
        elif age <= 27: return 1.00
        elif age <= 29: return 0.98
        elif age <= 31: return 0.92
        elif age <= 34: return 0.84
        else: return 0.70

rate_krw = 1500
rate_gbp = 0.86

def format_currency_desc(eur_man_euro):
    if eur_man_euro <= 0: return "₩0억 | £0만"
    total_eur = eur_man_euro * 10000
    krw_eok = (total_eur * rate_krw) / 100000000.0
    gbp_man = eur_man_euro * rate_gbp
    return f"약 {krw_eok:,.1f}억원 | £{gbp_man:,.1f}만"

def get_exact_val(row, col_name, default_val=""):
    try:
        if col_name in row and pd.notnull(row[col_name]) and str(row[col_name]).strip() not in ["", "nan", "None"]:
            return type(default_val)(row[col_name])
    except:
        pass
    return default_val

# 3. 메인 6개 탭 구성
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "💰 적정 이적료 평가", 
    "📱 FotMob 스타일 시즌 성적 및 이적 예측룸 (13대 풀 스탯)",
    "🔍 과거 유사 이적 사례 비교 (Comps TOP 5 & 10)",
    "🎯 이적 첫 시즌 실제 성적 입력 & 모델 검증",
    "👥 신규 이적생 vs 과거 유사 선수 다각도 벤치마크",
    "🏆 이적시장 구단/리그별 종합 결산 & 데이터룸"
])

# ================= TAB 1: 적정 이적료 평가 =================
with tab1:
    st.subheader("💰 적정 이적료 평가 메인 영역 (원본 뼈대 유지)")

# ================= TAB 2: 원본 고유 FotMob 스타일 13대 스탯 입력 탭 =================
with tab2:
    st.subheader("📱 FotMob 스타일 시즌 성적 및 이적 예측룸 (13대 풀 스탯)")

    col_s1, col_s2 = st.columns([2, 1])
    with col_s1:
        st.markdown("##### 🔍 비교 및 분석 대상 선수 선택")
        if history_df.empty or "선수명" not in history_df.columns:
            st.info("💡 등록된 선수 히스토리가 없습니다. 아래에서 직접 스탯을 입력하거나 1번 탭에서 평가를 진행하세요.")
            p_list = []
        else:
            p_list = list(history_df["선수명"].dropna().unique())
        
        sel_player = st.selectbox("DB 선수 불러오기 (선택 시 자동 매핑)", ["직접 입력 / 커스텀"] + p_list, key="tab2_player_select")

    # 기본값 설정
    def_mins = 2206; def_goals = 16; def_xg = 17.44; def_assists = 4; def_xa = 3.33
    def_rating = 7.32; def_matches = 28; def_starts = 25; def_shots = 88; def_sot = 43
    def_chances = 25; def_dribbles = 14; def_touches = 153; def_tackles = 24

    if sel_player != "직접 입력 / 커스텀" and not history_df.empty:
        matched_rows = history_df[history_df["선수명"] == sel_player]
        if not matched_rows.empty:
            r = matched_rows.iloc[-1]
            def_mins = int(r.get("이전_출전시간", 2206)) if pd.notnull(r.get("이전_출전시간")) else 2206
            def_goals = int(r.get("이전_골", 16)) if pd.notnull(r.get("이전_골")) else 16
            def_xg = float(r.get("이전_xG", 17.44)) if pd.notnull(r.get("이전_xG")) else 17.44
            def_assists = int(r.get("이전_도움", 4)) if pd.notnull(r.get("이전_도움")) else 4
            def_xa = float(r.get("이전_xA", 3.33)) if pd.notnull(r.get("이전_xA")) else 3.33
            def_rating = float(r.get("이전_FotMob평점", 7.32)) if pd.notnull(r.get("이전_FotMob평점")) else 7.32
            def_matches = int(r.get("이전_출전경기", 28)) if pd.notnull(r.get("이전_출전경기")) else 28
            def_starts = int(r.get("이전_선발", 25)) if pd.notnull(r.get("이전_선발")) else 25
            def_shots = int(r.get("이전_총슈팅", 88)) if pd.notnull(r.get("이전_총슈팅")) else 88
            def_sot = int(r.get("이전_유효슈팅", 43)) if pd.notnull(r.get("이전_유효슈팅")) else 43
            def_chances = int(r.get("이전_찬스메이킹", 25)) if pd.notnull(r.get("이전_찬스메이킹")) else 25
            def_dribbles = int(r.get("이전_성공드리블", 14)) if pd.notnull(r.get("이전_성공드리블")) else 14
            def_touches = int(r.get("이전_박스터치", 153)) if pd.notnull(r.get("이전_박스터치")) else 153
            def_tackles = int(r.get("이전_태클성공", 24)) if pd.notnull(r.get("이전_태클성공")) else 24

    st.markdown("---")
    st.markdown("#### ⚽ 직전 시즌 13대 핵심 스탯 입력룸")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("##### 📌 기본 출전 및 평점 지표")
        f_matches = st.number_input("출전 경기 (Matches)", min_value=0, max_value=60, value=def_matches, key="t2_matches")
        f_starts = st.number_input("선발 출전 (Starts)", min_value=0, max_value=60, value=def_starts, key="t2_starts")
        f_mins = st.number_input("출전 시간 (Minutes)", min_value=0, max_value=5000, value=def_mins, key="t2_mins")
        f_rating = st.number_input("FotMob 평균 평점", min_value=1.0, max_value=10.0, value=def_rating, step=0.01, key="t2_rating")

        st.markdown("##### 1️⃣ 슈팅 및 득점 (Shooting & Goals)")
        f_goals = st.number_input("득점 (Goals)", min_value=0, value=def_goals, key="t2_goals")
        f_xg = st.number_input("기대 득점 (xG)", min_value=0.0, value=def_xg, step=0.1, key="t2_xg")
        f_shots = st.number_input("총 슈팅 (Shots)", min_value=0, value=def_shots, key="t2_shots")
        f_sot = st.number_input("유효 슈팅 (On Target)", min_value=0, value=def_sot, key="t2_sot")
        f_pk_goals = st.number_input("PK 득점 (Penalty)", min_value=0, value=0, key="t2_pk")

    with col2:
        st.markdown("##### 2️⃣ 패스 및 기회 창출 (Passing & Creativity)")
        f_assists = st.number_input("도움 (Assists)", min_value=0, value=def_assists, key="t2_assists")
        f_xa = st.number_input("기대 도움 (xA)", min_value=0.0, value=def_xa, step=0.1, key="t2_xa")
        f_chances = st.number_input("기회 창출 (Chances)", min_value=0, value=def_chances, key="t2_chances")
        f_big_chances = st.number_input("빅 찬스 메이킹", min_value=0, value=0, key="t2_big_chances")
        f_pass_acc = st.number_input("패스 성공률 (%)", min_value=0.0, max_value=100.0, value=85.0, step=0.1, key="t2_pass_acc")

        st.markdown("##### 3️⃣ 경합 및 수비 기여 (Duels & Defending)")
        f_dribbles = st.number_input("성공한 드리블", min_value=0, value=def_dribbles, key="t2_dribbles")
        f_touches_box = st.number_input("박스 안 터치", min_value=0, value=def_touches, key="t2_touches")
        f_ground_duels = st.number_input("지상 경합 승률 (%)", min_value=0.0, max_value=100.0, value=55.0, step=0.1, key="t2_g_duels")
        f_aerial_duels = st.number_input("공중볼 승률 (%)", min_value=0.0, max_value=100.0, value=50.0, step=0.1, key="t2_a_duels")
        f_tackles = st.number_input("태클 성공", min_value=0, value=def_tackles, key="t2_tackles")

    st.markdown("---")
    with st.expander("🥅 골키퍼 전용 상세 지표 (GK Stats)", expanded=False):
        gk1, gk2, gk3, gk4, gk5, gk6 = st.columns(6)
        with gk1: st.number_input("선방 횟수", min_value=0, value=78, key="t2_gk_saves")
        with gk2: st.number_input("실점", min_value=0, value=28, key="t2_gk_conceded")
        with gk3: st.number_input("득점 차단 (Prevented)", value=2.45, step=0.1, key="t2_gk_prevented")
        with gk4: st.number_input("클린시트", min_value=0, value=10, key="t2_gk_cs")
        with gk5: st.number_input("실점 실수", min_value=0, value=0, key="t2_gk_errors")
        with gk6: st.number_input("공중볼 캐칭", min_value=0, value=18, key="t2_gk_claims")

# ================= TAB 3 ~ 6 =================
with tab3:
    st.subheader("🔍 과거 유사 이적 사례 비교")
with tab4:
    st.subheader("🎯 모델 검증")
with tab5:
    st.subheader("👥 벤치마크")
with tab6:
    st.subheader("🏆 종합 결산")
