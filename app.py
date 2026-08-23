import streamlit as st
import pandas as pd
import requests
import json
from datetime import datetime

# 1. 페이지 기본 설정
st.set_page_config(
    page_title="축구 이적시장 12대 가중치 분석 & FotMob 37대 지표 프로젝션",
    page_icon="⚽",
    layout="wide"
)

GOOGLE_SHEET_WEBAPP_URL = "https://script.google.com/macros/s/AKfycbzlIZEZ6C8T1mpIErWoAgi28cCfeezNfqE2U9CR1P6vtB5t928n7VSJ3OvhCyTd-not8g/exec"
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/1oUDZ96SJ7aklJdrq_rK5K1ti2RRUAGO3PqqLvPM9E2A/gviz/tq?tqx=out:csv"

if "form_key_id" not in st.session_state:
    st.session_state["form_key_id"] = 0
if "last_saved_msg" not in st.session_state:
    st.session_state["last_saved_msg"] = None

default_stats = {
    "f_mins": 2206, "f_goals": 16, "f_xg": 17.44, "f_assists": 4, "f_xa": 3.33,
    "f_rating": 7.32, "f_matches": 28, "f_starts": 25, "f_shots": 88, "f_sot": 43,
    "f_chances": 25, "f_dribbles": 14, "f_touches_box": 153, "f_tackles": 24
}
for k, v in default_stats.items():
    if k not in st.session_state:
        st.session_state[k] = v

st.title("⚽ 축구 선수 12대 지표 적정 이적료 평가 & FotMob 시즌 예측")

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
    "임대 후 의무 영입 (Loan w/ Obligation, +2%)": 1.02,
    "바이백 조항 포함 이적 (Buy-back Clause, -5%)": 0.95,
    "셀온 지분 포함 이적 (Sell-on Clause, -3%)": 0.97,
    "임대 후 선택 영입 (Loan w/ Option, -2%)": 0.98,
    "FA 자유계약 영입 (Free Transfer, 기준)": 1.00
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
    gbp_man = (eur_man_euro * rate_gbp)
    return f"약 {krw_eok:,.1f}억원 | £{gbp_man:,.1f}만"

# 3. 메인 3개 탭 구성
tab1, tab2, tab3 = st.tabs([
    "💰 적정 이적료 평가", 
    "📱 FotMob 시즌 성적 & 이적 예측 (시트 저장)",
    "🔍 과거 유사 이적 사례 비교 (Comps TOP 10)"
])

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
        with c_s2: transfer_type = st.selectbox("이적 형태 & 계약 조항", list(TRANSFER_TYPE_WEIGHTS.keys()), index=0, key=f"ttype_{k_id}")
            
        c_n1, c_n2, c_n3 = st.columns([2, 1, 1])
        with c_n1: player_name = st.text_input("선수 이름", value="", placeholder="예: Ezri Konsa", key=f"name_{k_id}")
        with c_n2: player_nat = st.text_input("국적", value="", placeholder="예: 잉글랜드", key=f"nat_{k_id}")
        with c_n3: player_age = st.number_input("나이(만)", min_value=15, max_value=45, value=28, key=f"age_{k_id}")
        
        pos_col1, pos_col2 = st.columns(2)
        with pos_col1: main_position = st.selectbox("주 포지션", list(POSITION_WEIGHTS.keys()), index=4, key=f"pos_{k_id}")
        with pos_col2: versatility = st.selectbox("멀티 포지션 소화 능력", list(VERSATILITY_WEIGHTS.keys()), index=0, key=f"vers_{k_id}")
            
        c_r1, c_r2 = st.columns(2)
        with c_r1: reg_status = st.selectbox("스쿼드 등록 / HG 쿼터", list(REGISTRATION_WEIGHTS.keys()), index=1, key=f"reg_{k_id}")
        with c_r2: big_stage = st.selectbox("UCL / 빅매치 검증도", list(BIG_STAGE_WEIGHTS.keys()), index=0, key=f"stage_{k_id}")
        
        c_i1, c_i2 = st.columns(2)
        with c_i1: injury_status = st.selectbox("부상 내구성 & 메디컬 리스크", list(INJURY_WEIGHTS.keys()), index=1, key=f"inj_{k_id}")
        with c_i2: urgency_status = st.selectbox("영입 구단 절박성 & 취약 포지션", list(URGENCY_WEIGHTS.keys()), index=0, key=f"urg_{k_id}")

        selling_league = st.selectbox("보내는 리그 (원소속)", list(LEAGUE_WEIGHTS.keys()), index=0, key=f"league_{k_id}")
        buying_club_tier = st.selectbox("영입하는 구단 규모", list(CLUB_TIERS.keys()), index=1, key=f"tier_{k_id}")
        remaining_contract = st.selectbox("이적 당시 잔여 계약 기간", list(CONTRACT_WEIGHTS.keys()), index=2, key=f"contract_{k_id}")
        
        st.markdown("---")
        
        f_p90 = (st.session_state["f_mins"] / 90.0) if st.session_state["f_mins"] > 0 else 1.0
        cur_p90_exp = (st.session_state["f_xg"] + st.session_state["f_xa"]) / f_p90
        cur_rating = st.session_state["f_rating"]
        
        if cur_rating >= 7.45 or cur_p90_exp >= 0.75:
            opta_w = 1.02
            opta_desc = "🌟 최상위권 엘리트 활약 (+2%)"
        elif cur_rating >= 7.15 or cur_p90_exp >= 0.50:
            opta_w = 1.01
            opta_desc = "🔥 주전급 준수한 활약 (+1%)"
        elif cur_rating >= 6.80 or cur_p90_exp >= 0.25:
            opta_w = 1.00
            opta_desc = "⚖️ 리그 평균 수준 (기준 1.00)"
        else:
            opta_w = 0.98
            opta_desc = "⚠️ 기대 이하 / 부진 (-2%)"

        with st.expander("🔗 [FotMob 탭 연동] 지난 시즌 실적 및 평점 가중치", expanded=True):
            st.markdown(f"""
            - **지난 시즌 실적**: `{st.session_state['f_goals']}골 {st.session_state['f_assists']}도움` (출전 {st.session_state['f_mins']:,}분)
            - **기대 생산력**: `xG {st.session_state['f_xg']:.2f}` / `xA {st.session_state['f_xa']:.2f}` (90분당 **{cur_p90_exp:.2f}**)
            - **FotMob 평균 평점**: `★ {cur_rating:.2f}` ➔ **{opta_desc} (가중치 {opta_w:.2f})**
            """)

        st.markdown("---")
        tm_market_value = st.number_input("트랜스퍼마르크트 시장 가치 (만 유로, €)", min_value=0, value=4500, step=50, key=f"tm_{k_id}")
        if tm_market_value > 0: st.caption(f"💡 시장가치 환산: **{format_currency_desc(tm_market_value)}**")
        
        actual_transfer_fee = st.number_input("실제 이적료 (만 유로, €)", min_value=0, value=5960, step=50, key=f"fee_{k_id}")
        if actual_transfer_fee > 0: st.caption(f"💡 실제이적료 환산: **{format_currency_desc(actual_transfer_fee)}**")
        
        player_notes = st.text_area("개인 메모 / 스카우팅 코멘트", placeholder="예: 대인 방어 및 후방 빌드업 우수", key=f"note_{k_id}")

    # 12대 가중치 추출
    league_w = LEAGUE_WEIGHTS[selling_league]
    age_w = get_positional_age_weight(player_age, main_position)
    club_w = CLUB_TIERS[buying_club_tier]
    contract_w = CONTRACT_WEIGHTS[remaining_contract]
    pos_w = POSITION_WEIGHTS[main_position]
    vers_w = VERSATILITY_WEIGHTS[versatility]
    reg_w = REGISTRATION_WEIGHTS[reg_status]
    ttype_w = TRANSFER_TYPE_WEIGHTS[transfer_type]
    stage_w = BIG_STAGE_WEIGHTS[big_stage]
    inj_w = INJURY_WEIGHTS[injury_status]
    urg_w = URGENCY_WEIGHTS[urgency_status]

    fair_value = tm_market_value * league_w * age_w * club_w * contract_w * pos_w * vers_w * reg_w * opta_w * ttype_w * stage_w * inj_w * urg_w
    diff = actual_transfer_fee - fair_value
    diff_desc = format_currency_desc(abs(diff))
    overpay_pct = (diff / fair_value) * 100 if fair_value > 0 else 0.0

    if fair_value == 0 and actual_transfer_fee == 0: 
        status_label = "입력 대기 중"
    elif abs(diff) <= (fair_value * 0.05): 
        status_label = "⚖️ 적정가 (Fair Deal)"
    elif diff > 0: 
        status_label = f"⚠️ 고평가 (+{overpay_pct:.1f}%)"
    else: 
        status_label = f"💎 저평가/혜자 ({overpay_pct:.1f}%)"

    # ================= 이적 종합 평점 (Deal Rating / 10.00점 만점) 계산 =================
    if tm_market_value > 0 and actual_transfer_fee > 0:
        base_deal_score = 7.50
        val_score_delta = max(-3.5, min(2.5, -(overpay_pct / 20.0)))
        rating_delta = max(-0.8, min(1.0, (cur_rating - 7.00) * 1.5))
        age_delta = max(-1.0, min(0.8, (age_w - 1.00) * 8.0))
        risk_delta = (stage_w - 1.00) * 5.0 + (inj_w - 1.00) * 5.0 + (reg_w - 1.00) * 3.0 + (urg_w - 1.00) * 2.0
        
        final_deal_score = round(max(1.00, min(10.00, base_deal_score + val_score_delta + rating_delta + age_delta + risk_delta)), 2)
        
        if final_deal_score >= 9.00:
            deal_grade = "💎 S등급 (Masterclass Deal)"
            deal_badge_type = "success"
        elif final_deal_score >= 8.00:
            deal_grade = "🌟 A등급 (Excellent Deal)"
            deal_badge_type = "success"
        elif final_deal_score >= 7.00:
            deal_grade = "⚖️ B등급 (Solid / Fair Deal)"
            deal_badge_type = "info"
        elif final_deal_score >= 6.00:
            deal_grade = "⚠️ C등급 (Risky Deal)"
            deal_badge_type = "warning"
        else:
            deal_grade = "🚨 D등급 (Panic Buy / Overpaid)"
            deal_badge_type = "error"
    else:
        final_deal_score = 0.00
        deal_grade = "분석 대기 중"
        deal_badge_type = "info"

    with col2:
        st.subheader("📊 분석 결과 및 12대 세부 지표")
        display_name = player_name if player_name else "선수명 미입력"
        display_nat = f"({player_nat})" if player_nat else ""
        pos_short = main_position.split(" (")[0]
        ttype_short = transfer_type.split(" (")[0]
        reg_short = reg_status.split(" (")[0]
        urg_short = urgency_status.split(" (")[0]
        
        st.markdown(f"### **{display_name}** {display_nat} - `{pos_short}` 이적 평가")
        st.caption(f"📌 조항: **{ttype_short}** | 쿼터: **{reg_short}** | 필요도: **{urg_short}** | UCL: **{stage_w:.2f}**")
        
        r1_1, r1_2, r1_3, r1_4 = st.columns(4)
        r1_1.metric("1. 리그 난이도", f"{league_w:.2f}")
        r1_2.metric("2. 나이(에이징)", f"{age_w:.2f}")
        r1_3.metric("3. 영입 구단", f"{club_w:.2f}")
        r1_4.metric("4. 잔여 계약", f"{contract_w:.2f}")
        
        r2_1, r2_2, r2_3, r2_4 = st.columns(4)
        r2_1.metric("5. 포지션", f"{pos_w:.2f}")
        r2_2.metric("6. 멀티 능력", f"{vers_w:.2f}")
        r2_3.metric("7. 쿼터/HG", f"{reg_w:.2f}")
        r2_4.metric("8. 평점/실적", f"{opta_w:.2f}")
        
        r3_1, r3_2, r3_3, r3_4 = st.columns(4)
        r3_1.metric("9. 계약 조항", f"{ttype_w:.2f}")
        r3_2.metric("10. UCL 검증", f"{stage_w:.2f}")
        r3_3.metric("11. 메디컬/부상", f"{inj_w:.2f}")
        r3_4.metric("12. 영입 절박성", f"{urg_w:.2f}")
        
        st.divider()
        
        m_col1, m_col2 = st.columns(2)
        with m_col1:
            st.metric("산출된 적정 이적료", f"€{fair_value:,.1f}만")
            if fair_value > 0: st.caption(f"{format_currency_desc(fair_value)}")
        with m_col2:
            st.metric("실제 이적료", f"€{actual_transfer_fee:,.1f}만", delta=f"{diff:+,.1f}만 (€)" if actual_transfer_fee > 0 else None, delta_color="inverse")
            if actual_transfer_fee > 0: st.caption(f"{format_currency_desc(actual_transfer_fee)}")
        
        st.markdown("---")
        
        if final_deal_score > 0:
            st.markdown("#### 🏆 **이번 이적 종합 평점 (Deal Rating)**")
            ds_col1, ds_col2 = st.columns([1, 2])
            with ds_col1:
                st.metric("이적 평가 총점", f"★ {final_deal_score:.2f} / 10.00")
            with ds_col2:
                st.markdown(f"**종합 등급 판정**: `{deal_grade}`")
                if "고평가" in status_label:
                    st.caption(f"💡 시장 적정가 대비 초과 지출({diff_desc})로 인해 가성비 감점이 반영되었습니다.")
                elif "저평가" in status_label:
                    st.caption(f"💡 시장 적정가 대비 절감({diff_desc})으로 인해 높은 가성비 가산점이 반영되었습니다.")
                else:
                    st.caption("💡 적정 시세에 부합하는 합리적인 이적 거래입니다.")
            
            if deal_badge_type == "error":
                st.error(f"**진단 결과**: {status_label} - 적정가 대비 €{diff:,.1f}만 유로 더 지불됨 (총점 **{final_deal_score:.2f}점**)")
            elif deal_badge_type == "warning":
                st.warning(f"**진단 결과**: {status_label} (총점 **{final_deal_score:.2f}점**)")
            elif deal_badge_type == "info":
                st.info(f"**진단 결과**: {status_label} (총점 **{final_deal_score:.2f}점**)")
            else:
                st.success(f"**진단 결과**: {status_label} - 최고 수준의 영입 효율 (총점 **{final_deal_score:.2f}점**)")
        else:
            st.info("💡 시장 가치와 실제 이적료를 입력하면 종합 평점이 산출됩니다.")

        if player_name.strip() and (tm_market_value > 0 or actual_transfer_fee > 0):
            with st.expander("📋 커뮤니티 / 메모장 공유용 상세 요약 텍스트 (클릭하여 복사)", expanded=True):
                nat_text = f"({player_nat}, 만 {player_age}세)" if player_nat else f"(만 {player_age}세)"
                diff_text = f"적정가 대비 €{abs(diff):,.1f}만 유로({format_currency_desc(abs(diff))}) "
                diff_text += "더 지불됨" if diff > 0 else ("저렴하게 영입" if diff < 0 else "정확히 일치")
                
                summary_text = f"""⚽ [{season_val} 12대 지표 이적 분석] {player_name} {nat_text}
━━━━━━━━━━━━━━━━━━━━
▪️ 계약 조항: {ttype_short} ({ttype_w:.2f}) | 쿼터/HG: {reg_short} ({reg_w:.2f})
▪️ 포지션: {pos_short} (희소성 {pos_w:.2f} / 에이징 {age_w:.2f}) | 멀티: {versatility.split(" (")[0]}
▪️ 원소속 리그: {selling_league.split(" (")[0]} ({league_w:.2f}) ➔ 영입: {buying_club_tier.split(":")[0]} ({club_w:.2f})
▪️ 계약 기간: {remaining_contract.split(" (")[0]} ({contract_w:.2f}) | 필요도: {urg_short} ({urg_w:.2f})
▪️ UCL 검증: {big_stage.split(" (")[0]} ({stage_w:.2f}) | 부상내구성: {injury_status.split(" (")[0]} ({inj_w:.2f})
▪️ 지난 시즌 실적: {st.session_state['f_goals']}골 {st.session_state['f_assists']}도움 / 평점 {cur_rating:.2f} ({opta_w:.2f})
▪️ TM 시장가치: €{tm_market_value:,.0f}만 ({format_currency_desc(tm_market_value)})
▪️ 산출 적정가: €{fair_value:,.1f}만 ({format_currency_desc(fair_value)})
▪️ 실제 이적료: €{actual_transfer_fee:,.1f}만 ({format_currency_desc(actual_transfer_fee)})
━━━━━━━━━━━━━━━━━━━━
🏆 이번 이적 총 평점: ★ {final_deal_score:.2f} / 10.00점 ({deal_grade})
📊 종합 진단: {status_label} - {diff_text}
"""
                if player_notes.strip(): summary_text += f"📝 메모: {player_notes.strip()}\n"
                st.code(summary_text.strip(), language="text")

# ================= TAB 2: FotMob 시즌 성적 & 이적 예측 =================
with tab2:
    st.subheader("📱 FotMob 스타일 시즌 스탯 입력 & 이적 첫 시즌 성적 프로젝션")
    
    f_c1, f_c2, f_c3, f_c4 = st.columns(4)
    with f_c1: f_pos = st.selectbox("선수 포지션", ["⚽ 스트라이커 (ST/CF)", "⚡ 윙어 / 공미 (WG/CAM)", "🏃 중앙 미드필더 (CM/CDM)", "🛡️ 수비수 (CB/FB)"], index=3, key="f_tab_pos")
    with f_c2: f_from_l = st.selectbox("원소속 리그 (기록 기준)", list(LEAGUE_WEIGHTS.keys()), index=0, key="f_tab_from_l")
    with f_c3: f_to_l = st.selectbox("이적할 리그", list(LEAGUE_WEIGHTS.keys()), index=0, key="f_tab_to_l")
    with f_c4: f_target_mins = st.number_input("이적 팀 예상 출전 시간(분)", 450, 3420, 3036, 90, key="f_tab_target_mins")
    
    raw_l_factor = LEAGUE_WEIGHTS[f_from_l] / LEAGUE_WEIGHTS[f_to_l]
    if LEAGUE_WEIGHTS[f_to_l] > LEAGUE_WEIGHTS[f_from_l]:
        diff_level = LEAGUE_WEIGHTS[f_to_l] - LEAGUE_WEIGHTS[f_from_l]
        adapt_penalty = max(0.80, 1.0 - (diff_level * 0.45))
        adapt_desc = f"⚠️ 상위 리그 스텝업 적응 감가 적용 ({adapt_penalty:.2f}x)"
    else:
        adapt_penalty = 1.00
        adapt_desc = "✅ 동급/하위 리그 이적 (적응 페널티 없음)"
        
    final_l_factor = raw_l_factor * adapt_penalty
    
    st.divider()
    st.markdown("### 📥 FotMob 시즌 실제 기록 입력 (지난 시즌 스탯)")
    
    b1, b2, b3, b4 = st.columns(4)
    with b1: in_matches = st.number_input("출전 경기 (Matches)", 1, 60, value=st.session_state["f_matches"], key="in_matches_box")
    with b2: in_starts = st.number_input("선발 출전 (Starts)", 0, 60, value=st.session_state["f_starts"], key="in_starts_box")
    with b3: in_mins = st.number_input("출전 시간 (Minutes)", 90, 4500, value=st.session_state["f_mins"], key="in_mins_box")
    with b4: in_rating = st.number_input("FotMob 평균 평점", 5.0, 10.0, value=st.session_state["f_rating"], step=0.01, key="in_rating_box")
    
    st.session_state["f_mins"] = in_mins
    st.session_state["f_rating"] = in_rating
    st.session_state["f_matches"] = in_matches
    st.session_state["f_starts"] = in_starts

    base_p90 = in_mins / 90.0 if in_mins > 0 else 1.0
    target_p90 = f_target_mins / 90.0

    st.markdown("#### 1️⃣ 슈팅 및 득점 (Shooting & Goals)")
    s1, s2, s3, s4, s5 = st.columns(5)
    with s1: in_goals = st.number_input("득점 (Goals)", 0, 50, value=st.session_state["f_goals"], key="in_goals_box")
    with s2: in_xg = st.number_input("기대 득점 (xG)", 0.0, 50.0, value=st.session_state["f_xg"], step=0.01, key="in_xg_box")
    with s3: in_shots = st.number_input("총 슈팅 (Shots)", 0, 200, value=st.session_state["f_shots"], key="in_shots_box")
    with s4: in_sot = st.number_input("유효 슈팅 (On Target)", 0, 100, value=st.session_state["f_sot"], key="in_sot_box")
    with s5: in_pk_goals = st.number_input("PK 득점 (Penalty)", 0, 20, 0, key="in_pk_box")

    st.session_state["f_goals"] = in_goals
    st.session_state["f_xg"] = in_xg
    st.session_state["f_shots"] = in_shots
    st.session_state["f_sot"] = in_sot

    st.markdown("#### 2️⃣ 패스 및 기회 창출 (Passing & Creativity)")
    p1, p2, p3, p4, p5 = st.columns(5)
    with p1: in_assists = st.number_input("도움 (Assists)", 0, 30, value=st.session_state["f_assists"], key="in_assists_box")
    with p2: in_xa = st.number_input("기대 도움 (xA)", 0.0, 30.0, value=st.session_state["f_xa"], step=0.01, key="in_xa_box")
    with p3: in_chances = st.number_input("기회 창출 (Chances)", 0, 150, value=st.session_state["f_chances"], key="in_chances_box")
    with p4: in_big_chances = st.number_input("빅 찬스 메이킹", 0, 50, 1, key="in_bc_box")
    with p5: in_pass_pct = st.number_input("패스 성공률 (%)", 30.0, 100.0, 88.2, 0.1, key="in_pass_pct_box")

    st.session_state["f_assists"] = in_assists
    st.session_state["f_xa"] = in_xa
    st.session_state["f_chances"] = in_chances

    st.markdown("#### 3️⃣ 경합 및 수비 기여 (Duels & Defending)")
    d1, d2, d3, d4, d5 = st.columns(5)
    with d1: in_dribbles = st.number_input("성공한 드리블", 0, 100, value=st.session_state["f_dribbles"], key="in_dribbles_box")
    with d2: in_touches_box = st.number_input("박스 안 터치 (Box Touches)", 0, 300, value=st.session_state["f_touches_box"], key="in_touches_box")
    with d3: in_duels_pct = st.number_input("지상 경합 승률 (%)", 20.0, 100.0, 62.4, 0.1, key="in_duels_box")
    with d4: in_aerial_pct = st.number_input("공중볼 승률 (%)", 20.0, 100.0, 65.8, 0.1, key="in_aerial_box")
    with d5: in_tackles = st.number_input("태클 성공 (Tackles)", 0, 150, value=st.session_state["f_tackles"], key="in_tackles_box")

    st.session_state["f_dribbles"] = in_dribbles
    st.session_state["f_touches_box"] = in_touches_box
    st.session_state["f_tackles"] = in_tackles

    st.divider()

    # 이적 후 기대 스탯 예측 계산
    p90_xg = (in_xg / base_p90) * final_l_factor
    p90_xa = (in_xa / base_p90) * final_l_factor
    p90_shots = (in_shots / base_p90) * final_l_factor
    p90_sot = (in_sot / base_p90) * final_l_factor
    p90_chances = (in_chances / base_p90) * final_l_factor
    p90_dribbles = (in_dribbles / base_p90) * final_l_factor
    p90_box_touches = (in_touches_box / base_p90) * final_l_factor
    p90_tackles = (in_tackles / base_p90) * (1.0 / raw_l_factor)
    
    finishing_ratio = in_goals / in_xg if in_xg > 0 else 1.0
    
    proj_goals = round(p90_xg * target_p90 * finishing_ratio, 1)
    proj_xg = round(p90_xg * target_p90, 2)
    proj_assists = round(p90_xa * target_p90, 1)
    proj_xa = round(p90_xa * target_p90, 2)
    proj_shots = round(p90_shots * target_p90, 0)
    proj_sot = round(p90_sot * target_p90, 0)
    proj_chances = round(p90_chances * target_p90, 0)
    proj_dribbles = round(p90_dribbles * target_p90, 0)
    proj_box_touches = round(p90_box_touches * target_p90, 0)
    proj_tackles = round(p90_tackles * target_p90, 0)
    
    proj_rating = round(max(6.0, in_rating - (1.0 - final_l_factor) * 0.9), 2)

    # 1) 상단 5대 핵심 지표 카드
    st.markdown(f"### 🎯 **FotMob 스타일 이적 첫 시즌 성적 예측 리포트**")
    st.caption(f"이적 환경: **{f_from_l.split(' ')[1]}** ➔ **{f_to_l.split(' ')[1]}** | 리그 난이도: **{raw_l_factor:.2f}x** | {adapt_desc} | 최종 환산 계수: **{final_l_factor:.2f}x**")
    
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("예상 평점 (Rating)", f"★ {proj_rating:.2f}", delta=f"{proj_rating - in_rating:+.2f}")
    m2.metric("예상 득점 (xG)", f"{proj_goals:.0f} 골", delta=f"xG {proj_xg:.2f}")
    m3.metric("예상 도움 (xA)", f"{proj_assists:.0f} 도움", delta=f"xA {proj_xa:.2f}")
    m4.metric("예상 공격포인트", f"{proj_goals + proj_assists:.0f} P", delta=f"{proj_goals:.0f}G + {proj_assists:.0f}A")
    m5.metric("예상 슈팅 (유효)", f"{int(proj_shots)} 회", delta=f"유효 {int(proj_sot)}회")

    st.markdown("<br>", unsafe_allow_html=True)
    
    # 2) 직전 시즌 vs 이적 첫 시즌 1:1 세부 스탯 비교 테이블
    st.markdown("#### 📊 **직전 시즌 실제 기록 vs 이적 첫 시즌 예측 데이터 비교표**")
    df_compare = pd.DataFrame({
        "FotMob 스탯 항목": [
            "출전 경기 / 선발 (Matches / Starts)",
            "출전 시간 (Minutes)",
            "득점 (Goals)",
            "기대 득점 (xG)",
            "도움 (Assists)",
            "기대 도움 (xA)",
            "총 슈팅 / 유효 슈팅 (Shots / SoT)",
            "90분당 슈팅 수 (Shots/90)",
            "시즌 기회 창출 (Chances Created)",
            "성공한 드리블 (Successful Dribbles)",
            "박스 안 터치 (Box Touches)",
            "시즌 태클 성공 (Tackles Won)",
            "FotMob 평균 평점 (Rating)"
        ],
        f"직전 시즌 실제치 ({f_from_l.split(' ')[1]})": [
            f"{in_matches}경기 ({in_starts}선발)",
            f"{in_mins:,} 분",
            f"{in_goals} 골",
            f"{in_xg:.2f}",
            f"{in_assists} 도움",
            f"{in_xa:.2f}",
            f"{in_shots}회 ({in_sot}회)",
            f"{(in_shots/base_p90):.2f} 회",
            f"{in_chances} 회",
            f"{in_dribbles} 회",
            f"{in_touches_box} 회",
            f"{in_tackles} 회",
            f"★ {in_rating:.2f}"
        ],
        f"이적 첫 시즌 예측치 ({f_to_l.split(' ')[1]})": [
            f"약 {target_p90:.0f}경기 상당",
            f"{f_target_mins:,} 분",
            f"{proj_goals:.1f} 골",
            f"{proj_xg:.2f}",
            f"{proj_assists:.1f} 도움",
            f"{proj_xa:.2f}",
            f"{int(proj_shots)}회 ({int(proj_sot)}회)",
            f"{p90_shots:.2f} 회",
            f"{int(proj_chances)} 회",
            f"{int(proj_dribbles)} 회",
            f"{int(proj_box_touches)} 회",
            f"{int(proj_tackles)} 회",
            f"★ {proj_rating:.2f}"
        ]
    })
    st.table(df_compare)

    # 3) 데이터 분석 스카우팅 총평 리포트
    st.info(f"""
    💡 **스카우팅 데이터 인사이트**:
    - **리그 난이도 격차 & 적응 모델**: '{f_from_l.split(' ')[1]}'에서 '{f_to_l.split(' ')[1]}'로 이적 시 발생하는 수비 압박 템포 차이(최종 환산 계수: **{final_l_factor:.2f}x**)가 적용되었습니다.
    - **기대치 분석**: 예상 출전 시간 **{f_target_mins:,}분** 기준, 첫 시즌 약 **{proj_goals:.0f}골 {proj_assists:.0f}도움 (공격포인트 {proj_goals+proj_assists:.0f}개)** 및 평균 평점 **★{proj_rating:.2f}** 수준의 안착이 합리적으로 예측됩니다.
    """)

    st.markdown("---")
    
    # 4) 구글 시트 저장 섹션 (37개 열 전용)
    display_pname = player_name.strip() if player_name.strip() else "선수명 미입력"
    st.markdown(f"#### 💾 **'{display_pname}'** 선수의 37대 전체 데이터 구글 시트 저장")
    
    if st.button("💾 FotMob 시즌 성적 & 이적 예측 데이터 구글 시트에 저장하기 (37개 전체 항목)", type="primary", use_container_width=True, key="save_btn_tab2"):
        if not player_name.strip():
            st.warning("⚠️ 선수 이름을 [💰 적정 이적료 평가] 탭에 먼저 입력해 주세요.")
        else:
            with st.spinner("구글 시트에 37개 세부 지표를 기록 중입니다..."):
                contract_desc = remaining_contract.split(" (")[0]
                nat_str = player_nat if player_nat.strip() else "미상"
                detailed_notes = f"[{ttype_short}|{reg_short}|{urg_short}|UCL:{stage_w:.2f}|메디컬:{inj_w:.2f}] 계약:{contract_desc}"
                if player_notes.strip():
                    detailed_notes += f" | {player_notes.strip()}"
                    
                payload = {
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "season": season_val,
                    "name": player_name,
                    "nat": nat_str,
                    "age": int(player_age),
                    "pos": pos_short,
                    "from_league": selling_league.split(" (")[0],
                    "buying_tier": buying_club_tier.split(":")[0],
                    "transfer_type": ttype_short,
                    "tm_val": float(tm_market_value),
                    "fee": float(actual_transfer_fee),
                    "fair_val": round(fair_value, 1),
                    "diff": round(diff, 1),
                    "status": status_label,
                    "deal_score": float(final_deal_score), # O열 독립 평점
                    
                    # FotMob 이전 시즌 실제 스탯 (13개)
                    "prev_matches": int(st.session_state["f_matches"]),
                    "prev_mins": int(st.session_state["f_mins"]),
                    "prev_goals": int(st.session_state["f_goals"]),
                    "prev_xg": float(st.session_state["f_xg"]),
                    "prev_assists": int(st.session_state["f_assists"]),
                    "prev_xa": float(st.session_state["f_xa"]),
                    "prev_shots": int(st.session_state["f_shots"]),
                    "prev_sot": int(st.session_state["f_sot"]),
                    "prev_chances": int(st.session_state["f_chances"]),
                    "prev_dribbles": int(st.session_state["f_dribbles"]),
                    "prev_touches_box": int(st.session_state["f_touches_box"]),
                    "prev_tackles": int(st.session_state["f_tackles"]),
                    "prev_rating": float(st.session_state["f_rating"]),
                    
                    # FotMob 이적 첫 시즌 예측 스탯 (8개)
                    "to_league": f_to_l.split(" (")[0],
                    "proj_mins": int(f_target_mins),
                    "proj_goals": float(proj_goals),
                    "proj_xg": float(proj_xg),
                    "proj_assists": float(proj_assists),
                    "proj_xa": float(proj_xa),
                    "proj_shots": float(proj_shots),
                    "proj_rating": float(proj_rating),
                    
                    "notes": detailed_notes
                }
                
                try:
                    res = requests.post(
                        GOOGLE_SHEET_WEBAPP_URL, 
                        data=json.dumps(payload), 
                        headers={"Content-Type": "text/plain;charset=utf-8"}, 
                        timeout=12, 
                        allow_redirects=True
                    )
                    if res.status_code in [200, 302]:
                        st.session_state["last_saved_msg"] = f"✅ '{player_name}' 선수의 37대 전체 데이터(이적평점 포함)가 구글 시트에 성공적으로 저장되었습니다!"
                        st.session_state["form_key_id"] += 1
                        st.rerun()
                    else:
                        st.error(f"⚠️ 저장 실패 (응답 코드: {res.status_code})")
                except Exception as e:
                    st.error(f"⚠️ 저장 오류: {e}")

# ================= TAB 3: 과거 유사 이적 사례 비교 (Comps TOP 10) =================
with tab3:
    st.subheader("🔍 과거 유사 이적 사례 검색 및 벤치마크 비교 (Comps TOP 10)")
    st.caption("구글 시트에 누적된 이전 이적 데이터 중 이적료, 총 평점, 평가율(고평가/저평가), 출발 리그가 가장 유사한 과거 사례 최대 10건을 자동으로 매칭합니다.")
    
    c_in1, c_in2, c_in3, c_in4, c_in5 = st.columns(5)
    with c_in1:
        target_fee = st.number_input("비교 기준 이적료 (만 €)", min_value=0, value=int(actual_transfer_fee) if actual_transfer_fee > 0 else 5000, step=100, key="comps_fee")
    with c_in2:
        target_score = st.number_input("비교 기준 이적 평점", min_value=1.00, max_value=10.00, value=float(final_deal_score) if final_deal_score > 0 else 7.50, step=0.1, key="comps_score")
    with c_in3:
        target_overpay = st.number_input("비교 기준 평가율 (%)", min_value=-100.0, max_value=200.0, value=float(overpay_pct), step=1.0, key="comps_overpay")
    with c_in4:
        pos_filter = st.selectbox("포지션 필터", ["전체 포지션", "스트라이커 (ST/CF)", "윙어/공미 (WG/CAM)", "미드필더 (CM/CDM)", "수비수 (CB/FB/WB)", "골키퍼 (GK)"], index=0, key="comps_pos_filter")
    with c_in5:
        league_filter = st.selectbox("원소속 리그 필터", ["전체 리그"] + list(LEAGUE_WEIGHTS.keys()), index=0, key="comps_league_filter")

    st.markdown("---")

    @st.cache_data(ttl=15)
    def fetch_sheet_history():
        try:
            df = pd.read_csv(SHEET_CSV_URL)
            return df
        except Exception:
            return pd.DataFrame()

    history_df = fetch_sheet_history()

    if history_df.empty or len(history_df) == 0:
        st.info("💡 **아직 구글 시트에 누적된 과거 이적 데이터가 없습니다.**\n\n1번 및 2번 탭에서 선수 데이터를 저장해 나가시면, 자동으로 이곳에 가장 유사한 과거 이적 사례 TOP 10이 순위별로 나타나게 됩니다.")
    else:
        try:
            valid_rows = []
            for idx, row in history_df.iterrows():
                try:
                    p_name = str(row.get("선수명", f"선수 {idx+1}"))
                    p_fee = float(row.get("실제이적료(만€)", 0))
                    p_fair = float(row.get("산출적정가(만€)", 0))
                    p_pos = str(row.get("포지션", "기타"))
                    p_league = str(row.get("원소속리그", "기타"))
                    p_season = str(row.get("이적시즌", "26/27"))
                    
                    # O열의 독립된 '이적평점' 직접 가져오기
                    p_score = float(row.get("이적평점", 7.50))
                    p_overpay = ((p_fee - p_fair) / p_fair * 100) if p_fair > 0 else 0.0
                    notes_str = str(row.get("스카우팅메모", ""))
                    
                    # 1) 포지션 필터링
                    if pos_filter != "전체 포지션":
                        f_pos_key = pos_filter.split(" (")[0]
                        if f_pos_key not in p_pos and p_pos not in pos_filter:
                            continue
                    
                    # 2) 리그 필터링
                    if league_filter != "전체 리그":
                        f_l_key = league_filter.split(" (")[0]
                        if f_l_key not in p_league:
                            continue

                    # 3) 4대 요소 복합 유사도 점수 계산
                    fee_diff_norm = abs(p_fee - target_fee) / (max(target_fee, 1000) * 1.5)
                    score_diff_norm = abs(p_score - target_score) / 5.0
                    overpay_diff_norm = abs(p_overpay - target_overpay) / 50.0
                    
                    target_l_w = LEAGUE_WEIGHTS.get(selling_league, 1.0)
                    row_l_w = 0.80
                    for l_k, l_v in LEAGUE_WEIGHTS.items():
                        if p_league in l_k:
                            row_l_w = l_v
                            break
                    league_diff_norm = abs(target_l_w - row_l_w) / 0.70

                    total_dist = (fee_diff_norm * 0.30) + (score_diff_norm * 0.25) + (overpay_diff_norm * 0.25) + (league_diff_norm * 0.20)
                    sim_pct = max(0.0, round((1.0 - total_dist) * 100, 1))
                    
                    valid_rows.append({
                        "시즌": p_season,
                        "선수명": p_name,
                        "포지션": p_pos,
                        "원소속리그": p_league,
                        "실제이적료(만€)": p_fee,
                        "산출적정가(만€)": p_fair,
                        "평가율(%)": round(p_overpay, 1),
                        "이적평점": round(p_score, 2),
                        "유사도(%)": sim_pct,
                        "스카우팅메모": notes_str
                    })
                except Exception:
                    continue

            if len(valid_rows) > 0:
                match_df = pd.DataFrame(valid_rows).sort_values(by="유사도(%)", ascending=False).head(10)
                
                st.markdown(f"### 🎯 **가장 유사한 과거 이적 사례 TOP 3 하이라이트**")
                top_cols = st.columns(min(3, len(match_df)))
                
                for i, (_, match_row) in enumerate(match_df.head(3).iterrows()):
                    with top_cols[i]:
                        st.markdown(f"#### **{i+1}위. {match_row['선수명']}** ({match_row['시즌']})")
                        st.caption(f"📌 포지션: `{match_row['포지션']}` | 리그: `{match_row['원소속리그']}`")
                        st.metric("매칭 유사도", f"{match_row['유사도(%)']}%")
                        st.write(f"- **실제 이적료**: €{match_row['실제이적료(만€)']:,.0f}만 ({format_currency_desc(match_row['실제이적료(만€)'])})")
                        st.write(f"- **이적 총 평점**: ★ {match_row['이적평점']:.2f} / 10.00")
                        st.write(f"- **평가율**: `{match_row['평가율(%)']:+.1f}%`")
                
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("#### 📋 **유사 이적 사례 TOP 10 전체 세부 비교 테이블**")
                st.dataframe(
                    match_df[[
                        "유사도(%)", "시즌", "선수명", "포지션", "원소속리그", 
                        "실제이적료(만€)", "산출적정가(만€)", "평가율(%)", "이적평점", "스카우팅메모"
                    ]], 
                    use_container_width=True
                )
            else:
                st.info("💡 선택하신 포지션 또는 리그 필터 조건에 일치하는 과거 이적 데이터가 없습니다.")
        except Exception as e:
            st.error(f"⚠️ 데이터 비교 중 오류: {e}")
