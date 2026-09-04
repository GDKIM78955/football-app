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

@st.cache_data(ttl=0)
def fetch_sheet_history():
    try:
        csv_url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv&gid=0"
        df = pd.read_csv(csv_url)
        if not df.empty: return df
    except Exception: pass
    return pd.DataFrame()

@st.cache_data(ttl=0)
def fetch_validation_data():
    try:
        val_url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv&gid=15389686"
        df = pd.read_csv(val_url)
        if not df.empty: return df
    except Exception: pass
    return pd.DataFrame()

history_df = fetch_sheet_history()
validation_df = fetch_validation_data()

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
    "Tier 1: 엘리트 메가클럽 (레알, 맨시티, 바이에른 등)": 1.05,
    "Tier 2: 빅클럽 (아스날, 리버풀 등)": 1.02,
    "Tier 3: 중상위권 클럽 (토트넘 등)": 1.00,
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

rate_krw = 1500
def format_currency_desc(eur_man_euro):
    if eur_man_euro <= 0: return "₩0억"
    total_eur = eur_man_euro * 10000
    krw_eok = (total_eur * rate_krw) / 100000000.0
    return f"약 {krw_eok:,.1f}억원"

# 6개 탭 구조 정의
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "💰 적정 이적료 평가", 
    "📱 FotMob 시즌 성적 & 이적 예측",
    "🔍 과거 유사 이적 사례 비교",
    "🎯 이적 첫 시즌 실제 성적 검증",
    "👥 신규 vs 과거 벤치마크",
    "🏆 구단/리그별 종합 결산"
])

# ================= TAB 1: 적정 이적료 평가 (원본 백업 스타일 그대로 복원) =================
with tab1:
    if st.session_state["last_saved_msg"]:
        st.success(st.session_state["last_saved_msg"])
        st.session_state["last_saved_msg"] = None

    st.subheader("💰 프로페셔널 적정 이적료 평가 시스템 (12대 가중치)")

    trade_type_choice = st.radio("거래 유형", ["🔵 영입 (IN)", "🔴 방출 (OUT)"], horizontal=True, key="t_type")
    is_out_trade = "방출" in trade_type_choice
    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("##### 👤 선수 기본 정보")
        season_val = st.selectbox("이적 시즌", ["26/27 여름 (Summer)", "26/27 겨울 (Winter)", "기타"], key="p_season")
        player_name = st.text_input("선수 이름", value="손흥민", key="p_name")
        player_nat = st.text_input("국적", value="대한민국", key="p_nat")
        player_age = st.number_input("만 나이", min_value=15, max_value=45, value=28, key="p_age")
        main_position = st.selectbox("주 포지션", list(POSITION_WEIGHTS.keys()), index=0, key="p_pos")
        selling_league = st.selectbox("원소속 리그", list(LEAGUE_WEIGHTS.keys()), index=0, key="p_league")
        buying_club_tier = st.selectbox("영입구단 티어", list(CLUB_TIERS.keys()), index=1, key="p_tier")
        in_from_team = st.text_input("원소속팀명 (보내는 팀)", value="토트넘 홋스퍼", key="p_from_team")
        in_to_team = st.text_input("이적팀명 (영입 구단)", value="바이에른 뮌헨", key="p_to_team")
        to_league_choice = st.selectbox("이적팀 리그", list(LEAGUE_WEIGHTS.keys()), index=0, key="p_to_league")

    with col2:
        st.markdown("##### 💼 계약 및 시장 가치")
        tm_market_value = st.number_input("TM 시장가치 (만€)", min_value=0, value=5000, step=100, key="p_tm")
        actual_transfer_fee = st.number_input("실제 이적료 (만€)", min_value=0, value=5500, step=100, key="p_fee")
        weekly_wage_in = st.number_input("주급 (만€)", min_value=0.0, value=0.0, step=0.5, key="p_wage")
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
    vers_w = 1.00
    reg_w = REGISTRATION_WEIGHTS[reg_status]
    opta_w = 1.00
    ttype_w = TRANSFER_TYPE_WEIGHTS[transfer_type]
    stage_w = BIG_STAGE_WEIGHTS[big_stage]
    inj_w = INJURY_WEIGHTS[injury_status]
    urg_w = URGENCY_WEIGHTS[urgency_status]

    is_winter = "겨울" in season_val
    season_factor = 1.10 if is_winter else 1.00

    base_calc_val = tm_market_value * league_w * age_w * club_w * contract_w * pos_w * vers_w * reg_w * opta_w * ttype_w * stage_w * inj_w * urg_w
    fair_value = base_calc_val * season_factor
    diff = actual_transfer_fee - fair_value
    overpay_pct = (diff / fair_value) * 100 if fair_value > 0 else 0.0

    base_deal_score = 7.50
    score_multiplier = 1.0 if is_out_trade else -1.0
    val_score_delta = max(-3.5, min(2.5, score_multiplier * (overpay_pct / 20.0)))
    final_deal_score = round(max(1.00, min(10.00, base_deal_score + val_score_delta)), 2)

    status_label = "⚖️ 적정가 (Fair Deal)" if abs(overpay_pct) <= 5.0 else (f"⚠️ 오버페이 (+{overpay_pct:.1f}%)" if diff > 0 else f"💎 혜자딜 ({overpay_pct:.1f}%)")

    st.markdown("---")
    st.subheader("📊 분석 결과 및 핵심 지표")

    res_c1, res_c2, res_c3, res_c4 = st.columns(4)
    res_c1.metric("산출 적정가", f"€{fair_value:,.1f}만", format_currency_desc(fair_value))
    res_c2.metric("실제 거래액", f"€{actual_transfer_fee:,.1f}만", delta=f"{diff:+,.1f}만 €")
    res_c3.metric("평가율 / 진단", f"{overpay_pct:+.1f}%", delta=status_label.split(" ")[0])
    res_c4.metric("이적 거래 평점", f"★ {final_deal_score:.2f}")

    st.markdown("---")

    viz_col1, viz_col2 = st.columns([1, 1], gap="large")

    with viz_col1:
        st.markdown("##### 📊 선수 12대 스카우팅 육각형 레이더")
        radar_categories = ['리그 템포', '나이/포텐', '구단 스케일', '계약 상태', '포지션 희소성', 'UCL/빅매치', '부상 내구성', '영입 절박성']
        radar_values = [league_w * 100, age_w * 100, club_w * 100, contract_w * 100, pos_w * 100, stage_w * 100, inj_w * 100, urg_w * 100]
        
        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(
            r=radar_values + [radar_values[0]],
            theta=radar_categories + [radar_categories[0]],
            fill='toself',
            fillcolor='rgba(31, 119, 180, 0.3)' if not is_out_trade else 'rgba(214, 39, 40, 0.3)',
            line=dict(color='#1f77b4' if not is_out_trade else '#d62728', width=2),
            name=player_name if player_name else "선수"
        ))
        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[50, 115])),
            showlegend=False,
            margin=dict(l=20, r=20, t=20, b=20),
            height=320
        )
        st.plotly_chart(fig, use_container_width=True)

    with viz_col2:
        st.markdown("##### 🔍 12대 세부 가중치 적용 현황")
        total_multiplier = league_w * age_w * club_w * contract_w * pos_w * vers_w * reg_w * opta_w * ttype_w * stage_w * inj_w * urg_w * season_factor
        df_weights_live = pd.DataFrame({
            "항목": [
                "① 원소속 리그 템포", "② 포지션별 나이", "③ 영입 구단 규모",
                "④ 잔여 계약 기간", "⑤ 포지션 희소성", "⑥ 멀티 포지션",
                "⑦ 쿼터(HG)", "⑧ FotMob 평점", "⑨ 이적 형태",
                "⑩ UCL/빅매치", "⑪ 부상 내구성", "⑫ 영입 절박성",
                "❄️ 겨울 프리미엄", "🎯 [종합] 누적 배율"
            ],
            "조건": [
                selling_league.split(" (")[0], f"만 {player_age}세", buying_club_tier.split(":")[0],
                remaining_contract.split(" (")[0], main_position.split(" (")[0], "단일",
                reg_status.split(" (")[0], "★6.50", transfer_type.split(" (")[0],
                big_stage.split(" (")[0], injury_status.split(" (")[0], urgency_status.split(" (")[0],
                "겨울 +10%" if is_winter else "여름 표준", "총 배율 합산"
            ],
            "배율": [
                f"{league_w:.2f}x", f"{age_w:.2f}x", f"{club_w:.2f}x", f"{contract_w:.2f}x",
                f"{pos_w:.2f}x", f"{vers_w:.2f}x", f"{reg_w:.2f}x", f"{opta_w:.2f}x",
                f"{ttype_w:.2f}x", f"{stage_w:.2f}x", f"{inj_w:.2f}x", f"{urg_w:.2f}x",
                f"{season_factor:.2f}x", f"✨ {total_multiplier:.3f}x"
            ]
        })
        st.dataframe(df_weights_live, use_container_width=True, height=320)

    st.markdown("---")

    # 구글 시트 저장 버튼 로직
    btn_label = f"💾 '{player_name}' 데이터 구글 시트에 바로 저장하기"
    if st.button(btn_label, type="primary", use_container_width=True):
        if not player_name.strip():
            st.warning("⚠️ 선수 이름을 입력해 주세요.")
        else:
            with st.spinner("구글 시트에 54개 항목 데이터를 기록 중입니다..."):
                pos_short = main_position.split(" (")[0]
                contract_desc = remaining_contract.split(" (")[0]
                detailed_notes = f"[{'방출' if is_out_trade else '영입'}|계약:{contract_desc}]"

                payload = {
                    "action": "save_all",
                    "row_index": None,
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "season": season_val,
                    "name": player_name,
                    "nat": player_nat if player_nat.strip() else "미상",
                    "age": int(player_age),
                    "pos": pos_short,
                    "from_league": selling_league.split(" (")[0],
                    "buying_tier": buying_club_tier.split(":")[0],
                    "transfer_type": transfer_type.split(" (")[0],
                    "tm_val": float(tm_market_value),
                    "fee": float(actual_transfer_fee),
                    "fair_val": round(fair_value, 1),
                    "diff": round(diff, 1),
                    "status": status_label,
                    "deal_score": float(final_deal_score),
                    "prev_matches": 1,
                    "prev_mins": 90,
                    "prev_goals": 0,
                    "prev_xg": 0.0,
                    "prev_assists": 0,
                    "prev_xa": 0.0,
                    "prev_shots": 0,
                    "prev_sot": 0,
                    "prev_chances": 0,
                    "prev_dribbles": 0,
                    "prev_touches_box": 0,
                    "prev_tackles": 0,
                    "prev_rating": 6.5,
                    "to_league": to_league_choice.split(" (")[0],
                    "proj_mins": 3000,
                    "proj_goals": 0.0,
                    "proj_xg": 0.0,
                    "proj_assists": 0.0,
                    "proj_xa": 0.0,
                    "proj_shots": 0.0,
                    "proj_rating": 7.0,
                    "notes": detailed_notes,
                    "from_team": in_from_team.strip(),
                    "to_team": in_to_team.strip(),
                    "to_league_name": to_league_choice.split(" (")[0],
                    "trade_type": "OUT" if is_out_trade else "IN",
                    "weekly_wage": float(weekly_wage_in),
                    "gk_saves": 0,
                    "gk_conceded": 0,
                    "gk_prevented": 0.0,
                    "gk_cs": 0,
                    "gk_errors": 0,
                    "gk_claims": 0,
                    "prev_starts": 0,
                    "big_chances": 0,
                    "pk_goals": 0,
                    "pass_pct": 0.0,
                    "duels_pct": 0.0,
                    "aerial_pct": 0.0
                }
                
                try:
                    res = requests.post(
                        GOOGLE_SHEET_WEBAPP_URL, 
                        data=json.dumps(payload), 
                        headers={"Content-Type": "text/plain;charset=utf-8"}, 
                        timeout=30, 
                        allow_redirects=True
                    )
                    res_json = res.json()
                    if res.status_code in [200, 302] and res_json.get("status") == "success":
                        st.session_state["last_saved_msg"] = f"✅ '{player_name}' 선수의 데이터가 구글 시트(메인기록부)에 성공적으로 저장되었습니다!"
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error(f"⚠️ 저장 실패: {res_json.get('message', '통신 오류')}")
                except Exception as e:
                    st.error(f"⚠️ 저장 오류: {e}")

# 나머지 탭 영역 (2~6번 탭 유지)
with tab2: st.subheader("📱 FotMob 시즌 성적 & 이적 예측")
with tab3: st.subheader("🔍 과거 유사 이적 사례 비교")
with tab4: st.subheader("🎯 이적 첫 시즌 실제 성적 검증")
with tab5: st.subheader("👥 신규 vs 과거 벤치마크")
with tab6: st.subheader("🏆 구단/리그별 종합 결산")
