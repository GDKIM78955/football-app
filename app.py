import streamlit as st
import pandas as pd
import requests
import json
from datetime import datetime

# 1. 페이지 기본 설정
st.set_page_config(
    page_title="축구 이적료 적정가 & Opta 기대스탯 시뮬레이터",
    page_icon="⚽",
    layout="wide"
)

GOOGLE_SHEET_WEBAPP_URL = "https://script.google.com/macros/s/AKfycbxV76sZFJaVPa7tmWSPBGlLaiZHijL77b7MZ_mpr6U-ia6hNO0UEiN-6A_1qz2u7XBNKA/exec"

if "form_key_id" not in st.session_state:
    st.session_state["form_key_id"] = 0
if "last_saved_msg" not in st.session_state:
    st.session_state["last_saved_msg"] = None

st.title("⚽ 축구 선수 이적 가치 평가 & Opta 기대스탯 예측 시스템")

# 2. 리그 및 구단 가중치 데이터베이스
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
    "스코틀랜드 프리미어십 (1부)": 0.88,
    "폴란드 엑스트라클라사 (1부)": 0.88,
    "프랑스 리그 2 (2부)": 0.88,
    "그리스 슈퍼리그 (1부)": 0.87,
    "스웨덴 알스벤스칸 (1부)": 0.87,
    "노르웨이 엘리테세리엔 (1부)": 0.87,
    "일본 J2리그 (2부)": 0.84,
    "대한민국 K리그2 (2부)": 0.83,
    "기타 리그": 0.77
}

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
    "스트라이커 / 센터포워드 (ST/CF)": 1.02,
    "윙어 / 공격형 미드필더 (WG/CAM)": 1.01,
    "중앙 / 수비형 미드필더 (CM/CDM)": 1.00,
    "풀백 / 윙백 (RB/LB/WB)": 0.99,
    "센터백 (CB)": 0.99,
    "골키퍼 (GK)": 0.97
}

VERSATILITY_WEIGHTS = {
    "단일 포지션 전담 (기준)": 1.00,
    "듀얼 롤 (2개 포지션 소화)": 1.01,
    "만능 유틸리티 (3개 이상 소화)": 1.02
}

REGISTRATION_WEIGHTS = {
    "일반 (EU 국적자 / 쿼터 이슈 없음, 기준)": 1.00,
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿 EPL 홈그로운 (Home-Grown 충족, +4%)": 1.04,
    "🏛️ 구단 자체 유스 출신 (Club-Trained, +2%)": 1.02,
    "🇪🇸🇮🇹 비EU 쿼터 소모 (Non-EU Quota, -2%)": 0.98
}

TRANSFER_TYPES = [
    "일반 완전 이적 (Permanent)",
    "임대 후 의무 영입 (Loan w/ Obligation)",
    "임대 후 선택 영입 (Loan w/ Option)",
    "바이백 조항 포함 이적 (Buy-back Clause)",
    "셀온 조항 포함 이적 (Sell-on Clause)",
    "FA 자유계약 영입 (Free Transfer)",
    "기타 / 스왑딜 (Swap Deal)"
]

def get_positional_age_weight(age, position_name):
    if "ST/CF" in position_name or "WG/CAM" in position_name:
        if age <= 19: return 1.00
        elif age <= 23: return 1.03
        elif age <= 27: return 1.00
        elif age <= 29: return 0.97
        elif age <= 31: return 0.90
        elif age <= 34: return 0.80
        else: return 0.65
    elif "GK" in position_name or "CB" in position_name:
        if age <= 19: return 0.98
        elif age <= 23: return 1.01
        elif age <= 27: return 1.00
        elif age <= 29: return 1.00
        elif age <= 31: return 0.96
        elif age <= 34: return 0.90
        else: return 0.78
    else:
        if age <= 19: return 1.00
        elif age <= 23: return 1.02
        elif age <= 27: return 1.00
        elif age <= 29: return 0.98
        elif age <= 31: return 0.92
        elif age <= 34: return 0.84
        else: return 0.70

# 환산 통화 함수
rate_krw = 1500
rate_gbp = 0.86
def format_currency_desc(eur_man_euro):
    if eur_man_euro <= 0: return "₩0억 | £0만"
    total_eur = eur_man_euro * 10000
    krw_eok = (total_eur * rate_krw) / 100000000.0
    gbp_man = (eur_man_euro * rate_gbp)
    return f"약 {krw_eok:,.1f}억원 | £{gbp_man:,.1f}만"

# 3. 메인 탭 구성
tab1, tab2 = st.tabs(["💰 적정 이적료 평가 & 구글 시트 저장", "📊 이적 첫 시즌 Opta 기대 스탯 예측기"])

# ================= TAB 1: 적정 이적료 평가 =================
with tab1:
    if st.session_state["last_saved_msg"]:
        st.success(st.session_state["last_saved_msg"])
        st.session_state["last_saved_msg"] = None

    k_id = st.session_state["form_key_id"]
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("📝 선수 & 이적 기본 정보")
        c_s1, c_s2 = st.columns(2)
        with c_s1: season_val = st.selectbox("이적 시즌", ["26/27", "기타"], key=f"season_{k_id}")
        with c_s2: transfer_type = st.selectbox("이적 형태", TRANSFER_TYPES, index=0, key=f"ttype_{k_id}")
            
        c_n1, c_n2, c_n3 = st.columns([2, 1, 1])
        with c_n1: player_name = st.text_input("선수 이름", value="", placeholder="예: 빅터 오시멘", key=f"name_{k_id}")
        with c_n2: player_nat = st.text_input("국적", value="", placeholder="예: 나이지리아", key=f"nat_{k_id}")
        with c_n3: player_age = st.number_input("나이(만)", min_value=15, max_value=45, value=25, key=f"age_{k_id}")
        
        pos_col1, pos_col2 = st.columns(2)
        with pos_col1: main_position = st.selectbox("주 포지션", list(POSITION_WEIGHTS.keys()), index=0, key=f"pos_{k_id}")
        with pos_col2: versatility = st.selectbox("멀티 포지션 소화 능력", list(VERSATILITY_WEIGHTS.keys()), index=0, key=f"vers_{k_id}")
            
        reg_status = st.selectbox("스쿼드 등록 / HG 쿼터", list(REGISTRATION_WEIGHTS.keys()), index=0, key=f"reg_{k_id}")
        selling_league = st.selectbox("보내는 리그 (원소속)", list(LEAGUE_WEIGHTS.keys()), key=f"league_{k_id}")
        buying_club_tier = st.selectbox("영입하는 구단 규모", list(CLUB_TIERS.keys()), key=f"tier_{k_id}")
        remaining_contract = st.selectbox("이적 당시 잔여 계약 기간", list(CONTRACT_WEIGHTS.keys()), index=2, key=f"contract_{k_id}")
        
        st.markdown("---")
        tm_market_value = st.number_input("트랜스퍼마르크트 시장 가치 (만 유로, €)", min_value=0, value=0, step=50, key=f"tm_{k_id}")
        if tm_market_value > 0: st.caption(f"💡 시장가치 환산: **{format_currency_desc(tm_market_value)}**")
        
        actual_transfer_fee = st.number_input("실제 이적료 (만 유로, €)", min_value=0, value=0, step=50, key=f"fee_{k_id}")
        if actual_transfer_fee > 0: st.caption(f"💡 실제이적료 환산: **{format_currency_desc(actual_transfer_fee)}**")
        
        player_notes = st.text_area("개인 메모 / 스카우팅 코멘트", placeholder="예: 전방 압박 및 결정력 우수", key=f"note_{k_id}")

    league_w = LEAGUE_WEIGHTS[selling_league]
    age_w = get_positional_age_weight(player_age, main_position)
    club_w = CLUB_TIERS[buying_club_tier]
    contract_w = CONTRACT_WEIGHTS[remaining_contract]
    pos_w = POSITION_WEIGHTS[main_position]
    vers_w = VERSATILITY_WEIGHTS[versatility]
    reg_w = REGISTRATION_WEIGHTS[reg_status]

    fair_value = tm_market_value * league_w * age_w * club_w * contract_w * pos_w * vers_w * reg_w
    diff = actual_transfer_fee - fair_value
    overpay_pct = (diff / fair_value) * 100 if fair_value > 0 else 0.0

    if fair_value == 0 and actual_transfer_fee == 0: status_label = "입력 대기 중"
    elif abs(diff) <= (fair_value * 0.05): status_label = "⚖️ 적정가 (Fair Deal)"
    elif diff > 0: status_label = f"⚠️ 고평가 (+{overpay_pct:.1f}%)"
    else: status_label = f"💎 저평가/혜자 ({overpay_pct:.1f}%)"

    with col2:
        st.subheader("📊 분석 결과 및 평가")
        display_name = player_name if player_name else "선수명 미입력"
        display_nat = f"({player_nat})" if player_nat else ""
        pos_short = main_position.split(" (")[0]
        st.markdown(f"### **{display_name}** {display_nat} - `{pos_short}` 이적 평가")
        
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("리그", f"{league_w:.2f}")
        k2.metric("나이", f"{age_w:.2f}")
        k3.metric("구단", f"{club_w:.2f}")
        k4.metric("계약", f"{contract_w:.2f}")
        
        st.divider()
        m_col1, m_col2 = st.columns(2)
        with m_col1:
            st.metric("산출된 적정 이적료", f"€{fair_value:,.1f}만")
            if fair_value > 0: st.caption(f"{format_currency_desc(fair_value)}")
        with m_col2:
            st.metric("실제 이적료", f"€{actual_transfer_fee:,.1f}만", delta=f"{diff:+,.1f}만 (€)" if actual_transfer_fee > 0 else None, delta_color="inverse")
            if actual_transfer_fee > 0: st.caption(f"{format_currency_desc(actual_transfer_fee)}")
        
        st.markdown("---")
        if status_label == "입력 대기 중": st.info("💡 시장 가치와 이적료를 입력하면 분석이 시작됩니다.")
        elif "적정가" in status_label: st.info(f"**진단 결과**: {status_label}")
        elif "고평가" in status_label: st.error(f"**진단 결과**: {status_label} - 적정가 대비 €{diff:,.1f}만 유로 더 지불됨")
        else: st.success(f"**진단 결과**: {status_label} - 적정가 대비 €{abs(diff):,.1f}만 유로 저렴하게 영입")

        if player_name.strip() and (tm_market_value > 0 or actual_transfer_fee > 0):
            with st.expander("📋 커뮤니티 / 메모장 공유용 요약 텍스트 (클릭하여 복사)", expanded=True):
                nat_text = f"({player_nat}, 만 {player_age}세)" if player_nat else f"(만 {player_age}세)"
                summary_text = f"""⚽ [{season_val} 이적 분석] {player_name} {nat_text}
━━━━━━━━━━━━━━━━━━━━
▪️ 포지션: {pos_short} | 원소속 리그: {selling_league.split(" (")[0]}
▪️ 영입 구단: {buying_club_tier.split(":")[0]} | 잔여 계약: {remaining_contract.split(" (")[0]}
▪️ TM 시장가치: €{tm_market_value:,.0f}만 ({format_currency_desc(tm_market_value)})
▪️ 산출 적정가: €{fair_value:,.1f}만 ({format_currency_desc(fair_value)})
▪️ 실제 이적료: €{actual_transfer_fee:,.1f}만 ({format_currency_desc(actual_transfer_fee)})
━━━━━━━━━━━━━━━━━━━━
📊 종합 진단: {status_label}
"""
                if player_notes.strip(): summary_text += f"📝 메모: {player_notes.strip()}\n"
                st.code(summary_text.strip(), language="text")

        if st.button("💾 구글 시트 데이터베이스에 저장하기", type="primary", use_container_width=True):
            if not player_name.strip(): st.warning("⚠️ 선수 이름을 입력해 주세요.")
            else:
                with st.spinner("구글 시트에 기록 중입니다..."):
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
                        "notes": f"[{pos_short}] 국적: {player_nat} | {player_notes}"
                    }
                    try:
                        res = requests.post(GOOGLE_SHEET_WEBAPP_URL, data=json.dumps(payload), headers={"Content-Type": "text/plain;charset=utf-8"}, timeout=12, allow_redirects=True)
                        if res.status_code in [200, 302]:
                            st.session_state["last_saved_msg"] = f"✅ '{player_name}' 선수의 분석 데이터가 구글 시트에 저장되었습니다!"
                            st.session_state["form_key_id"] += 1
                            st.rerun()
                    except Exception as e: st.error(f"⚠️ 저장 오류: {e}")

# ================= TAB 2: Opta 기대 스탯 예측기 =================
with tab2:
    st.subheader("📊 Opta 이전 리그 스탯 기반 ➔ 이적 첫 시즌 기대 스탯 시뮬레이터")
    st.markdown("""
    선수의 **이전 소속 리그에서의 90분당 Opta 기록**과 **이적할 리그/팀 환경**을 매칭하여, 
    새로운 리그 첫 시즌에 기록할 **예상 90분당 스탯 및 시즌 누적 기대값(Projection)**을 산출합니다.
    """)
    
    c_p1, c_p2, c_p3 = st.columns([1, 1, 1])
    with c_p1:
        sim_pos = st.selectbox("예측 대상 포지션", ["⚽ 스트라이커/센터포워드 (ST)", "⚡ 윙어/공격형 미드필더 (WG/CAM)", "🏃 중앙/수비형 미드필더 (CM/CDM)", "🛡️ 풀백/센터백 (FB/CB)", "🧤 골키퍼 (GK)"])
    with c_p2:
        sim_from_league = st.selectbox("출발 리그 (이전 기록 리그)", list(LEAGUE_WEIGHTS.keys()), index=10) # 기본: 에레디비시
    with c_p3:
        sim_to_league = st.selectbox("도착 리그 (이적할 리그)", list(LEAGUE_WEIGHTS.keys()), index=0) # 기본: EPL

    c_t1, c_t2 = st.columns(2)
    with c_t1:
        sim_team_tier = st.selectbox("이적할 구단의 전력 티어", list(CLUB_TIERS.keys()), index=1)
    with c_t2:
        sim_minutes = st.slider("첫 시즌 예상 출전 시간 (분)", min_value=450, max_value=3420, value=2250, step=90, help="2,250분 = 리그 약 25경기 풀타임 상당")

    # 리그 번역 계수 (League Translation Factor)
    from_score = LEAGUE_WEIGHTS[sim_from_league]
    to_score = LEAGUE_WEIGHTS[sim_to_league]
    league_trans_factor = from_score / to_score # 예: 0.92 / 1.00 = 0.92
    team_boost = 1.0 + (CLUB_TIERS[sim_team_tier] - 1.0) * 0.5 # 빅클럽일수록 공격 기회 가산

    st.markdown("---")
    st.markdown(f"#### 📥 **{sim_pos.split(' ')[1]}** 이전 시즌 90분당 Opta 기록 입력")
    
    col_in, col_out = st.columns([1, 1])
    
    with col_in:
        # 포지션별 세부 스탯 입력창
        if "스트라이커" in sim_pos:
            in_npxg = st.number_input("이전 90분당 npxG (기대 득점)", 0.0, 1.5, 0.55, 0.05)
            in_xa = st.number_input("이전 90분당 xA (기대 도움)", 0.0, 1.0, 0.15, 0.05)
            in_shots = st.number_input("이전 90분당 슈팅 수 (Shots/90)", 0.0, 6.0, 3.2, 0.1)
            
            proj_npxg_90 = in_npxg * league_trans_factor * team_boost
            proj_xa_90 = in_xa * league_trans_factor * team_boost
            proj_shots_90 = in_shots * league_trans_factor * team_boost
            
            total_matches = sim_minutes / 90.0
            proj_goals = round(proj_npxg_90 * total_matches, 1)
            proj_assists = round(proj_xa_90 * total_matches, 1)
            proj_shots = round(proj_shots_90 * total_matches, 0)
            
        elif "윙어" in sim_pos:
            in_npxg = st.number_input("이전 90분당 npxG (기대 득점)", 0.0, 1.5, 0.35, 0.05)
            in_xa = st.number_input("이전 90분당 xA (기대 도움)", 0.0, 1.0, 0.30, 0.05)
            in_sca = st.number_input("이전 90분당 슛 생성 횟수 (SCA/90)", 0.0, 10.0, 4.5, 0.2)
            in_prgc = st.number_input("이전 90분당 전진 드리블 운반 (PrgC/90)", 0.0, 15.0, 6.0, 0.5)
            
            proj_npxg_90 = in_npxg * league_trans_factor * team_boost
            proj_xa_90 = in_xa * league_trans_factor * team_boost
            proj_sca_90 = in_sca * league_trans_factor * team_boost
            proj_prgc_90 = in_prgc * league_trans_factor * team_boost
            
            total_matches = sim_minutes / 90.0
            proj_goals = round(proj_npxg_90 * total_matches, 1)
            proj_assists = round(proj_xa_90 * total_matches, 1)
            proj_sca = round(proj_sca_90 * total_matches, 0)
            proj_prgc = round(proj_prgc_90 * total_matches, 0)
            
        elif "미드필더" in sim_pos:
            in_prgp = st.number_input("이전 90분당 전진 패스 (PrgP/90)", 0.0, 15.0, 6.8, 0.5)
            in_pass_pct = st.number_input("이전 패스 성공률 (%)", 50.0, 100.0, 86.5, 0.5)
            in_tkl_int = st.number_input("이전 90분당 태클+가로채기 (Tkl+Int/90)", 0.0, 8.0, 3.8, 0.2)
            in_xa = st.number_input("이전 90분당 xA (기대 도움)", 0.0, 1.0, 0.18, 0.05)
            
            proj_prgp_90 = in_prgp * league_trans_factor * team_boost
            proj_pass_pct = max(70.0, in_pass_pct - (1.0 - league_trans_factor) * 10)
            proj_tkl_int_90 = in_tkl_int * (1.0 / league_trans_factor) * (2.0 - team_boost) # 하위리그로 압박이 심해지면 수비횟수 증가
            proj_xa_90 = in_xa * league_trans_factor * team_boost
            
            total_matches = sim_minutes / 90.0
            proj_prgp = round(proj_prgp_90 * total_matches, 0)
            proj_tkl_int = round(proj_tkl_int_90 * total_matches, 0)
            proj_assists = round(proj_xa_90 * total_matches, 1)
            
        elif "수비수" in sim_pos:
            in_tkl_int = st.number_input("이전 90분당 태클+가로채기 (Tkl+Int/90)", 0.0, 8.0, 3.2, 0.2)
            in_aerial_pct = st.number_input("이전 공중볼 경합 승률 (%)", 30.0, 100.0, 64.0, 1.0)
            in_prgp = st.number_input("이전 90분당 빌드업 전진패스 (PrgP/90)", 0.0, 10.0, 4.2, 0.3)
            
            proj_tkl_int_90 = in_tkl_int * (1.0 / league_trans_factor)
            proj_aerial_pct = max(45.0, in_aerial_pct - (1.0 - league_trans_factor) * 8)
            proj_prgp_90 = in_prgp * league_trans_factor * team_boost
            
            total_matches = sim_minutes / 90.0
            proj_tkl_int = round(proj_tkl_int_90 * total_matches, 0)
            proj_prgp = round(proj_prgp_90 * total_matches, 0)
            
        else: # 골키퍼
            in_psxg_net = st.number_input("이전 90분당 PSxG-GA (실점 억제 지표)", -1.0, 1.0, 0.22, 0.05, help="+값이면 기대실점보다 골을 더 많이 막아낸 선방쇼를 의미")
            in_save_pct = st.number_input("이전 선방률 (%)", 50.0, 95.0, 74.5, 0.5)
            
            proj_psxg_net_90 = in_psxg_net * league_trans_factor
            proj_save_pct = max(60.0, in_save_pct - (1.0 - league_trans_factor) * 6)
            total_matches = sim_minutes / 90.0
            proj_goals_prevented = round(proj_psxg_net_90 * total_matches, 1)

    with col_out:
        st.markdown(f"#### 🎯 **이적 첫 시즌({sim_to_league.split(' ')[1]}) 기대 스탯 예측치**")
        st.caption(f"기준: 첫 시즌 총 **{sim_minutes:,}분** 출전 (약 {sim_minutes/90:.1f}경기)")
        
        if "스트라이커" in sim_pos:
            st.metric("첫 시즌 예상 득점 (xG 기반)", f"{proj_goals:.1f} 골", delta=f"90분당 {proj_npxg_90:.2f} xG")
            st.metric("첫 시즌 예상 도움 (xA 기반)", f"{proj_assists:.1f} 도움", delta=f"90분당 {proj_xa_90:.2f} xA")
            st.metric("첫 시즌 예상 슈팅 수", f"{int(proj_shots):,} 회", delta=f"90분당 {proj_shots_90:.1f} 회")
            
        elif "윙어" in sim_pos:
            st.metric("첫 시즌 예상 공격포인트", f"{proj_goals + proj_assists:.1f} 개", delta=f"{proj_goals:.1f}골 + {proj_assists:.1f}도움")
            st.metric("예상 슛 생성 횟수 (SCA)", f"{int(proj_sca):,} 회", delta=f"90분당 {proj_sca_90:.2f} 회")
            st.metric("예상 전진 드리블 운반", f"{int(proj_prgc):,} 회", delta=f"90분당 {proj_prgc_90:.2f} 회")
            
        elif "미드필더" in sim_pos:
            st.metric("첫 시즌 예상 전진 패스 (PrgP)", f"{int(proj_prgp):,} 회", delta=f"90분당 {proj_prgp_90:.1f} 회")
            st.metric("예상 패스 성공률", f"{proj_pass_pct:.1f} %", delta=f"리그 적응 보정: {proj_pass_pct - in_pass_pct:+.1f}%p")
            st.metric("예상 수비 액션 (태클+가로채기)", f"{int(proj_tkl_int):,} 회", delta=f"90분당 {proj_tkl_int_90:.2f} 회")
            
        elif "수비수" in sim_pos:
            st.metric("첫 시즌 예상 수비 성공 (Tkl+Int)", f"{int(proj_tkl_int):,} 회", delta=f"90분당 {proj_tkl_int_90:.2f} 회")
            st.metric("예상 공중볼 승률", f"{proj_aerial_pct:.1f} %", delta=f"리그 적응 보정: {proj_aerial_pct - in_aerial_pct:+.1f}%p")
            st.metric("예상 빌드업 전진 패스", f"{int(proj_prgp):,} 회", delta=f"90분당 {proj_prgp_90:.1f} 회")
            
        else: # 골키퍼
            st.metric("첫 시즌 예상 실점 억제 (Goals Prevented)", f"{proj_goals_prevented:+.1f} 골", delta=f"90분당 {proj_psxg_net_90:+.2f} PSxG")
            st.metric("예상 선방률 (Save %)", f"{proj_save_pct:.1f} %", delta=f"리그 난이도 보정: {proj_save_pct - in_save_pct:+.1f}%p")

        st.info(f"💡 **분석 노트**: '{sim_from_league.split(' ')[1]}'에서 '{sim_to_league.split(' ')[1]}'로 이적 시 리그 템포 및 수비 압박 차이(난이도 계수: **{league_trans_factor:.2f}x**)가 적용되었습니다.")
