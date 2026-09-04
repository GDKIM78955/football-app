import streamlit as st
import pandas as pd
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

# 데이터 로드 함수 (캐시 즉시 갱신)
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
        if not df.empty and "선수명" in df.columns:
            return df
    except Exception:
        pass
    return pd.DataFrame()

history_df = fetch_sheet_history()
validation_df = fetch_validation_data()

# 세션 상태 변수 초기화
if "last_saved_msg" not in st.session_state: st.session_state["last_saved_msg"] = None
if "edit_row_index" not in st.session_state: st.session_state["edit_row_index"] = None
if "custom_proj_mins" not in st.session_state: st.session_state["custom_proj_mins"] = 3000

# 폼 입력값 다이렉트 동기화용 세션 키 초기화
for k in ["input_name", "input_nat", "input_from_team", "input_to_team", "input_notes"]:
    if k not in st.session_state: st.session_state[k] = ""
if "input_age" not in st.session_state: st.session_state["input_age"] = 28
if "input_tm" not in st.session_state: st.session_state["input_tm"] = 4500
if "input_fee" not in st.session_state: st.session_state["input_fee"] = 0
if "input_wage" not in st.session_state: st.session_state["input_wage"] = 0.0

# FotMob 기본 스탯 초기화
for k, v in {
    "f_mins": 90, "f_goals": 0, "f_xg": 0.0, "f_assists": 0, "f_xa": 0.0,
    "f_rating": 6.50, "f_matches": 1, "f_starts": 0, "f_shots": 0, "f_sot": 0,
    "f_chances": 0, "f_dribbles": 0, "f_touches_box": 0, "f_tackles": 0,
    "f_gk_saves": 0, "f_gk_conceded": 0, "f_gk_prevented": 0.0,
    "f_gk_cs": 0, "f_gk_errors": 0, "f_gk_claims": 0,
    "f_big_chances": 0, "f_pk_goals": 0, "f_pass_pct": 0.0, "f_duels_pct": 0.0, "f_aerial_pct": 0.0
}.items():
    if k not in st.session_state: st.session_state[k] = v

# 가중치 딕셔너리 정의
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

CLUB_TIERS = {
    "Tier 1: 엘리트 메가클럽": 1.05, "Tier 2: 빅클럽": 1.02,
    "Tier 3: 중상위권 클럽": 1.00, "Tier 4: 중하위권 클럽": 0.98, "Tier 5: 소형/셀링 클럽": 0.95
}

CONTRACT_WEIGHTS = {
    "6개월 이하 (-20%)": 0.80, "1년 남음 (-8%)": 0.92,
    "2년 남음 (기준 1.00)": 1.00, "3년 남음 (+2%)": 1.02, "4년 이상 (+4%)": 1.04
}

POSITION_WEIGHTS = {
    "스트라이커 / 센터포워드 (ST/CF)": 1.02, "윙어 / 공격형 미드필더 (WG/CAM)": 1.01,
    "중앙 / 수비형 미드필더 (CM/CDM)": 1.00, "풀백 / 윙백 (RB/LB/WB)": 0.99,
    "센터백 (CB)": 0.99, "골키퍼 (GK)": 0.97
}

VERSATILITY_WEIGHTS = {"단일 포지션 전담": 1.00, "듀얼 롤 (+1%)": 1.01, "만능 유틸리티 (+2%)": 1.02}
REGISTRATION_WEIGHTS = {"일반 (기준)": 1.00, "🏴󠁧󠁢󠁥󠁮󠁧󠁿 EPL 홈그로운 (+4%)": 1.04, "🏛️ 유스 출신 (+2%)": 1.02, "🇪🇸🇮🇹 비EU 쿼터 (-2%)": 0.98}
TRANSFER_TYPE_WEIGHTS = {"일반 완전 이적 (기준)": 1.00, "단순 1년 임대 (20%)": 0.20, "임대 후 의무 영입": 1.02, "FA 자유계약": 1.00, "비공개 이적": 1.00}
BIG_STAGE_WEIGHTS = {"🌟 UCL/국대 주전 (+3%)": 1.03, "🔥 UEL/국대 (+1%)": 1.01, "⚖️ 경험 없음 (기준)": 1.00}
INJURY_WEIGHTS = {"🛡️ 철강왕 (+1%)": 1.01, "⚖️ 일반 (기준)": 1.00, "⚠️ 잔부상 (-3%)": 0.97, "🚨 장기부상 (-6%)": 0.94}
URGENCY_WEIGHTS = {"⚖️ 일반 보강 (기준)": 1.00, "🔥 우선 보강 (+4%)": 1.04, "🚨 패닉바이 (+8%)": 1.08}

def get_positional_age_weight(age, pos):
    if "ST" in pos or "WG" in pos or "CAM" in pos:
        return 1.05 if age <= 19 else (1.03 if age <= 23 else (1.00 if age <= 27 else (0.97 if age <= 29 else 0.85)))
    return 1.01 if age <= 23 else (1.00 if age <= 29 else 0.90)

def get_exact_val(row, col_name, default_val=""):
    try:
        if col_name in row and pd.notnull(row[col_name]) and str(row[col_name]).strip() not in ["", "nan", "None"]:
            return type(default_val)(row[col_name])
    except:
        pass
    return default_val

# 메인 앱 타이틀
st.title("⚽ 프로페셔널 축구 이적시장 12대 가중치 분석 & 스카우팅 데이터룸")

if st.session_state["last_saved_msg"]:
    st.success(st.session_state["last_saved_msg"])
    st.session_state["last_saved_msg"] = None

# 6개 탭 구성
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "💰 적정 이적료 평가", 
    "📱 FotMob 시즌 성적 & 이적 예측",
    "🔍 과거 유사 이적 사례 비교",
    "🎯 이적 첫 시즌 실제 성적 & 모델 검증",
    "👥 신규 이적생 vs 과거 선수 벤치마크",
    "🏆 이적시장 구단/리그별 종합 결산 & 데이터룸"
])

# ================= TAB 1 =================
with tab1:
    c_m1, c_m2 = st.columns([1, 1])
    with c_m1:
        edit_toggle = st.toggle("✏️ 기존 저장된 선수 불러와서 수정 모드", value=False)

    if edit_toggle:
        st.markdown("##### 🔍 불러올 선수 선택")
        if history_df.empty or "이적시즌" not in history_df.columns or "선수명" not in history_df.columns:
            st.warning("⚠️ 시트에 저장된 기존 데이터가 없습니다.")
        else:
            ld1, ld2, ld3 = st.columns([1, 2, 1])
            with ld1:
                e_seasons = list(history_df["이적시즌"].dropna().unique())
                sel_e_season = st.selectbox("시즌 선택", e_seasons, key="r_season_sel")
            e_season_df = history_df[history_df["이적시즌"] == sel_e_season]
            e_players = list(e_season_df["선수명"].dropna().unique())
            with ld2:
                sel_e_player = st.selectbox("선수 선택", e_players, key="r_player_sel") if e_players else None
            with ld3:
                st.write("")
                st.write("")
                if st.button("📥 데이터 불러오기", type="primary", use_container_width=True):
                    if sel_e_player:
                        row_raw = e_season_df[e_season_df["선수명"] == sel_e_player].iloc[-1]
                        match_idx_list = e_season_df.index[e_season_df["선수명"] == sel_e_player].tolist()
                        if match_idx_list:
                            st.session_state["edit_row_index"] = match_idx_list[-1] + 2

                        st.session_state["input_name"] = str(get_exact_val(row_raw, "선수명", ""))
                        st.session_state["input_nat"] = str(get_exact_val(row_raw, "국적", ""))
                        st.session_state["input_age"] = int(get_exact_val(row_raw, "만나이", 28))
                        st.session_state["input_from_team"] = str(get_exact_val(row_raw, "원소속팀명", ""))
                        st.session_state["input_to_team"] = str(get_exact_val(row_raw, "이적팀명", ""))
                        st.session_state["input_tm"] = int(get_exact_val(row_raw, "TM시장가치(만€)", 4500))
                        st.session_state["input_fee"] = int(get_exact_val(row_raw, "실제이적료(만€)", 0))
                        st.session_state["input_wage"] = float(get_exact_val(row_raw, "주급(만€)", 0.0))
                        st.session_state["input_notes"] = str(get_exact_val(row_raw, "스카우팅메모", ""))
                        st.success(f"✅ '{sel_e_player}' 불러오기 완료!")
                        st.rerun()
    else:
        st.session_state["edit_row_index"] = None

    st.markdown("---")
    trade_type_choice = st.radio("거래 유형 구분", ["🔵 영입 (IN)", "🔴 방출 / 판매 (OUT)"], index=0, horizontal=True)
    is_out_trade = "방출" in trade_type_choice

    col1, col2 = st.columns([1, 1])
    with col1:
        st.subheader(f"📝 {'[수정 모드] ' if edit_toggle else ''}선수 & 계약 정보")
        c_s1, c_s2 = st.columns(2)
        with c_s1: season_val = st.selectbox("이적 시즌", ["26/27 여름 (Summer)", "26/27 겨울 (Winter)", "기타"], index=0)
        with c_s2: transfer_type = st.selectbox("이적 형태", list(TRANSFER_TYPE_WEIGHTS.keys()), index=0)

        cn1, cn2, cn3 = st.columns([2, 1, 1])
        with cn1: player_name = st.text_input("선수 이름", key="input_name")
        with cn2: player_nat = st.text_input("국적", key="input_nat")
        with cn3: player_age = st.number_input("만 나이", min_value=15, max_value=45, key="input_age")

        ct1, ct2, ct3 = st.columns(3)
        with ct1: in_from_team = st.text_input("원소속팀명", key="input_from_team")
        with ct2: in_to_team = st.text_input("이적팀명", key="input_to_team")
        with ct3: in_to_league_choice = st.selectbox("이적팀 리그", list(LEAGUE_WEIGHTS.keys()), index=0)

        pc1, pc2 = st.columns(2)
        with pc1: main_position = st.selectbox("주 포지션", list(POSITION_WEIGHTS.keys()), index=0)
        with pc2: versatility = st.selectbox("멀티 포지션", list(VERSATILITY_WEIGHTS.keys()), index=0)

        rc1, rc2 = st.columns(2)
        with rc1: reg_status = st.selectbox("쿼터", list(REGISTRATION_WEIGHTS.keys()), index=0)
        with rc2: big_stage = st.selectbox("빅매치 검증", list(BIG_STAGE_WEIGHTS.keys()), index=2)

        ic1, ic2 = st.columns(2)
        with ic1: injury_status = st.selectbox("부상 내구성", list(INJURY_WEIGHTS.keys()), index=1)
        with ic2: urgency_status = st.selectbox("구단 절박성", list(URGENCY_WEIGHTS.keys()), index=0)

        selling_league = st.selectbox("보내는 리그", list(LEAGUE_WEIGHTS.keys()), index=0)
        buying_club_tier = st.selectbox("구단 티어", list(CLUB_TIERS.keys()), index=1)
        remaining_contract = st.selectbox("잔여 계약", list(CONTRACT_WEIGHTS.keys()), index=2)

        st.markdown("---")
        tm_market_value = st.number_input("TM시장가치(만€)", min_value=0, key="input_tm", step=50)
        is_undisclosed = "비공개" in transfer_type
        actual_transfer_fee = st.number_input("실제이적료(만€)", min_value=0, key="input_fee", step=50, disabled=is_undisclosed)
        weekly_wage_in = st.number_input("주급(만€)", min_value=0.0, key="input_wage", step=0.5)
        player_notes = st.text_area("스카우팅메모", key="input_notes")

    # 가중치 계산
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

    season_factor = 1.10 if "겨울" in season_val else 1.00
    base_calc_val = tm_market_value * league_w * age_w * club_w * contract_w * pos_w * vers_w * reg_w * ttype_w * stage_w * inj_w * urg_w
    fair_value = base_calc_val * season_factor
    calc_actual_fee = fair_value if is_undisclosed else actual_transfer_fee
    diff = calc_actual_fee - fair_value
    overpay_pct = (diff / fair_value) * 100 if fair_value > 0 else 0.0
    status_label = "⚖️ 적정가" if abs(diff) <= (fair_value * 0.05) else (f"⚠️ 오버페이 (+{overpay_pct:.1f}%)" if diff > 0 else f"💎 저평가")
    final_deal_score = 7.50

    with col2:
        st.subheader("📊 분석 결과")
        st.markdown(f"### **{player_name if player_name else '선수명 미입력'}**")
        rc1, rc2, rc3, rc4 = st.columns(4)
        rc1.metric("산출 적정가", f"€{fair_value:,.1f}만")
        rc2.metric("실제 거래액", f"€{calc_actual_fee:,.1f}만")
        rc3.metric("평가율", f"{overpay_pct:+.1f}%")
        rc4.metric("이적 평점", f"★ {final_deal_score:.2f}")

    st.markdown("---")
    action_type = "update" if edit_toggle and st.session_state.get("edit_row_index") is not None else "save_all"
    btn_label = f"🔄 '{player_name}' 기존 기록 수정하기 (덮어쓰기)" if action_type == "update" else f"💾 구글 시트에 신규 저장하기"

    if st.button(btn_label, type="primary", use_container_width=True):
        if not player_name.strip():
            st.warning("⚠️ 선수 이름을 입력해 주세요.")
        else:
            with st.spinner("구글 시트에 전송 중..."):
                payload = {
                    "action": action_type,
                    "row_index": st.session_state.get("edit_row_index") if action_type == "update" else None,
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "season": season_val, "name": player_name, "nat": player_nat or "미상",
                    "age": int(player_age), "pos": main_position.split(" (")[0],
                    "from_league": selling_league.split(" (")[0], "buying_tier": buying_club_tier.split(":")[0],
                    "transfer_type": transfer_type.split(" (")[0], "tm_val": float(tm_market_value),
                    "fee": float(calc_actual_fee), "fair_val": round(fair_value, 1), "diff": round(diff, 1),
                    "status": status_label, "deal_score": float(final_deal_score),
                    "prev_matches": 1, "prev_mins": 90, "prev_goals": 0, "prev_xg": 0.0,
                    "prev_assists": 0, "prev_xa": 0.0, "prev_shots": 0, "prev_sot": 0,
                    "prev_chances": 0, "prev_dribbles": 0, "prev_touches_box": 0, "prev_tackles": 0,
                    "prev_rating": 6.5, "to_league": in_to_league_choice.split(" (")[0],
                    "proj_mins": 3000, "proj_goals": 10.0, "proj_xg": 9.0, "proj_assists": 5.0, "proj_xa": 4.5,
                    "proj_shots": 50.0, "proj_rating": 7.0, "notes": player_notes,
                    "from_team": in_from_team, "to_team": in_to_team, "to_league_name": in_to_league_choice.split(" (")[0],
                    "trade_type": "OUT" if is_out_trade else "IN", "weekly_wage": float(weekly_wage_in),
                    "gk_saves": 0, "gk_conceded": 0, "gk_prevented": 0.0, "gk_cs": 0, "gk_errors": 0, "gk_claims": 0,
                    "prev_starts": 0, "big_chances": 0, "pk_goals": 0, "pass_pct": 0.0, "duels_pct": 0.0, "aerial_pct": 0.0
                }
                try:
                    res = requests.post(GOOGLE_SHEET_WEBAPP_URL, data=json.dumps(payload), headers={"Content-Type": "text/plain;charset=utf-8"}, timeout=30)
                    res_json = res.json()
                    if res.status_code in [200, 302] and res_json.get("status") == "success":
                        st.session_state["last_saved_msg"] = f"✅ '{player_name}' 처리 완료!"
                        st.cache_data.clear()
                        st.session_state["edit_row_index"] = None
                        for k in ["input_name", "input_nat", "input_from_team", "input_to_team", "input_notes"]:
                            st.session_state[k] = ""
                        st.session_state["input_age"] = 28
                        st.session_state["input_tm"] = 4500
                        st.session_state["input_fee"] = 0
                        st.session_state["input_wage"] = 0.0
                        st.rerun()
                    else:
                        st.error(f"⚠️ 실패: {res_json.get('message')}")
                except Exception as e:
                    st.error(f"⚠️ 오류: {e}")

# ================= TAB 2 =================
with tab2:
    st.subheader("📱 FotMob 스타일 시즌 스탯 입력 & 프로젝션")
    st.info("여권/스탯 입력 및 프로젝션 공간입니다.")

# ================= TAB 3 =================
with tab3:
    st.subheader("🔍 과거 유사 이적 사례 비교 (Comps)")
    if history_df.empty: st.info("데이터가 없습니다.")
    else: st.dataframe(history_df, use_container_width=True)

# ================= TAB 4 =================
with tab4:
    st.subheader("🎯 모델 사후 검증")
    if validation_df.empty: st.info("검증 데이터가 없습니다.")
    else: st.dataframe(validation_df, use_container_width=True)

# ================= TAB 5 =================
with tab5:
    st.subheader("👥 신규 이적생 vs 과거 선수 벤치마크")
    st.info("다각도 교차 비교 공간입니다.")

# ================= TAB 6 =================
with tab6:
    st.subheader("🏆 종합 결산 및 데이터룸")
    if history_df.empty: st.info("데이터가 없습니다.")
    else: st.dataframe(history_df, use_container_width=True)
