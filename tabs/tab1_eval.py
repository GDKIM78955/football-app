import streamlit as st
import pandas as pd
import requests
import json
from datetime import datetime

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
    "Tier 1: 엘리트 메가클럽 (레알, 맨시티, 바이에른, PSG 등)": 1.05,
    "Tier 2: 빅클럽 (아스날, 리버풀, 첼시, 바르샤, 유벤투스 등)": 1.02,
    "Tier 3: 중상위권 클럽 (토트넘, AT마드리드, 도르트문트 등)": 1.00,
    "Tier 4: 중하위권 클럽 (EPL 중하위, 타 빅리그 중위권)": 0.98,
    "Tier 5: 소형/셀링 클럽 (중소리그, 2부리그, K/J리그)": 0.95
}

CONTRACT_WEIGHTS = {"6개월 이하 (FA 임박/겨울 이적, -20%)": 0.80, "1년 남음 (재계약 분기점, -8%)": 0.92, "2년 남음 (표준 계약 기준선, 1.00)": 1.00, "3년 남음 (구단 협상 우위, +2%)": 1.02, "4년 이상 (장기 계약/바이아웃, +4%)": 1.04}
POSITION_WEIGHTS = {"스트라이커 / 센터포워드 (ST/CF, +2%)": 1.02, "윙어 / 공격형 미드필더 (WG/CAM, +1%)": 1.01, "중앙 / 수비형 미드필더 (CM/CDM, 기준)": 1.00, "풀백 / 윙백 (RB/LB/WB, -1%)": 0.99, "센터백 (CB, -1%)": 0.99, "골키퍼 (GK, -3%)": 0.97}
VERSATILITY_WEIGHTS = {"단일 포지션 전담 (1개 포지션, 기준)": 1.00, "듀얼 롤 (2개 포지션 소화, +1%)": 1.01, "만능 유틸리티 (3개 이상 소화, +2%)": 1.02}
REGISTRATION_WEIGHTS = {"일반 (EU 국적자 / 쿼터 이슈 없음, 기준)": 1.00, "🏴󠁧󠁢󠁥󠁮󠁧󠁿 EPL 홈그로운 (Home-Grown 충족, +4%)": 1.04, "🏛️ 구단 자체 유스 출신 (Club-Trained, +2%)": 1.02, "🇪🇸🇮🇹 비EU 쿼터 소모 (Non-EU Quota, -2%)": 0.98}
TRANSFER_TYPE_WEIGHTS = {"일반 완전 이적 (Permanent, 기준)": 1.00, "단순 1년 임대 (Simple Loan, 1년사용가치 20% 자동환산)": 0.20, "임대 후 의무 영입 (Loan w/ Obligation, +2%)": 1.02, "임대 후 선택 영입 (Loan w/ Option, 1년사용가치 기준)": 0.20, "바이백 조항 포함 이적 (Buy-back Clause, -5%)": 0.95, "셀온 지분 포함 이적 (Sell-on Clause, -3%)": 0.97, "비공개 이적 (Undisclosed, 시장적정가 1:1 수렴 추정)": 1.00, "FA 자유계약 영입 (Free Transfer, 계약금 기준)": 1.00}
BIG_STAGE_WEIGHTS = {"🌟 UCL 본선 16강+ / 주요 A매치 핵심 주전 (+3%)": 1.03, "🔥 UEL/UECL 본선 또는 국대 A매치 주전 (+1%)": 1.01, "⚖️ 유럽대항전 / 메이저 국대 경험 없음 (기준)": 1.00}
INJURY_WEIGHTS = {"🛡️ 철강왕 (최근 2년 결장 거의 없음, +1%)": 1.01, "⚖️ 일반적인 수준 (경미한 1~2주 결장, 기준)": 1.00, "⚠️ 잦은 근육/잔부상 (시즌당 4~6주 결장, -3%)": 0.97, "🚨 최근 2년 내 장기 부상 이력 (십자인대/골절, -6%)": 0.94}
URGENCY_WEIGHTS = {"⚖️ 일반 보강 / 뎁스 자원 (기준)": 1.00, "🔥 최우선 보강 타겟 (선발진 명확한 취약, +4%)": 1.04, "🚨 비상사태 / 대체불가 타겟 (핵심이탈·패닉바이, +8%)": 1.08}

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

def get_exact_val(row, col_name, default_val=""):
    try:
        if col_name in row and pd.notnull(row[col_name]) and str(row[col_name]).strip() not in ["", "nan", "None"]:
            return type(default_val)(row[col_name])
    except:
        pass
    return default_val

def render(history_df, webhook_url):
    if st.session_state.get("last_saved_msg"):
        st.success(st.session_state["last_saved_msg"])
        st.session_state["last_saved_msg"] = None

    if "form_key_id" not in st.session_state:
        st.session_state["form_key_id"] = 0
    if "persistent_edit_row" not in st.session_state:
        st.session_state["persistent_edit_row"] = None

    c_mode1, _ = st.columns([1, 1])
    with c_mode1:
        edit_toggle = st.toggle("✏️ 기존 저장된 선수 불러와서 수정/주급 추가 모드", value=False, key="tab1_edit_toggle")

    if edit_toggle:
        st.markdown("##### 🔍 불러올 선수 선택")
        if history_df.empty or "이적시즌" not in history_df.columns or "선수명" not in history_df.columns:
            st.warning("⚠️ 시트에 저장된 기존 데이터가 없습니다.")
        else:
            c_ld1, c_ld2, c_ld3 = st.columns([1, 2, 1])
            with c_ld1:
                e_seasons = list(history_df["이적시즌"].dropna().unique())
                sel_e_season = st.selectbox("시즌 선택", e_seasons, key="tab1_season_box")
            
            e_season_df = history_df[history_df["이적시즌"] == sel_e_season]
            e_players = list(e_season_df["선수명"].dropna().unique())
            
            with c_ld2:
                sel_e_player = st.selectbox("선수 선택", e_players, key="tab1_player_box") if e_players else None

            with c_ld3:
                st.write("")
                st.write("")
                if st.button("📥 데이터 불러오기", type="primary", use_container_width=True, key="tab1_load_btn"):
                    if sel_e_player:
                        matched_rows = e_season_df[e_season_df["선수명"] == sel_e_player]
                        row_raw = matched_rows.iloc[-1]
                        
                        match_idx_list = e_season_df.index[e_season_df["선수명"] == sel_e_player].tolist()
                        if match_idx_list:
                            real_row_idx = match_idx_list[-1] + 2
                            st.session_state["persistent_edit_row"] = real_row_idx

                        # 🌟 폼 키 ID를 증가시켜 위젯 세트를 새로 생성
                        st.session_state["form_key_id"] += 1
                        k_id = st.session_state["form_key_id"]

                        # 🌟 불러온 데이터를 세션 키에 직접 대입하여 위젯에 반영
                        st.session_state[f"tab1_name_{k_id}"] = str(get_exact_val(row_raw, "선수명", ""))
                        st.session_state[f"tab1_nat_{k_id}"] = str(get_exact_val(row_raw, "국적", ""))
                        st.session_state[f"tab1_age_{k_id}"] = int(get_exact_val(row_raw, "만나이", 28))
                        st.session_state[f"tab1_from_team_{k_id}"] = str(get_exact_val(row_raw, "원소속팀명", ""))
                        st.session_state[f"tab1_to_team_{k_id}"] = str(get_exact_val(row_raw, "이적팀명", ""))
                        st.session_state[f"tab1_tm_{k_id}"] = int(get_exact_val(row_raw, "TM시장가치(만€)", 4500))
                        st.session_state[f"tab1_fee_{k_id}"] = int(get_exact_val(row_raw, "실제이적료(만€)", 0))
                        st.session_state[f"tab1_wage_{k_id}"] = float(get_exact_val(row_raw, "주급(만€)", 0.0))
                        
                        p_notes = str(get_exact_val(row_raw, "스카우팅메모", ""))
                        st.session_state[f"tab1_notes_{k_id}"] = p_notes.split(" | [영입")[0].split(" | [방출")[0].strip()

                        # 셀렉트박스 매칭
                        p_pos_str = str(get_exact_val(row_raw, "포지션", ""))
                        for p_k in POSITION_WEIGHTS.keys():
                            if p_pos_str and p_pos_str in p_k:
                                st.session_state[f"tab1_pos_{k_id}"] = p_k
                                break

                        p_from_league = str(get_exact_val(row_raw, "원소속리그", ""))
                        for l_k in LEAGUE_WEIGHTS.keys():
                            if p_from_league and p_from_league in l_k:
                                st.session_state[f"tab1_from_league_{k_id}"] = l_k
                                break

                        p_to_league_name = str(get_exact_val(row_raw, "이적팀리그", ""))
                        for l_k in LEAGUE_WEIGHTS.keys():
                            if p_to_league_name and p_to_league_name in l_k:
                                st.session_state[f"tab1_to_league_{k_id}"] = l_k
                                break

                        p_tier = str(get_exact_val(row_raw, "영입구단티어", ""))
                        for t_k in CLUB_TIERS.keys():
                            if p_tier and p_tier in t_k:
                                st.session_state[f"tab1_tier_{k_id}"] = t_k
                                break

                        p_ttype = str(get_exact_val(row_raw, "이적형태", ""))
                        for tt_k in TRANSFER_TYPE_WEIGHTS.keys():
                            if p_ttype and p_ttype in tt_k:
                                st.session_state[f"tab1_ttype_{k_id}"] = tt_k
                                break

                        st.session_state["last_saved_msg"] = f"✅ '{sel_e_player}' 데이터 불러오기 완료! (시트 행번호: {st.session_state['persistent_edit_row']})"
                        st.rerun()
    else:
        st.session_state["persistent_edit_row"] = None

    k_id = st.session_state["form_key_id"]
    active_row_index = st.session_state.get("persistent_edit_row")

    if edit_toggle and active_row_index:
        st.info(f"📌 [수정 모드 활성화됨] 현재 타겟 구글 시트 행 번호: **{active_row_index}번째 행** (이 행의 데이터가 덮어씌워집니다)")

    st.markdown("---")
    trade_type_choice = st.radio("거래 유형 구분", ["🔵 영입 (IN)", "🔴 방출 / 판매 (OUT)"], index=0, horizontal=True, key=f"tab1_trade_type_{k_id}")
    is_out_trade = "방출" in trade_type_choice
    
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader(f"📝 {'[수정 모드 안심 상태] ' if (edit_toggle and active_row_index) else ''}{'방출(OUT)' if is_out_trade else '영입(IN)'} 선수 & 계약 정보")
        c_s1, c_s2 = st.columns(2)
        with c_s1: season_val = st.selectbox("이적 시즌 / 시장", ["26/27 여름 (Summer)", "26/27 겨울 (Winter)", "기타"], index=0, key=f"tab1_season_{k_id}")
        with c_s2: transfer_type = st.selectbox("이적 형태 & 계약 조항", list(TRANSFER_TYPE_WEIGHTS.keys()), index=0, key=f"tab1_ttype_{k_id}")
            
        option_exercised = st.checkbox("📌 임대 후 옵션 발동 (완전 전환 완료된 건)", value=False, key=f"tab1_opt_{k_id}")
        if option_exercised:
            transfer_type = "일반 완전 이적 (Permanent, 기준)"

        c_n1, c_n2, c_n3 = st.columns([2, 1, 1])
        with c_n1: player_name = st.text_input("선수 이름", placeholder="예: Bruno Guimarães", key=f"tab1_name_{k_id}")
        with c_n2: player_nat = st.text_input("국적", placeholder="예: 브라질", key=f"tab1_nat_{k_id}")
        with c_n3: player_age = st.number_input("만 나이", min_value=15, max_value=45, value=28, key=f"tab1_age_{k_id}")

        c_t1, c_t2, c_t3 = st.columns(3)
        with c_t1: in_from_team = st.text_input("원소속팀명 (보내는 팀)", placeholder="예: 뉴캐슬", key=f"tab1_from_team_{k_id}")
        with c_t2: in_to_team = st.text_input("이적팀명 (영입 구단)", placeholder="예: 맨체스터 시티", key=f"tab1_to_team_{k_id}")
        with c_t3: in_to_league_choice = st.selectbox("이적팀 리그", list(LEAGUE_WEIGHTS.keys()), index=0, key=f"tab1_to_league_{k_id}")
        
        pos_col1, pos_col2 = st.columns(2)
        with pos_col1: main_position = st.selectbox("주 포지션", list(POSITION_WEIGHTS.keys()), index=2, key=f"tab1_pos_{k_id}")
        with pos_col2: versatility = st.selectbox("멀티 포지션 소화 능력", list(VERSATILITY_WEIGHTS.keys()), index=0, key=f"tab1_vers_{k_id}")
            
        c_r1, c_r2 = st.columns(2)
        with c_r1: reg_status = st.selectbox("스쿼드 등록 / HG 쿼터", list(REGISTRATION_WEIGHTS.keys()), index=0, key=f"tab1_reg_{k_id}")
        with c_r2: big_stage = st.selectbox("UCL / 빅매치 검증도", list(BIG_STAGE_WEIGHTS.keys()), index=0, key=f"tab1_stage_{k_id}")
        
        c_i1, c_i2 = st.columns(2)
        with c_i1: injury_status = st.selectbox("부상 내구성 & 메디컬 리스크", list(INJURY_WEIGHTS.keys()), index=1, key=f"tab1_inj_{k_id}")
        with c_i2: urgency_status = st.selectbox("영입 구단 절박성 & 취약 포지션", list(URGENCY_WEIGHTS.keys()), index=0, key=f"tab1_urg_{k_id}")

        selling_league = st.selectbox("보내는 리그 (원소속 리그)", list(LEAGUE_WEIGHTS.keys()), index=0, key=f"tab1_from_league_{k_id}")
        buying_club_tier = st.selectbox("영입구단티어", list(CLUB_TIERS.keys()), index=1, key=f"tab1_tier_{k_id}")
        remaining_contract = st.selectbox("이적 당시 잔여 계약 기간", list(CONTRACT_WEIGHTS.keys()), index=2, key=f"tab1_contract_{k_id}")
        
        st.markdown("---")
        tm_market_value = st.number_input("TM시장가치(만€)", min_value=0, value=8500, step=50, key=f"tab1_tm_{k_id}")
        actual_transfer_fee = st.number_input("실제이적료(만€)", min_value=0, value=10000, step=50, key=f"tab1_fee_{k_id}")
        weekly_wage_in = st.number_input("주급(만€)", min_value=0.0, value=30.0, step=0.5, key=f"tab1_wage_{k_id}")
        player_notes = st.text_area("스카우팅메모", placeholder="특이사항 입력", key=f"tab1_notes_{k_id}")

    # 계산 로직
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

    is_winter = "겨울" in season_val
    season_factor = 1.10 if is_winter else 1.00

    base_calc_val = tm_market_value * league_w * age_w * club_w * contract_w * pos_w * vers_w * reg_w * 1.01 * ttype_w * stage_w * inj_w * urg_w
    fair_value = base_calc_val * season_factor
    diff = actual_transfer_fee - fair_value
    overpay_pct = (diff / fair_value) * 100 if fair_value > 0 else 0.0
    status_label = "⚖️ 적정가 (Fair Deal)" if abs(diff) <= (fair_value * 0.05) else (f"⚠️ 오버페이 (+{overpay_pct:.1f}%)" if diff > 0 else f"💎 혜자 ({overpay_pct:.1f}%)")

    with col2:
        st.subheader("📊 핵심 분석 결과")
        st.metric("산출 적정가", f"€{fair_value:,.1f}만")
        st.metric("실제 거래액", f"€{actual_transfer_fee:,.1f}만")
        st.metric("평가율", f"{overpay_pct:+,.1f}%")

    st.markdown("---")
    action_type = "update" if (edit_toggle and active_row_index) else "save_all"
    btn_label = f"🔄 '{player_name or '선수'}' 구글 시트 업데이트 (행: {active_row_index})" if (edit_toggle and active_row_index) else "💾 구글 시트에 신규 저장하기"

    if st.button(btn_label, type="primary", use_container_width=True, key=f"tab1_save_btn_{k_id}"):
        if not player_name.strip():
            st.warning("⚠️ 선수 이름을 입력해 주세요.")
        else:
            with st.spinner("구글 시트 통신 중..."):
                payload = {
                    "action": action_type,
                    "row_index": active_row_index if (edit_toggle and active_row_index) else None,
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "season": season_val,
                    "name": player_name,
                    "nat": player_nat if player_nat.strip() else "미상",
                    "age": int(player_age),
                    "pos": main_position.split(" (")[0],
                    "from_league": selling_league.split(" (")[0],
                    "buying_tier": buying_club_tier.split(":")[0],
                    "transfer_type": transfer_type.split(" (")[0],
                    "tm_val": float(tm_market_value),
                    "fee": float(actual_transfer_fee),
                    "fair_val": round(fair_value, 1),
                    "diff": round(diff, 1),
                    "status": status_label,
                    "deal_score": 8.0,
                    "prev_matches": 10, "prev_starts": 10, "prev_mins": 900, "prev_goals": 5, "prev_xg": 4.5, "prev_assists": 3, "prev_xa": 2.5,
                    "prev_shots": 0, "prev_sot": 0, "prev_chances": 0, "prev_dribbles": 0, "prev_touches_box": 0, "prev_tackles": 0,
                    "prev_rating": 7.20,
                    "to_league": in_to_league_choice.split(" (")[0],
                    "proj_mins": 3000,
                    "proj_goals": 0.0, "proj_xg": 0.0, "proj_assists": 0.0, "proj_xa": 0.0, "proj_shots": 0.0, "proj_rating": 7.0,
                    "notes": player_notes,
                    "from_team": in_from_team.strip(),
                    "to_team": in_to_team.strip(),
                    "to_league_name": in_to_league_choice.split(" (")[0],
                    "trade_type": "OUT" if is_out_trade else "IN",
                    "weekly_wage": float(weekly_wage_in)
                }
                try:
                    res = requests.post(webhook_url, data=json.dumps(payload), headers={"Content-Type": "text/plain;charset=utf-8"}, timeout=30)
                    if res.status_code in [200, 302]:
                        st.session_state["last_saved_msg"] = f"✅ '{player_name}' 데이터가 {active_row_index if (edit_toggle and active_row_index) else '신규'} 행에 정상 반영되었습니다!"
                        st.session_state["persistent_edit_row"] = None
                        st.cache_data.clear()
                        st.rerun()
                except Exception as e:
                    st.error(f"⚠️ 오류: {e}")
