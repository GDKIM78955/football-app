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

if "last_saved_msg" not in st.session_state:
    st.session_state["last_saved_msg"] = None

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
    "Tier 1: 엘리트 메가클럽 (레알, 맨시티 등)": 1.05,
    "Tier 2: 빅클럽 (아스날, 리버풀 등)": 1.02,
    "Tier 3: 중상위권 클럽 (토트넘 등)": 1.00,
    "Tier 4: 중하위권 클럽": 0.98,
    "Tier 5: 소형/셀링 클럽": 0.95
}

CONTRACT_WEIGHTS = {
    "6개월 이하 (-20%)": 0.80,
    "1년 남음 (-8%)": 0.92,
    "2년 남음 (기준)": 1.00,
    "3년 남음 (+2%)": 1.02,
    "4년 이상 (+4%)": 1.04
}

POSITION_WEIGHTS = {
    "스트라이커 / 센터포워드 (ST/CF, +2%)": 1.02,
    "윙어 / 공미 (WG/CAM, +1%)": 1.01,
    "중미 / 수미 (CM/CDM, 기준)": 1.00,
    "풀백 / 윙백 (RB/LB/WB, -1%)": 0.99,
    "센터백 (CB, -1%)": 0.99,
    "골키퍼 (GK, -3%)": 0.97
}

REGISTRATION_WEIGHTS = {
    "일반 (기준)": 1.00,
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿 홈그로운 (+4%)": 1.04,
    "🏛️ 구단 유스 (+2%)": 1.02,
    "🇪🇸🇮🇹 비EU (-2%)": 0.98
}

TRANSFER_TYPE_WEIGHTS = {
    "일반 완전 이적 (기준)": 1.00,
    "단순 1년 임대 (20% 환산)": 0.20,
    "임대 후 의무 영입 (+2%)": 1.02,
    "바이백 조항 (-5%)": 0.95,
    "FA 자유계약": 1.00
}

BIG_STAGE_WEIGHTS = {
    "🌟 UCL 16강+ / A매치 주전 (+3%)": 1.03,
    "🔥 UEL/UECL / 국대 주전 (+1%)": 1.01,
    "⚖️ 경험 없음 (기준)": 1.00
}

INJURY_WEIGHTS = {
    "🛡️ 철강왕 (+1%)": 1.01,
    "⚖️ 일반적 수준 (기준)": 1.00,
    "⚠️ 잦은 잔부상 (-3%)": 0.97,
    "🚨 장기 부상 이력 (-6%)": 0.94
}

URGENCY_WEIGHTS = {
    "⚖️ 일반 보강 (기준)": 1.00,
    "🔥 최우선 타겟 (+4%)": 1.04,
    "🚨 패닉바이 (+8%)": 1.08
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

# ================= TAB 1: 적정 이적료 평가 =================
with tab1:
    if st.session_state["last_saved_msg"]:
        st.success(st.session_state["last_saved_msg"])
        st.session_state["last_saved_msg"] = None

    col_left, col_right = st.columns([1.1, 1.4], gap="large")

    with col_left:
        st.markdown("#### 📝 선수 프로필 & 계약 조건 입력")
        trade_type_choice = st.radio("거래 유형", ["🔵 영입 (IN)", "🔴 방출 (OUT)"], horizontal=True, key="t_type")
        is_out_trade = "방출" in trade_type_choice
        
        # 💡 [압축 레이아웃] 이적 시즌, 선수 이름, 국적을 한 행에 나란히 배치
        r1_c1, r1_c2, r1_c3 = st.columns([1.1, 1.2, 0.9])
        with r1_c1:
            season_val = st.selectbox("이적 시즌", ["26/27 여름", "26/27 겨울", "기타"], key="p_season")
        with r1_c2:
            player_name = st.text_input("선수 이름", value="손흥민", key="p_name")
        with r1_c3:
            player_nat = st.text_input("국적", value="대한민국", key="p_nat")

        # 💡 [압축 레이아웃] 나이와 포지션을 한 행에 배치
        r2_c1, r2_c2 = st.columns([0.8, 2.2])
        with r2_c1:
            player_age = st.number_input("만 나이", min_value=15, max_value=45, value=28, key="p_age")
        with r2_c2:
            main_position = st.selectbox("주 포지션", list(POSITION_WEIGHTS.keys()), index=0, key="p_pos")

        # 💡 [압축 레이아웃] 원소속 리그와 영입 구단 티어
        r3_c1, r3_c2 = st.columns(2)
        with r3_c1:
            selling_league = st.selectbox("원소속 리그", list(LEAGUE_WEIGHTS.keys()), index=0, key="p_league")
        with r3_c2:
            buying_club_tier = st.selectbox("영입구단 티어", list(CLUB_TIERS.keys()), index=1, key="p_tier")

        # 💡 [압축 레이아웃] 원소속팀명과 이적팀명
        r4_c1, r4_c2 = st.columns(2)
        with r4_c1:
            in_from_team = st.text_input("원소속팀명", value="토트넘 홋스퍼", key="p_from_team")
        with r4_c2:
            in_to_team = st.text_input("이적팀명", value="바이에른 뮌헨", key="p_to_team")

        # 💡 [압축 레이아웃] 이적팀 리그와 TM 시장가치
        r5_c1, r5_c2 = st.columns(2)
        with r5_c1:
            to_league_choice = st.selectbox("이적팀 리그", list(LEAGUE_WEIGHTS.keys()), index=0, key="p_to_league")
        with r5_c2:
            tm_market_value = st.number_input("TM 시장가치 (만€)", min_value=0, value=5000, step=100, key="p_tm")

        # 💡 [압축 레이아웃] 실제 이적료와 주급
        r6_c1, r6_c2 = st.columns(2)
        with r6_c1:
            actual_transfer_fee = st.number_input("실제 이적료 (만€)", min_value=0, value=5500, step=100, key="p_fee")
        with r6_c2:
            weekly_wage_in = st.number_input("주급 (만€)", min_value=0.0, value=0.0, step=0.5, key="p_wage")

        # 💡 [압축 레이아웃] 잔여 계약 기간과 이적 형태
        r7_c1, r7_c2 = st.columns(2)
        with r7_c1:
            remaining_contract = st.selectbox("잔여 계약 기간", list(CONTRACT_WEIGHTS.keys()), index=2, key="p_con")
        with r7_c2:
            transfer_type = st.selectbox("이적 형태", list(TRANSFER_TYPE_WEIGHTS.keys()), index=0, key="p_ttype")

        # 💡 [압축 레이아웃] 쿼터, 부상, UCL 검증, 절박성 (2개씩 짝지어 배치)
        r8_c1, r8_c2 = st.columns(2)
        with r8_c1:
            reg_status = st.selectbox("스쿼드 쿼터 상태", list(REGISTRATION_WEIGHTS.keys()), index=0, key="p_reg")
            injury_status = st.selectbox("부상 내구성", list(INJURY_WEIGHTS.keys()), index=1, key="p_inj")
        with r8_c2:
            big_stage = st.selectbox("UCL/빅매치 검증도", list(BIG_STAGE_WEIGHTS.keys()), index=0, key="p_stage")
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

    with col_right:
        st.markdown("#### 📊 분석 결과 및 스카우팅 시각화")
        
        # 1. 핵심 지표 카드 4개
        res_c1, res_c2, res_c3, res_c4 = st.columns(4)
        res_c1.metric("산출 적정가", f"€{fair_value:,.1f}만", format_currency_desc(fair_value))
        res_c2.metric("실제 거래액", f"€{actual_transfer_fee:,.1f}만", delta=f"{diff:+,.1f}만 €")
        res_c3.metric("평가율 / 진단", f"{overpay_pct:+.1f}%", delta=status_label.split(" ")[0])
        res_c4.metric("이적 거래 평점", f"★ {final_deal_score:.2f}")

        st.markdown("---")

        # 2. 육각형 레이더 차트
        st.markdown("##### 📈 12대 스카우팅 육각형 레이더 차트")
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
            margin=dict(l=20, r=20, t=10, b=10),
            height=260
        )
        st.plotly_chart(fig, use_container_width=True)

        # 3. 12대 가중치 세부 적용 현황표 (접이식)
        with st.expander("🔍 12대 가중치 세부 적용 현황표 상세 보기", expanded=False):
            total_multiplier = league_w * age_w * club_w * contract_w * pos_w * vers_w * reg_w * opta_w * ttype_w * stage_w * inj_w * urg_w * season_factor
            df_weights_live = pd.DataFrame({
                "가중치 세부 항목": [
                    "① 원소속 리그 템포 난이도", "② 포지션별 나이(에이징 커브)", "③ 영입 구단 규모 (클럽 티어)",
                    "④ 이적 당시 잔여 계약 기간", "⑤ 주 포지션 시장 희소성", "⑥ 멀티 포지션 소화 능력",
                    "⑦ 스쿼드 등록 / HG 쿼터", "⑧ FotMob 실적 및 평점 가중치", "⑨ 이적 형태 & 계약 조항",
                    "⑩ UCL / 빅매치 검증도", "⑪ 부상 내구성 & 메디컬 리스크", "⑫ 영입 구단 절박성 & 취약 포지션",
                    "❄️ 계절성 프리미엄 (겨울 특수)", "🎯 [종합] 최종 누적 가중치 배율"
                ],
                "선택된 조건 / 등급": [
                    selling_league.split(" (")[0], f"만 {player_age}세", buying_club_tier.split(":")[0],
                    remaining_contract.split(" (")[0], main_position.split(" (")[0], "단일 포지션",
                    reg_status.split(" (")[0], "★6.50 (기준)", transfer_type.split(" (")[0],
                    big_stage.split(" (")[0], injury_status.split(" (")[0], urgency_status.split(" (")[0],
                    "+10% 겨울 프리미엄" if is_winter else "여름 표준 시장", "12대 가중치 총 곱셈 합산"
                ],
                "실시간 배율": [
                    f"{league_w:.2f}x", f"{age_w:.2f}x", f"{club_w:.2f}x", f"{contract_w:.2f}x",
                    f"{pos_w:.2f}x", f"{vers_w:.2f}x", f"{reg_w:.2f}x", f"{opta_w:.2f}x",
                    f"{ttype_w:.2f}x", f"{stage_w:.2f}x", f"{inj_w:.2f}x", f"{urg_w:.2f}x",
                    f"{season_factor:.2f}x", f"✨ {total_multiplier:.3f}x"
                ]
            })
            st.table(df_weights_live)

        st.markdown("---")

        # 4. 구글 시트 저장 버튼
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

# 나머지 탭 영역
with tab2: st.subheader("📱 FotMob 시즌 성적 & 이적 예측")
with tab3: st.subheader("🔍 과거 유사 이적 사례 비교")
with tab4: st.subheader("🎯 이적 첫 시즌 실제 성적 검증")
with tab5: st.subheader("👥 신규 vs 과거 벤치마크")
with tab6: st.subheader("🏆 구단/리그별 종합 결산")
