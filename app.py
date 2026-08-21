import streamlit as st
import pandas as pd
import math

# Page configuration
st.set_page_config(
    page_title="축구 이적료 적정가 분석기",
    page_icon="⚽",
    layout="wide"
)

# Title and description
st.title("⚽ 축구 선수 적정 이적료 & 고평가/저평가 분석기")
st.markdown("""
이 앱은 **리그 가중치(Opta Power Rankings 기반)**와 **나이 가중치(Age Curve)**를 적용하여 
선수의 트랜스퍼마르크트(Transfermarkt) 시장 가치 대비 실제 이적료가 **고평가(Overpaid)**되었는지 **저평가(Underpaid/Bargain)**되었는지를 분석합니다.
""")

st.divider()

# Sidebar: Reference Tables & Settings
st.sidebar.header("⚙️ 가중치 설정 & 정보")

# 최신 Opta 파워랭킹 기준 리그 가중치
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

def get_age_weight(age):
    if age <= 19:
        return 1.20
    elif age <= 23:
        return 1.30
    elif age <= 27:
        return 1.05
    elif age <= 29:
        return 0.90
    elif age <= 31:
        return 0.70
    else:
        return 0.45

# Display weights info in sidebar
with st.sidebar.expander("📊 적용 리그 가중치 기준"):
    df_league = pd.DataFrame(list(LEAGUE_WEIGHTS.items()), columns=["리그명", "가중치"])
    st.dataframe(df_league, hide_index=True, use_container_width=True)

with st.sidebar.expander("📈 적용 나이 가중치 기준"):
    st.markdown("""
    - **17~19세**: `1.20` (원석 유망주)
    - **20~23세**: `1.30` (최고 가치/재판매 피크)
    - **24~27세**: `1.05` (전성기 피크)
    - **28~29세**: `0.90` (전성기 후반)
    - **30~31세**: `0.70` (감가상각 시작)
    - **32세 이상**: `0.45` (베테랑/FA 임박)
    """)

# Main Content Layout: Two Columns
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📝 선수 정보 입력")
    
    player_name = st.text_input("선수 이름", value="손흥민")
    player_age = st.number_input("선수 나이 (만 나이)", min_value=15, max_value=45, value=22)
    selling_league = st.selectbox("원소속 리그 (Selling League)", list(LEAGUE_WEIGHTS.keys()))
    
    st.markdown("---")
    st.markdown("💡 **이적료 및 몸값 정보 (€ Euros)**")
    
    tm_market_value = st.number_input(
        "트랜스퍼마르크트 시장 가치 (만 유로, €)", 
        min_value=0, 
        value=3000, 
        step=100,
        help="예: 3000만 유로 = €30M"
    )
    
    actual_transfer_fee = st.number_input(
        "실제 이적료 / 예상 이적료 (만 유로, €)", 
        min_value=0, 
        value=4500, 
        step=100,
        help="예: 4500만 유로 = €45M"
    )

    analyze_btn = st.button("🔍 적정 가치 계산하기", type="primary", use_container_width=True)

# Calculation & Display Results
with col2:
    st.subheader("📊 분석 결과 및 평가")
    
    # Calculate factors
    league_w = LEAGUE_WEIGHTS[selling_league]
    age_w = get_age_weight(player_age)
    
    # Fair Value Calculation
    fair_value = tm_market_value * league_w * age_w
    diff = actual_transfer_fee - fair_value
    
    if fair_value > 0:
        overpay_pct = (diff / fair_value) * 100
    else:
        overpay_pct = 0.0

    st.markdown(f"### **{player_name}** 선수 가치 분석")
    
    res_col1, res_col2 = st.columns(2)
    res_col1.metric(label="적용 리그 가중치", value=f"{league_w:.2f}")
    res_col2.metric(label="적용 나이 가중치", value=f"{age_w:.2f}")
    
    st.divider()
    
    m_col1, m_col2 = st.columns(2)
    m_col1.metric(
        label="산출된 적정 이적료 (Fair Value)", 
        value=f"€{fair_value:,.1f}M (만 유로)"
    )
    m_col2.metric(
        label="실제 이적료 (Actual Fee)", 
        value=f"€{actual_transfer_fee:,.1f}M (만 유로)",
        delta=f"{diff:+,.1f}M (€)",
        delta_color="inverse"
    )
    
    st.markdown("---")
    
    # Value Judgment
    if abs(diff) <= (fair_value * 0.05):
        st.info("⚖️ **적정가 거래 (Fair Deal)**: 실제 이적료가 산출된 적정 가치 범위 내에 있습니다.")
    elif diff > 0:
        st.error(f"⚠️ **고평가 (Overpaid)**: 적정가 대비 **€{diff:,.1f}M (+{overpay_pct:.1f}%)** 더 높게 거래되었습니다.")
    else:
        st.success(f"💎 **저평가/혜자 이적 (Bargain)**: 적정가 대비 **€{abs(diff):,.1f}M ({overpay_pct:.1f}%)** 더 저렴하게 거래되었습니다.")

    st.caption("※ 본 산출식은 트랜스퍼마르크트 기본 가치에 리그 수준 및 나이곡선 보정치를 적층 적용한 기초 모델입니다.")

# Footer Sample CSV download section
st.divider()
st.subheader("📁 일괄 분석용 샘플 CSV 다운로드 (선택사항)")
st.write("여러 선수를 한 번에 엑셀로 정리해서 테스트해 볼 수 있는 파이썬 코드 구조입니다.")

sample_data = pd.DataFrame([
    {"선수명": "선수A", "나이": 21, "리그": "네덜란드 에레디비시 (Eredivisie 1부)", "TM시장가치(만유로)": 2000, "실제이적료(만유로)": 3500},
    {"선수명": "선수B", "나이": 30, "리그": "잉글랜드 프리미어리그 (EPL 1부)", "TM시장가치(만유로)": 4000, "실제이적료(만유로)": 3000},
])
st.dataframe(sample_data, use_container_width=True)
