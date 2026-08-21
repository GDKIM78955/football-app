import streamlit as st
import pandas as pd

# 1. 페이지 설정
st.set_page_config(
    page_title="축구 이적료 적정가 분석기",
    page_icon="⚽",
    layout="wide"
)

st.title("⚽ 축구 선수 적정 이적료 & 고평가/저평가 분석기")
st.markdown("""
이 앱은 **리그 수준**, **선수 나이(보수적 모델)**, 그리고 **영입 구단의 규모(빅클럽 프리미엄)**를 복합 적용하여
트랜스퍼마르크트 몸값 대비 실제 이적료의 적정성을 분석합니다.
""")

st.divider()

# 2. 가중치 딕셔너리 정의
LEAGUE_WEIGHTS = {
    "잉글랜드 프리미어리그 (EPL 1부)": 1.00,
    "이탈리아 세리에 A (Serie A 1부)": 0.97,
    "스페인 라리가 (La Liga 1부)": 0.97,
    "독일 분데스리가 (Bundesliga 1부)": 0.97,
    "프랑스 리그 1 (Ligue 1 1부)": 0.97,
    "브라질 세리에 A (Brasileirão 1부)": 0.96,
    "잉글랜드 챔피언십 (EFL 2부)": 0.95,
    "벨기에 주필러 프로 리그 (1부)": 0.94,
    "아르헨티나 프리메라 디비시온 (1부)": 0.94,
    "포르투갈 프리메이라리가 (1부)": 0.94,
    "네덜란드 에레디비시 (Eredivisie 1부)": 0.92,
    "미국 메이저리그사커 (MLS 1부)": 0.92,
    "멕시코 리가 MX (1부)": 0.92,
    "독일 2. 분데스리가 (2부)": 0.92,
    "스페인 라리가 2 (세군다 2부)": 0.91,
    "이탈리아 세리에 B (2부)": 0.90,
    "일본 J1리그 (1부)": 0.90,
    "사우디 프로리그 (SPL 1부)": 0.89,
    "대한민국 K리그1 (1부)": 0.89,
    "튀르키예 쉬페르리그 (1부)": 0.89,
    "스위스 슈퍼리그 (1부)": 0.89,
    "오스트리아 분데스리가 (1부)": 0.89,
    "덴마크 수페르리가 (1부)": 0.88,
    "프랑스 리그 2 (2부)": 0.88,
    "일본 J2리그 (2부)": 0.84,
    "대한민국 K리그2 (2부)": 0.83,
    "기타 리그": 0.77
}

CLUB_TIERS = {
    "Tier 1: 엘리트 메가클럽 (레알, 맨시티, 바이에른, PSG 등)": 1.15,
    "Tier 2: 빅클럽 (아스날, 리버풀, 첼시, 바르샤, 유벤투스 등)": 1.08,
    "Tier 3: 중상위권 클럽 (토트넘, AT마드리드, 도르트문트 등)": 1.00,
    "Tier 4: 중하위권 클럽 (EPL 중하위, 빅리그 중위권 팀)": 0.92,
    "Tier 5: 소형/셀링 클럽 (중소리그 팀, 2부리그, K리그/J리그)": 0.80
}

# 현실적/보수적 나이 가중치 함수
def get_age_weight(age):
    if age <= 19:
        return 1.00   # 유망주 리스크 반영
    elif age <= 23:
        return 1.12   # 완만한 유망주 프리미엄
    elif age <= 27:
        return 1.00   # 전성기 즉시 전력
    elif age <= 29:
        return 0.90   # 재판매 가치 하락
    elif age <= 31:
        return 0.75   # 감가상각 진입
    else:
        return 0.55   # 노장/베테랑

# 3. 사이드바 정보
st.sidebar.header("⚙️ 가중치 설정 & 정보")
with st.sidebar.expander("📊 구매 구단 규모(티어) 기준"):
    df_tier = pd.DataFrame(list(CLUB_TIERS.items()), columns=["구단 구분", "가중치"])
    st.dataframe(df_tier, hide_index=True, use_container_width=True)

with st.sidebar.expander("📊 적용 리그 가중치 기준"):
    df_league = pd.DataFrame(list(LEAGUE_WEIGHTS.items()), columns=["리그명", "가중치"])
    st.dataframe(df_league, hide_index=True, use_container_width=True)

with st.sidebar.expander("📈 적용 나이 가중치 기준 (보수적)"):
    st.markdown("""
    - **17~19세**: `1.00` (검증 리스크 감안)
    - **20~23세**: `1.12` (재판매 프리미엄)
    - **24~27세**: `1.00` (전성기 피크)
    - **28~29세**: `0.90` (전성기 후반)
    - **30~31세**: `0.75` (감가상각 시작)
    - **32세 이상**: `0.55` (베테랑)
    """)

# 4. 선수 및 이적 정보 입력창
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📝 이적 정보 입력")
    
    player_name = st.text_input("선수 이름", value="선수명 입력")
    player_age = st.number_input("선수 나이 (만 나이)", min_value=15, max_value=45, value=22)
    selling_league = st.selectbox("보내는 리그 (Selling League)", list(LEAGUE_WEIGHTS.keys()))
    buying_club_tier = st.selectbox("영입하는 구단 규모 (Buying Club)", list(CLUB_TIERS.keys()))
    
    st.markdown("---")
    tm_market_value = st.number_input("트랜스퍼마르크트 시장 가치 (만 유로, €)", min_value=0, value=3000, step=100)
    actual_transfer_fee = st.number_input("실제 이적료 (만 유로, €)", min_value=0, value=4000, step=100)

# 5. 분석 결과 출력
with col2:
    st.subheader("📊 분석 결과 및 평가")
    
    league_w = LEAGUE_WEIGHTS[selling_league]
    age_w = get_age_weight(player_age)
    club_w = CLUB_TIERS[buying_club_tier]
    
    # 적정가 = 시장가 * 리그가중치 * 나이가중치 * 구단티어가중치
    fair_value = tm_market_value * league_w * age_w * club_w
    diff = actual_transfer_fee - fair_value
    overpay_pct = (diff / fair_value) * 100 if fair_value > 0 else 0.0

    st.markdown(f"### **{player_name}** 선수 이적 평가")
    
    # 3대 가중치 지표 표시
    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.metric("리그 가중치", f"{league_w:.2f}")
    kpi2.metric("나이 가중치", f"{age_w:.2f}")
    kpi3.metric("구단 가중치", f"{club_w:.2f}")
    
    st.divider()
    
    m_col1, m_col2 = st.columns(2)
    m_col1.metric("산출된 적정 이적료", f"€{fair_value:,.1f}만")
    m_col2.metric("실제 이적료", f"€{actual_transfer_fee:,.1f}만", delta=f"{diff:+,.1f}만 (€)", delta_color="inverse")
    
    st.markdown("---")
    
    # 평가 판정
    if abs(diff) <= (fair_value * 0.05):
        st.info("⚖️ **적정가 거래 (Fair Deal)**: 실제 이적료가 산출된 적정 가치 범위 내에 있습니다.")
    elif diff > 0:
        st.error(f"⚠️ **고평가 (Overpaid)**: 적정가 대비 **€{diff:,.1f}만 (+{overpay_pct:.1f}%)** 더 높게 지불되었습니다.")
    else:
        st.success(f"💎 **저평가/혜자 이적 (Bargain)**: 적정가 대비 **€{abs(diff):,.1f}만 ({overpay_pct:.1f}%)** 더 저렴하게 영입되었습니다.")
