import streamlit as st
import pandas as pd
import numpy as np

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

# ================= 12대 가중치 딕셔너리 정의 =================
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
    "기타 리그": 0.30
}

CLUB_TIERS = {
    "Tier 1: 엘리트 메가클럽 (레알, 맨시티, 바이에른 등)": 1.05,
    "Tier 2: 빅클럽 (아스날, 리버풀, 바르샤 등)": 1.02,
    "Tier 3: 중상위권 클럽 (토트넘, 도르트문트 등)": 1.00,
    "Tier 4: 중하위권 클럽": 0.98,
    "Tier 5: 소형/셀링 클럽": 0.95
}

CONTRACT_WEIGHTS = {
    "6개월 이하 (FA 임박, -20%)": 0.80,
    "1년 남음 (-8%)": 0.92,
    "2년 남음 (기준)": 1.00,
    "3년 남음 (+2%)": 1.02,
    "4년 이상 (+4%)": 1.04
}

POSITION_WEIGHTS = {
    "스트라이커 / 센터포워드 (ST/CF, +2%)": 1.02,
    "윙어 / 공격형 미드필더 (WG/CAM, +1%)": 1.01,
    "중앙 / 수비형 미드필더 (CM/CDM, 기준)": 1.00,
    "풀백 / 윙백 (RB/LB/WB, -1%)": 0.99,
    "센터백 (CB, -1%)": 0.99,
    "골키퍼 (GK, -3%)": 0.97
}

REGISTRATION_WEIGHTS = {
    "일반 (쿼터 이슈 없음, 기준)": 1.00,
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿 EPL 홈그로운 충족 (+4%)": 1.04,
    "🏛️ 구단 자체 유스 출신 (+2%)": 1.02,
    "🇪🇸🇮🇹 비EU 쿼터 소모 (-2%)": 0.98
}

TRANSFER_TYPE_WEIGHTS = {
    "일반 완전 이적 (Permanent, 기준)": 1.00,
    "단순 1년 임대 (20% 자동환산)": 0.20,
    "임대 후 의무 영입 (+2%)": 1.02,
    "바이백 조항 포함 (-5%)": 0.95,
    "FA 자유계약 영입": 1.00
}

BIG_STAGE_WEIGHTS = {
    "🌟 UCL 본선 16강+ / A매치 주전 (+3%)": 1.03,
    "🔥 UEL/UECL 또는 국대 주전 (+1%)": 1.01,
    "⚖️ 유럽대항전 / 국대 경험 없음 (기준)": 1.00
}

INJURY_WEIGHTS = {
    "🛡️ 철강왕 (결장 거의 없음, +1%)": 1.01,
    "⚖️ 일반적인 수준 (기준)": 1.00,
    "⚠️ 잦은 잔부상 (-3%)": 0.97,
    "🚨 장기 부상 이력 (-6%)": 0.94
}

URGENCY_WEIGHTS = {
    "⚖️ 일반 보강 (기준)": 1.00,
    "🔥 최우선 보강 타겟 (+4%)": 1.04,
    "🚨 패닉바이 / 대체불가 타겟 (+8%)": 1.08
}

def get_positional_age_weight(age, position_name):
    if "ST/CF" in position_name or "WG/CAM" in position_name:
        if age <= 19: return 1.05
        elif age <= 23: return 1.03
        elif age <= 27: return 1.00
        elif age <= 29: return 0.97
        elif age <= 31: return 0.90
        else: return 0.70
    else:
        if age <= 23: return 1.01
        elif age <= 27: return 1.00
        elif age <= 29: return 1.00
        elif age <= 31: return 0.96
        else: return 0.80

# 6개 탭 구조 정의
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "💰 적정 이적료 평가", 
    "📱 FotMob 시즌 성적 & 이적 예측",
    "🔍 과거 유사 이적 사례 비교",
    "🎯 이적 첫 시즌 실제 성적 검증",
    "👥 신규 vs 과거 벤치마크",
    "🏆 구단/리그별 종합 결산"
])

# ================= TAB 1: 적정 이적료 평가 =================
with tab1:
    st.subheader("💰 프로페셔널 적정 이적료 평가 시스템 (12대 가중치)")

    trade_type_choice = st.radio("거래 유형", ["🔵 영입 (IN)", "🔴 방출 (OUT)"], horizontal=True, key="t_type")
    is_out_trade = "방출" in trade_type_choice
    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("##### 👤 선수 기본 정보")
        player_name = st.text_input("선수 이름", value="손흥민", key="p_name")
        player_nat = st.text_input("국적", value="대한민국", key="p_nat")
        player_age = st.number_input("만 나이", min_value=15, max_value=45, value=28, key="p_age")
        main_position = st.selectbox("주 포지션", list(POSITION_WEIGHTS.keys()), index=0, key="p_pos")
        selling_league = st.selectbox("원소속 리그", list(LEAGUE_WEIGHTS.keys()), index=0, key="p_league")
        buying_club_tier = st.selectbox("영입구단 티어", list(CLUB_TIERS.keys()), index=1, key="p_tier")

    with col2:
        st.markdown("##### 💼 계약 및 시장 가치")
        tm_market_value = st.number_input("TM 시장가치 (만€)", min_value=0, value=5000, step=100, key="p_tm")
        actual_transfer_fee = st.number_input("실제 이적료 (만€)", min_value=0, value=5500, step=100, key="p_fee")
        remaining_contract = st.selectbox("잔여 계약 기간", list(CONTRACT_WEIGHTS.keys()), index=2, key="p_con")
        reg_status = st.selectbox("스쿼드 쿼터 상태", list(REGISTRATION_WEIGHTS.keys()), index=0, key="p_reg")
        transfer_type = st.selectbox("이적 형태", list(TRANSFER_TYPE_WEIGHTS.keys()), index=0, key="p_ttype")
        big_stage = st.selectbox("UCL/빅매치 검증도", list(BIG_STAGE_WEIGHTS.keys()), index=0, key="p_stage")
        injury_status = st.selectbox("부상 내구성", list(INJURY_WEIGHTS.keys()), index=1, key="p_inj")
        urgency_status = st.selectbox("영입 절박성", list(URGENCY_WEIGHTS.keys()), index=0, key="p_urg")

    # 12대 가중치 연산
    league_w = LEAGUE_WEIGHTS[selling_league]
    age_w = get_positional_age_weight(player_age, main_position)
    club_w = CLUB_TIERS[buying_club_tier]
    contract_w = CONTRACT_WEIGHTS[remaining_contract]
    pos_w = POSITION_WEIGHTS[main_position]
    vers_w = 1.00  # 기본
    reg_w = REGISTRATION_WEIGHTS[reg_status]
    opta_w = 1.00  # 2번 탭 연동 전 기본
    ttype_w = TRANSFER_TYPE_WEIGHTS[transfer_type]
    stage_w = BIG_STAGE_WEIGHTS[big_stage]
    inj_w = INJURY_WEIGHTS[injury_status]
    urg_w = URGENCY_WEIGHTS[urgency_status]

    # 최종 적정가 산출
    fair_value = tm_market_value * league_w * age_w * club_w * contract_w * pos_w * vers_w * reg_w * opta_w * ttype_w * stage_w * inj_w * urg_w
    diff = actual_transfer_fee - fair_value
    overpay_pct = (diff / fair_value) * 100 if fair_value > 0 else 0.0

    st.markdown("---")
    st.subheader("📊 분석 결과 및 12대 가중치 요약")

    res_c1, res_c2, res_c3, res_c4 = st.columns(4)
    res_c1.metric("산출 적정가", f"€{fair_value:,.1f}만")
    res_c2.metric("실제 거래액", f"€{actual_transfer_fee:,.1f}만", delta=f"{diff:+,.1f}만 €")
    res_c3.metric("평가율", f"{overpay_pct:+.1f}%", delta="오버페이" if overpay_pct > 0 else "혜자딜")
    res_c4.metric("종합 누적 배율", f"{(fair_value/tm_market_value if tm_market_value>0 else 1):.3f}x")

# 나머지 탭 빈 껍데기
with tab2: st.subheader("📱 FotMob 시즌 성적 & 이적 예측")
with tab3: st.subheader("🔍 과거 유사 이적 사례 비교")
with tab4: st.subheader("🎯 이적 첫 시즌 실제 성적 검증")
with tab5: st.subheader("👥 신규 vs 과거 벤치마크")
with tab6: st.subheader("🏆 구단/리그별 종합 결산")
