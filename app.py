import streamlit as st
import pandas as pd
import numpy as np
import requests
import json
import plotly.graph_objects as go
from datetime import datetime

# tabs 폴더 안의 패키지에서 6개 탭 모듈 임포트
from tabs.tab1_eval import render_tab1
from tabs.tab2_fotmob import render_tab2
from tabs.tab3_comps import render_tab3
from tabs.tab4_validation import render_tab4
from tabs.tab5_benchmark import render_tab5
from tabs.tab6_analytics import render_tab6

# 1. 페이지 기본 설정
st.set_page_config(
    page_title="축구 이적시장 12대 가중치 분석 & FotMob 프로젝션 Pro",
    page_icon="⚽",
    layout="wide"
)

GOOGLE_SHEET_WEBAPP_URL = "https://script.google.com/macros/s/AKfycbzlIZEZ6C8T1mpIErWoAgi28cCfeezNfqE2U9CR1P6vtB5t928n7VSJ3OvhCyTd-not8g/exec"
SPREADSHEET_ID = "1oUDZ96SJ7aklJdrq_rK5K1ti2RRUAGO3PqqLvPM9E2A"
SHEET_CSV_URL = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/gviz/tq?tqx=out:csv"

VAL_SHEET_GID = "2043479646"
VAL_SHEET_CSV_URL = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv&gid={VAL_SHEET_GID}"

# 세션 상태 초기화
if "form_key_id" not in st.session_state:
    st.session_state["form_key_id"] = 0
if "last_saved_msg" not in st.session_state:
    st.session_state["last_saved_msg"] = None

default_stats = {
    "f_mins": 2206, "f_goals": 16, "f_xg": 17.44, "f_assists": 4, "f_xa": 3.33,
    "f_rating": 7.32, "f_matches": 28, "f_starts": 25, "f_shots": 88, "f_sot": 43,
    "f_chances": 25, "f_dribbles": 14, "f_touches_box": 153, "f_tackles": 24,
    "f_gk_saves": 78, "f_gk_conceded": 28, "f_gk_prevented": 2.45,
    "f_gk_cs": 10, "f_gk_errors": 0, "f_gk_claims": 18
}
for k, v in default_stats.items():
    if k not in st.session_state:
        st.session_state[k] = v

st.title("⚽ 프로페셔널 축구 이적시장 12대 가중치 분석 & 스카우팅 데이터룸")

# 공통 가중치 및 유틸 정의
LEAGUE_WEIGHTS = {
    "잉글랜드 프리미어리그 (EPL 1부)": 1.00, "스페인 라리가 (La Liga 1부)": 0.92,
    "독일 분데스리가 (Bundesliga 1부)": 0.91, "이탈리아 세리에 A (Serie A 1부)": 0.90,
    "프랑스 리그 1 (Ligue 1 1부)": 0.88, "잉글랜드 챔피언십 (EFL 2부)": 0.80,
    "포르투갈 프리메이라리가 (1부)": 0.78, "네덜란드 에레디비시 (Eredivisie 1부)": 0.77,
    "벨기에 주필러 프로 리그 (1부)": 0.75, "브라질 세리에 A (Brasileirão 1부)": 0.68,
    "독일 2. 분데스리가 (2부)": 0.67, "스페인 라리가 2 (세군다 2부)": 0.66,
    "튀르키예 쉬페르리그 (1부)": 0.65, "이탈리아 세리에 B (2부)": 0.64,
    "미국 메이저리그사커 (MLS 1부)": 0.64, "멕시코 리가 MX (1부)": 0.63,
    "스위스 슈퍼리그 (1부)": 0.62, "오스트리아 분데스리가 (1부)": 0.62,
    "덴마크 수페르리가 (1부)": 0.61, "스코틀랜드 프리미어십 (1부)": 0.60,
    "아르헨티나 프리메라 디비시온 (1부)": 0.60, "폴란드 엑스트라클라사 (1부)": 0.55,
    "프랑스 리그 2 (2부)": 0.55, "그리스 슈퍼리그 (1부)": 0.54,
    "사우디 프로리그 (SPL 1부)": 0.52, "일본 J1리그 (1부)": 0.50,
    "대한민국 K리그1 (1부)": 0.48, "스웨덴 알스벤스칸 (1부)": 0.48,
    "노르웨이 엘리테세리엔 (1부)": 0.47, "일본 J2리그 (2부)": 0.35,
    "대한민국 K리그2 (2부)": 0.33, "기타 리그": 0.30
}

TRACKED_LEAGUE_NAMES = ["프리미어리그", "라리가", "분데스리가", "세리에 A", "리그 1", "에레디비시", "포르투갈", "벨기에", "튀르키예", "챔피언십"]

CLUB_TIERS = {
    "Tier 1: 엘리트 메가클럽 (레알, 맨시티, 바이에른, PSG 등)": 1.05,
    "Tier 2: 빅클럽 (아스날, 리버풀, 첼시, 바르샤, 유벤투스 등)": 1.02,
    "Tier 3: 중상위권 클럽 (토트넘, AT마드리드, 도르트문트 등)": 1.00,
    "Tier 4: 중하위권 클럽 (EPL 중하위, 타 빅리그 중위권)": 0.98,
    "Tier 5: 소형/셀링 클럽 (중소리그, 2부리그, K/J리그)": 0.95
}

CONTRACT_WEIGHTS = {
    "6개월 이하 (FA 임박/겨울 이적, -20%)": 0.80, "1년 남음 (재계약 분기점, -8%)": 0.92,
    "2년 남음 (표준 계약 기준선, 1.00)": 1.00, "3년 남음 (구단 협상 우위, +2%)": 1.02,
    "4년 이상 (장기 계약/바이아웃, +4%)": 1.04
}

POSITION_WEIGHTS = {
    "스트라이커 / 센터포워드 (ST/CF, +2%)": 1.02, "윙어 / 공격형 미드필더 (WG/CAM, +1%)": 1.01,
    "중앙 / 수비형 미드필더 (CM/CDM, 기준)": 1.00, "풀백 / 윙백 (RB/LB/WB, -1%)": 0.99,
    "센터백 (CB, -1%)": 0.99, "골키퍼 (GK, -3%)": 0.97
}

VERSATILITY_WEIGHTS = {"단일 포지션 전담 (1개 포지션, 기준)": 1.00, "듀얼 롤 (2개 포지션 소화, +1%)": 1.01, "만능 유틸리티 (3개 이상 소화, +2%)": 1.02}
REGISTRATION_WEIGHTS = {"일반 (EU 국적자 / 쿼터 이슈 없음, 기준)": 1.00, "🏴󠁧󠁢󠁥󠁮󠁧󠁿 EPL 홈그로운 (Home-Grown 충족, +4%)": 1.04, "🏛️ 구단 자체 유스 출신 (Club-Trained, +2%)": 1.02, "🇪🇸🇮🇹 비EU 쿼터 소모 (Non-EU Quota, -2%)": 0.98}
TRANSFER_TYPE_WEIGHTS = {"일반 완전 이적 (Permanent, 기준)": 1.00, "단순 1년 임대 (Simple Loan, 1년사용가치 20% 자동환산)": 0.20, "임대 후 의무 영입 (Loan w/ Obligation, +2%)": 1.02, "임대 후 선택 영입 (Loan w/ Option, 1년사용가치 기준)": 0.20, "바이백 조항 포함 이적 (Buy-back Clause, -5%)": 0.95, "셀온 지분 포함 이적 (Sell-on Clause, -3%)": 0.97, "비공개 이적 (Undisclosed, 시장적정가 1:1 수렴 추정)": 1.00, "FA 자유계약 영입 (Free Transfer, 계약금 기준)": 1.00}
BIG_STAGE_WEIGHTS = {"🌟 UCL 본선 16강+ / 주요 A매치 핵심 주전 (+3%)": 1.03, "🔥 UEL/UECL 본선 또는 국대 A매치 주전 (+1%)": 1.01, "⚖️ 유럽대항전 / 메이저 국대 경험 없음 (기준)": 1.00}
INJURY_WEIGHTS = {"🛡️ 철강왕 (최근 2년 결장 거의 없음, +1%)": 1.01, "⚖️ 일반적인 수준 (경미한 1~2주 결장, 기준)": 1.00, "⚠️ 잦은 근육/잔부상 (시즌당 4~6주 결장, -3%)": 0.97, "🚨 최근 2년 내 장기 부상 이력 (십자인대/골절, -6%)": 0.94}
URGENCY_WEIGHTS = {"⚖️ 일반 보강 / 뎁스 자원 (기준)": 1.00, "🔥 최우선 보강 타겟 (선발진 명확한 취약, +4%)": 1.04, "🚨 비상사태 / 대체불가 타겟 (핵심이탈·패닉바이, +8%)": 1.08}

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

@st.cache_data(ttl=5)
def fetch_sheet_history():
    try:
        return pd.read_csv(SHEET_CSV_URL)
    except Exception:
        return pd.DataFrame()

history_df = fetch_sheet_history()

# 메인 6개 탭 정의
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "💰 적정 이적료 평가", 
    "📱 FotMob 시즌 성적 & 이적 예측 (13대 풀 스탯)",
    "🔍 과거 유사 이적 사례 비교 (Comps TOP 5 & 10)",
    "🎯 이적 첫 시즌 실제 성적 입력 & 모델 검증",
    "👥 신규 이적생 vs 과거 유사 선수 다각도 벤치마크",
    "🏆 이적시장 구단/리그별 종합 결산 & 데이터룸"
])

# 각 탭 모듈 렌더링 호출
with tab1:
    tab1_data = render_tab1(
        history_df, GOOGLE_SHEET_WEBAPP_URL, LEAGUE_WEIGHTS, CLUB_TIERS, 
        CONTRACT_WEIGHTS, POSITION_WEIGHTS, VERSATILITY_WEIGHTS, REGISTRATION_WEIGHTS, 
        TRANSFER_TYPE_WEIGHTS, BIG_STAGE_WEIGHTS, INJURY_WEIGHTS, URGENCY_WEIGHTS, 
        TRACKED_LEAGUE_NAMES, get_positional_age_weight, format_currency_desc, rate_krw, rate_gbp
    )

with tab2:
    render_tab2(
        history_df, GOOGLE_SHEET_WEBAPP_URL, LEAGUE_WEIGHTS, TRACKED_LEAGUE_NAMES, 
        format_currency_desc, rate_krw, rate_gbp, tab1_data
    )

with tab3:
    render_tab3(history_df, LEAGUE_WEIGHTS, format_currency_desc, tab1_data)

with tab4:
    render_tab4(VAL_SHEET_CSV_URL, GOOGLE_SHEET_WEBAPP_URL)

with tab5:
    render_tab5(history_df, LEAGUE_WEIGHTS, format_currency_desc, tab1_data)

with tab6:
    render_tab6(history_df, GOOGLE_SHEET_WEBAPP_URL, format_currency_desc)
