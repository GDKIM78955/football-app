import streamlit as st
import pandas as pd
import requests
import json
from datetime import datetime

# 1. 페이지 기본 설정
st.set_page_config(
    page_title="축구 이적료 적정가 분석기",
    page_icon="⚽",
    layout="wide"
)

# 구글 시트 연동 Web App URL
GOOGLE_SHEET_WEBAPP_URL = "https://script.google.com/macros/s/AKfycbxV76sZFJaVPa7tmWSPBGlLaiZHijL77b7MZ_mpr6U-ia6hNO0UEiN-6A_1qz2u7XBNKA/exec"

# 세션 상태 초기화 (폼 리셋용 키 카운터)
if "form_key_id" not in st.session_state:
    st.session_state["form_key_id"] = 0
if "last_saved_msg" not in st.session_state:
    st.session_state["last_saved_msg"] = None

st.title("⚽ 축구 선수 적정 이적료 & 구글 시트 자동 저장 시스템")
st.markdown("""
이 앱은 **리그 수준(Opta 점수)**, **포지션별 차등 에이징 커브**, **영입 구단 규모**, 
**잔여 계약 기간**, **포지션 희소성 & 멀티 능력**, 그리고 **이적 형태(완전/임대/바이백 등)**를 종합 반영하여 적정가를 산출하고 구글 시트에 누적 저장합니다.
""")

# 이전 저장 성공 메시지 출력
if st.session_state["last_saved_msg"]:
    st.success(st.session_state["last_saved_msg"])
    st.session_state["last_saved_msg"] = None

st.divider()

# 2. 가중치 딕셔너리 정의
LEAGUE_WEIGHTS = {
    # Top 5 유럽 빅리그
    "잉글랜드 프리미어리그 (EPL 1부)": 1.00,
    "이탈리아 세리에 A (Serie A 1부)": 0.97,
    "스페인 라리가 (La Liga 1부)": 0.97,
    "독일 분데스리가 (Bundesliga 1부)": 0.97,
    "프랑스 리그 1 (Ligue 1 1부)": 0.97,

    # 상위권 및 유럽 중상위 리그
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

    # 아시아 및 기타 유럽 주요 1부 리그
    "일본 J1리그 (1부)": 0.90,
    "사우디 프로리그 (SPL 1부)": 0.89,
    "대한민국 K리그1 (1부)": 0.89,
    "튀르키예 쉬페르리그 (1부)": 0.89,
    "스위스 슈퍼리그 (1부)": 0.89,
    "오스트리아 분데스리가 (1부)": 0.89,
    "덴마크 수페르리가 (1부)": 0.88,
    "스코틀랜드 프리미어십 (1부)": 0.88,
    "폴란드 엑스트라클라사 (1부)": 0.88,
    "프랑스 리그 2 (2부)": 0.88,
    "그리스 슈퍼리그 (1부)": 0.87,
    "스웨덴 알스벤스칸 (1부)": 0.87,
    "노르웨이 엘리테세리엔 (1부)": 0.87,

    # 아시아 2부 리그
    "일본 J2리그 (2부)": 0.84,
    "대한민국 K리그2 (2부)": 0.83,

    # 기타
    "기타 리그": 0.77
}

CLUB_TIERS = {
    "Tier 1: 엘리트 메가클럽 (레알, 맨시티, 바이에른, PSG 등)": 1.15,
    "Tier 2: 빅클럽 (아스날, 리버풀, 첼시, 바르샤, 유벤투스 등)": 1.08,
    "Tier 3: 중상위권 클럽 (토트넘, AT마드리드, 도르트문트 등)": 1.00,
    "Tier 4: 중하위권 클럽 (EPL 중하위, 타 빅리그 중위권)": 0.92,
    "Tier 5: 소형/셀링 클럽 (중소리그, 2부리그, K/J리그)": 0.80
}

# 보수적 잔여 계약 가중치
CONTRACT_WEIGHTS = {
    "6개월 이하 (FA 임박/겨울 이적, -40%)": 0.60,
    "1년 남음 (재계약 분기점, -15%)": 0.85,
    "2년 남음 (표준 계약 기준선, 1.00)": 1.00,
    "3년 남음 (구단 협상 우위, +8%)": 1.08,
    "4년 이상 (장기 계약/바이아웃, +15%)": 1.15
}

# 포지션 희소성 가중치
POSITION_WEIGHTS = {
    "스트라이커 / 센터포워드 (ST/CF, +10%)": 1.10,
    "윙어 / 공격형 미드필더 (WG/CAM, +5%)": 1.05,
    "중앙 / 수비형 미드필더 (CM/CDM, 기준)": 1.00,
    "센터백 (CB, -5%)": 0.95,
    "풀백 / 윙백 (RB/LB/WB, -5%)": 0.95,
    "골키퍼 (GK, -15%)": 0.85
}

# 멀티 포지션 소화 능력 가중치
VERSATILITY_WEIGHTS = {
    "단일 포지션 전담 (1개 포지션만 소화, 기준)": 1.00,
    "듀얼 롤 (2개 포지션 소화 가능, +5%)": 1.05,
    "만능 유틸리티 (3개 이상 포지션 소화 가능, +10%)": 1.10
}

# 이적 형태 목록
TRANSFER_TYPES = [
    "일반 완전 이적 (Permanent)",
    "임대 후 의무 영입 (Loan w/ Obligation)",
    "임대 후 선택 영입 (Loan w/ Option)",
    "바이백 조항 포함 이적 (Buy-back Clause)",
    "셀온 조항 포함 이적 (Sell-on Clause)",
    "FA 자유계약 영입 (Free Transfer)",
    "기타 / 스왑딜 (Swap Deal)"
]

# 3. 포지션별 차등 에이징 커브 함수
def get_positional_age_weight(age, position_name):
    if "ST/CF" in position_name or "WG/CAM" in position_name:
        if age <= 19: return 1.00
        elif age <= 23: return 1.12
        elif age <= 27: return 1.00
        elif age <= 29: return 0.88
        elif age <= 31: return 0.70
        elif age <= 34: return 0.50
        else: return 0.35
    elif "GK" in position_name or "CB" in position_name:
        if age <= 19: return 0.95
        elif age <= 23: return 1.05
        elif age <= 27: return 1.00
        elif age <= 29: return 1.00
        elif age <= 31: return 0.88
        elif age <= 34: return 0.75
        else: return 0.60
    else:
        if age <= 19: return 1.00
        elif age <= 23: return 1.10
        elif age <= 27: return 1.00
        elif age <= 29: return 0.92
        elif age <= 31: return 0.78
        elif age <= 34: return 0.60
        else: return 0.45

# 4. 사이드바 정보창 & 환율 설정
st.sidebar.header("⚙️ 시스템 설정 및 환율 기준")
st.sidebar.success("🔗 구글 시트 DB 연동 상태: 정상")

with st.sidebar.expander("💱 실시간 환산 기준 환율 설정"):
    rate_krw = st.number_input("1 유로(€)당 원화(KRW)", value=1500, step=10, help="기본: 1€ = 1,500원")
    rate_gbp = st.number_input("1 유로(€)당 파운드(GBP)", value=0.86, step=0.01, format="%.2f", help="기본: 1€ = £0.86")

def format_currency_desc(eur_man_euro):
    if eur_man_euro <= 0:
        return "₩0억 | £0만"
    total_eur = eur_man_euro * 10000
    krw_eok = (total_eur * rate_krw) / 100000000.0
    gbp_man = (eur_man_euro * rate_gbp)
    return f"약 {krw_eok:,.1f}억원 | £{gbp_man:,.1f}만"

with st.sidebar.expander("📈 포지션별 차등 에이징 커브 기준"):
    st.markdown("""
    **⚽ 공격수 / 윙어 (ST/CF, WG/CAM)**
    - 20~23세: `1.12` | 24~27세: `1.00` | 28~29세: `0.88`
    - 30~31세: `0.70` | 32~34세: `0.50` | 35세+: `0.35`
    
    **🛡️ 센터백 / 골키퍼 (CB, GK)**
    - 20~23세: `1.05` | 24~29세: `1.00` (전성기 유지)
    - 30~31세: `0.88` | 32~34세: `0.75` | 35세+: `0.60`
    
    **🏃 미드필더 / 풀백 (CM/CDM, RB/LB)**
    - 20~23세: `1.10` | 24~27세: `1.00` | 28~29세: `0.92`
    - 30~31세: `0.78` | 32~34세: `0.60` | 35세+: `0.45`
    """)

with st.sidebar.expander("📊 포지션 및 멀티 능력 가중치"):
    st.markdown("**[포지션 희소성 가중치]**")
    st.dataframe(pd.DataFrame(list(POSITION_WEIGHTS.items()), columns=["포지션", "가중치"]), hide_index=True, use_container_width=True)
    st.markdown("**[멀티 포지션 가중치]**")
    st.dataframe(pd.DataFrame(list(VERSATILITY_WEIGHTS.items()), columns=["멀티 능력", "가중치"]), hide_index=True, use_container_width=True)

with st.sidebar.expander("📊 잔여 계약 기간 가중치 (보수적 모델)"):
    df_contract = pd.DataFrame(list(CONTRACT_WEIGHTS.items()), columns=["잔여 계약", "가중치"])
    st.dataframe(df_contract, hide_index=True, use_container_width=True)

with st.sidebar.expander("📊 구매 구단 규모(티어) 기준"):
    df_tier = pd.DataFrame(list(CLUB_TIERS.items()), columns=["구단 구분", "가중치"])
    st.dataframe(df_tier, hide_index=True, use_container_width=True)

with st.sidebar.expander("📊 적용 리그 가중치 (Opta 점수 기반)"):
    df_league = pd.DataFrame(list(LEAGUE_WEIGHTS.items()), columns=["리그명", "가중치"])
    st.dataframe(df_league, hide_index=True, use_container_width=True)

# 5. 메인 화면 레이아웃
k_id = st.session_state["form_key_id"]

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📝 이적 & 선수 정보 입력")
    
    c_s1, c_s2 = st.columns(2)
    with c_s1:
        season_val = st.selectbox("이적 시즌", ["26/27", "기타"], key=f"season_{k_id}")
    with c_s2:
        transfer_type = st.selectbox("이적 형태", TRANSFER_TYPES, index=0, key=f"ttype_{k_id}")
        
    player_name = st.text_input("선수 이름", value="", placeholder="예: 비니시우스 주니오르", key=f"name_{k_id}")
    player_nat = st.text_input("선수 국적", value="", placeholder="예: 브라질", key=f"nat_{k_id}")
    player_age = st.number_input("선수 나이 (만 나이)", min_value=15, max_value=45, value=24, key=f"age_{k_id}")
    
    pos_col1, pos_col2 = st.columns(2)
    with pos_col1:
        main_position = st.selectbox("선수 주 포지션", list(POSITION_WEIGHTS.keys()), index=0, key=f"pos_{k_id}")
    with pos_col2:
        versatility = st.selectbox("멀티 포지션 소화 능력", list(VERSATILITY_WEIGHTS.keys()), index=0, key=f"vers_{k_id}")
        
    selling_league = st.selectbox("보내는 리그 (원소속)", list(LEAGUE_WEIGHTS.keys()), key=f"league_{k_id}")
    buying_club_tier = st.selectbox("영입하는 구단 규모", list(CLUB_TIERS.keys()), key=f"tier_{k_id}")
    remaining_contract = st.selectbox("이적 당시 잔여 계약 기간", list(CONTRACT_WEIGHTS.keys()), index=2, key=f"contract_{k_id}")
    
    st.markdown("---")
    
    tm_market_value = st.number_input(
        "트랜스퍼마르크트 시장 가치 (만 유로, €)", 
        min_value=0, 
        value=0, 
        step=50, 
        help="예: 3000만 유로 = €30M", 
        key=f"tm_{k_id}"
    )
    if tm_market_value > 0:
        st.caption(f"💡 시장가치 환산: **{format_currency_desc(tm_market_value)}**")
    
    actual_transfer_fee = st.number_input(
        "실제 이적료 (만 유로, €)", 
        min_value=0, 
        value=0, 
        step=50, 
        help="예: 4000만 유로 = €40M", 
        key=f"fee_{k_id}"
    )
    if actual_transfer_fee > 0:
        st.caption(f"💡 실제이적료 환산: **{format_currency_desc(actual_transfer_fee)}**")
    
    player_notes = st.text_area("개인 메모 / 기대 스탯 (xG, xA, 스카우팅 코멘트 등)", placeholder="예: 90분당 xG 0.45 기록, 전방 압박 능력이 뛰어남", key=f"note_{k_id}")

# 6. 계산 및 결과 출력
league_w = LEAGUE_WEIGHTS[selling_league]
age_w = get_positional_age_weight(player_age, main_position)
club_w = CLUB_TIERS[buying_club_tier]
contract_w = CONTRACT_WEIGHTS[remaining_contract]
pos_w = POSITION_WEIGHTS[main_position]
vers_w = VERSATILITY_WEIGHTS[versatility]

# 6대 가중치 종합 곱연산
fair_value = tm_market_value * league_w * age_w * club_w * contract_w * pos_w * vers_w
diff = actual_transfer_fee - fair_value
overpay_pct = (diff / fair_value) * 100 if fair_value > 0 else 0.0

if fair_value == 0 and actual_transfer_fee == 0:
    status_label = "입력 대기 중"
elif abs(diff) <= (fair_value * 0.05):
    status_label = "⚖️ 적정가 (Fair Deal)"
elif diff > 0:
    status_label = f"⚠️ 고평가 (+{overpay_pct:.1f}%)"
else:
    status_label = f"💎 저평가/혜자 ({overpay_pct:.1f}%)"

with col2:
    st.subheader("📊 분석 결과 및 평가")
    
    display_name = player_name if player_name else "선수명 미입력"
    display_nat = f"({player_nat})" if player_nat else ""
    pos_short = main_position.split(" (")[0]
    ttype_short = transfer_type.split(" (")[0]
    
    st.markdown(f"### **{display_name}** {display_nat} - `{pos_short}` 이적 평가")
    st.caption(f"📌 이적 형태: **{ttype_short}**")
    
    # 6대 가중치 현황 표시
    k1, k2, k3 = st.columns(3)
    k1.metric("리그 가중치", f"{league_w:.2f}")
    k2.metric("나이 (포지션 맞춤)", f"{age_w:.2f}")
    k3.metric("구단 가중치", f"{club_w:.2f}")
    
    k4, k5, k6 = st.columns(3)
    k4.metric("계약 가중치", f"{contract_w:.2f}")
    k5.metric("포지션 가중치", f"{pos_w:.2f}")
    k6.metric("멀티 가중치", f"{vers_w:.2f}")
    
    st.divider()
    
    # 메트릭 출력 (원화/파운드 병기)
    m_col1, m_col2 = st.columns(2)
    with m_col1:
        st.metric("산출된 적정 이적료", f"€{fair_value:,.1f}만")
        if fair_value > 0:
            st.caption(f"{format_currency_desc(fair_value)}")
            
    with m_col2:
        st.metric(
            "실제 이적료", 
            f"€{actual_transfer_fee:,.1f}만", 
            delta=f"{diff:+,.1f}만 (€)" if actual_transfer_fee > 0 else None, 
            delta_color="inverse"
        )
        if actual_transfer_fee > 0:
            st.caption(f"{format_currency_desc(actual_transfer_fee)}")
    
    st.markdown("---")
    
    if status_label == "입력 대기 중":
        st.info("💡 왼쪽 폼에 시장 가치와 이적료를 입력하면 적정성 분석이 시작됩니다.")
    elif "적정가" in status_label:
        st.info(f"**진단 결과**: {status_label}")
    elif "고평가" in status_label:
        diff_desc = format_currency_desc(abs(diff))
        st.error(f"**진단 결과**: {status_label} - 적정가 대비 €{diff:,.1f}만 유로({diff_desc}) 더 지불됨")
    else:
        diff_desc = format_currency_desc(abs(diff))
        st.success(f"**진단 결과**: {status_label} - 적정가 대비 €{abs(diff):,.1f}만 유로({diff_desc}) 저렴하게 영입")

    # 7. 커뮤니티/메모장 공유용 요약 텍스트 박스
    if player_name.strip() and (tm_market_value > 0 or actual_transfer_fee > 0):
        with st.expander("📋 커뮤니티 / 메모장 공유용 요약 텍스트 (클릭하여 복사)", expanded=True):
            nat_text = f"({player_nat}, " if player_nat else "("
            nat_text += f"만 {player_age}세)"
            diff_text = f"적정가 대비 €{abs(diff):,.1f}만 유로({format_currency_desc(abs(diff))}) "
            diff_text += "더 지불됨" if diff > 0 else ("저렴하게 영입" if diff < 0 else "정확히 일치")
            
            summary_text = f"""⚽ [{season_val} 이적 분석] {player_name} {nat_text}
━━━━━━━━━━━━━━━━━━━━
▪️ 이적 형태: {ttype_short}
▪️ 포지션: {pos_short} (가중치 {pos_w:.2f} / 에이징 {age_w:.2f}) | 멀티: {versatility.split(" (")[0]}
▪️ 원소속 리그: {selling_league.split(" (")[0]} (가중치 {league_w:.2f})
▪️ 영입 구단: {buying_club_tier.split(":")[0]} (가중치 {club_w:.2f})
▪️ 잔여 계약: {remaining_contract.split(" (")[0]} (가중치 {contract_w:.2f})
▪️ TM 시장가치: €{tm_market_value:,.0f}만 ({format_currency_desc(tm_market_value)})
▪️ 산출 적정가: €{fair_value:,.1f}만 ({format_currency_desc(fair_value)})
▪️ 실제 이적료: €{actual_transfer_fee:,.1f}만 ({format_currency_desc(actual_transfer_fee)})
━━━━━━━━━━━━━━━━━━━━
📊 종합 진단: {status_label} - {diff_text}
"""
            if player_notes.strip():
                summary_text += f"📝 메모: {player_notes.strip()}\n"
                
            st.code(summary_text.strip(), language="text")
            st.caption("💡 오른쪽 상단의 복사 아이콘(📋)을 누르면 클립보드에 바로 복사됩니다.")

    st.markdown("<br>", unsafe_allow_html=True)
    
    # 8. 구글 시트 저장 버튼
    if st.button("💾 구글 시트 데이터베이스에 저장하기", type="primary", use_container_width=True):
        if not player_name.strip():
            st.warning("⚠️ 선수 이름을 입력해 주세요.")
        else:
            with st.spinner("구글 시트에 기록 중입니다..."):
                contract_desc = remaining_contract.split(" (")[0]
                nat_str = player_nat if player_nat.strip() else "미상"
                note_content = f"[{ttype_short}] 국적: {nat_str} | 포지션: {pos_short} | 멀티: {versatility.split(' (')[0]} | 잔여계약: {contract_desc}"
                if player_notes.strip():
                    note_content += f" | {player_notes.strip()}"
                    
                payload = {
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "season": season_val,
                    "name": player_name,
                    "age": int(player_age),
                    "league": selling_league.split(" (")[0],
                    "tier": buying_club_tier.split(":")[0],
                    "tm_val": float(tm_market_value),
                    "fee": float(actual_transfer_fee),
                    "fair_val": round(fair_value, 1),
                    "diff": round(diff, 1),
                    "status": status_label,
                    "notes": note_content
                }
                try:
                    headers = {"Content-Type": "text/plain;charset=utf-8"}
                    res = requests.post(
                        GOOGLE_SHEET_WEBAPP_URL, 
                        data=json.dumps(payload),
                        headers=headers,
                        timeout=12,
                        allow_redirects=True
                    )
                    
                    if res.status_code in [200, 302]:
                        st.session_state["last_saved_msg"] = f"✅ '{player_name}' 선수의 분석 데이터가 구글 시트에 성공적으로 저장되었습니다! (새 선수를 입력하세요)"
                        st.session_state["form_key_id"] += 1
                        st.rerun()
                    else:
                        st.error(f"⚠️ 응답 코드: {res.status_code}")
                except Exception as e:
                    st.error(f"⚠️ 연결 오류: {e}")
