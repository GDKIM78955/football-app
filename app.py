import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# 1. 페이지 기본 설정
st.set_page_config(
    page_title="축구 이적료 적정가 분석기",
    page_icon="⚽",
    layout="wide"
)

# 구글 시트 Web App 연동 URL
GOOGLE_SHEET_WEBAPP_URL = "https://script.google.com/macros/s/AKfycbxV76sZFJaVPa7tmWSPBGlLaiZHijL77b7MZ_mpr6U-ia6hNO0UEiN-6A_1qz2u7XBNKA/exec"

st.title("⚽ 축구 선수 적정 이적료 & 구글 시트 자동 저장 시스템")
st.markdown("""
리그 수준(Opta 점수 기반), 선수 나이 곡선, 구매 구단 규모(빅클럽 프리미엄)를 적용해 적정가를 산출하고,
분석 결과를 **내 구글 시트(DB)**에 실시간으로 자동 저장합니다.
""")

st.divider()

# 2. 가중치 딕셔너리
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

def get_age_weight(age):
    if age <= 19:
        return 1.00
    elif age <= 23:
        return 1.12
    elif age <= 27:
        return 1.00
    elif age <= 29:
        return 0.90
    elif age <= 31:
        return 0.75
    else:
        return 0.55

# 3. 사이드바 정보 창
st.sidebar.header("⚙️ 시스템 설정 및 가중치 정보")
st.sidebar.success("🔗 구글 시트 데이터베이스 연동됨")

with st.sidebar.expander("📊 구매 구단 티어 기준"):
    st.dataframe(pd.DataFrame(list(CLUB_TIERS.items()), columns=["구단 구분", "가중치"]), hide_index=True, use_container_width=True)

with st.sidebar.expander("📊 원소속 리그 가중치"):
    st.dataframe(pd.DataFrame(list(LEAGUE_WEIGHTS.items()), columns=["리그명", "가중치"]), hide_index=True, use_container_width=True)

with st.sidebar.expander("📈 나이 가중치 (보수적 모델)"):
    st.markdown("""
    - **17~19세**: `1.00`
    - **20~23세**: `1.12`
    - **24~27세**: `1.00`
    - **28~29세**: `0.90`
    - **30~31세**: `0.75`
    - **32세 이상**: `0.55`
    """)

# 4. 입력 폼 레이아웃
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📝 이적 & 선수 정보 입력")
    
    season_val = st.selectbox("이적 시즌", ["24/25", "25/26", "23/24", "기타"])
    player_name = st.text_input("선수 이름", value="손흥민")
    player_age = st.number_input("선수 나이 (만 나이)", min_value=15, max_value=45, value=23)
    selling_league = st.selectbox("보내는 리그 (원소속)", list(LEAGUE_WEIGHTS.keys()))
    buying_club_tier = st.selectbox("영입하는 구단 규모", list(CLUB_TIERS.keys()))
    
    st.markdown("---")
    tm_market_value = st.number_input("트랜스퍼마르크트 시장 가치 (만 유로, €)", min_value=0, value=3000, step=100)
    actual_transfer_fee = st.number_input("실제 이적료 (만 유로, €)", min_value=0, value=4000, step=100)
    
    player_notes = st.text_area("개인 메모 / 기대 스탯 (xG, xA, 평점, 스카우팅 코멘트 등)", placeholder="예: 지난 시즌 90분당 xG 0.45 기록. 전방 압박 능력이 뛰어나 적응 빠를 것으로 예상.")

# 5. 계산 및 평가
league_w = LEAGUE_WEIGHTS[selling_league]
age_w = get_age_weight(player_age)
club_w = CLUB_TIERS[buying_club_tier]

fair_value = tm_market_value * league_w * age_w * club_w
diff = actual_transfer_fee - fair_value
overpay_pct = (diff / fair_value) * 100 if fair_value > 0 else 0.0

if abs(diff) <= (fair_value * 0.05):
    status_label = "⚖️ 적정가 (Fair Deal)"
elif diff > 0:
    status_label = f"⚠️ 고평가 (+{overpay_pct:.1f}%)"
else:
    status_label = f"💎 저평가/혜자 ({overpay_pct:.1f}%)"

with col2:
    st.subheader("📊 분석 결과 및 DB 저장")
    
    st.markdown(f"### **{player_name}** 선수 이적 평가")
    
    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.metric("리그 가중치", f"{league_w:.2f}")
    kpi2.metric("나이 가중치", f"{age_w:.2f}")
    kpi3.metric("구단 가중치", f"{club_w:.2f}")
    
    st.divider()
    
    m_col1, m_col2 = st.columns(2)
    m_col1.metric("산출된 적정 이적료", f"€{fair_value:,.1f}만")
    m_col2.metric("실제 이적료", f"€{actual_transfer_fee:,.1f}만", delta=f"{diff:+,.1f}만 (€)", delta_color="inverse")
    
    st.markdown("---")
    
    if "적정가" in status_label:
        st.info(f"**진단 결과**: {status_label}")
    elif "고평가" in status_label:
        st.error(f"**진단 결과**: {status_label} - 적정가보다 €{diff:,.1f}만 유로 더 지불됨")
    else:
        st.success(f"**진단 결과**: {status_label} - 적정가보다 €{abs(diff):,.1f}만 유로 저렴하게 영입")

    st.markdown("<br>", unsafe_allow_html=True)
    
    # 6. 구글 시트 저장 버튼
    if st.button("💾 구글 시트 데이터베이스에 저장하기", type="primary", use_container_width=True):
        with st.spinner("구글 시트에 기록 중입니다..."):
            payload = {
                "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "season": season_val,
                "name": player_name,
                "age": player_age,
                "league": selling_league.split(" (")[0],
                "tier": buying_club_tier.split(":")[0],
                "tm_val": tm_market_value,
                "fee": actual_transfer_fee,
                "fair_val": round(fair_value, 1),
                "diff": round(diff, 1),
                "status": status_label,
                "notes": player_notes
            }
            try:
                res = requests.post(GOOGLE_SHEET_WEBAPP_URL, json=payload, timeout=10)
                if res.status_code == 200:
                    st.success(f"✅ '{player_name}' 선수의 분석 데이터가 구글 시트에 안전하게 저장되었습니다!")
                else:
                    st.error("⚠️ 저장 중 문제가 발생했습니다. 잠시 후 다시 시도해 주세요.")
            except Exception as e:
                st.error(f"⚠️ 연결 오류 발생: {e}")
