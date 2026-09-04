import streamlit as st
import pandas as pd
import requests
import json
import plotly.graph_objects as go
from datetime import datetime

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
    "단순 1년 임대 (Simple Loan, 1년사용가치 20% 자동환산)": 0.20,
    "임대 후 의무 영입 (Loan w/ Obligation, +2%)": 1.02,
    "임대 후 선택 영입 (Loan w/ Option, 1년사용가치 기준)": 0.20,
    "바이백 조항 포함 이적 (Buy-back Clause, -5%)": 0.95,
    "셀온 지분 포함 이적 (Sell-on Clause, -3%)": 0.97,
    "비공개 이적 (Undisclosed, 시장적정가 1:1 수렴 추정)": 1.00,
    "FA 자유계약 영입 (Free Transfer, 계약금 기준)": 1.00
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

def get_exact_val(row, col_name, default_val=""):
    try:
        if col_name in row and pd.notnull(row[col_name]) and str(row[col_name]).strip() not in ["", "nan", "None"]:
            return type(default_val)(row[col_name])
    except:
        pass
    return default_val

def render(history_df, GOOGLE_SHEET_WEBAPP_URL):
    if st.session_state.get("last_saved_msg"):
        st.success(st.session_state["last_saved_msg"])
        st.session_state["last_saved_msg"] = None

    c_mode1, c_mode2 = st.columns([1, 1])
    with c_mode1:
        edit_toggle = st.toggle("✏️ 기존 저장된 선수 불러와서 수정/주급 추가 모드", value=False, key="main_edit_toggle")

    if "edit_data" not in st.session_state:
        st.session_state["edit_data"] = {}

    if edit_toggle:
        st.markdown("##### 🔍 불러올 선수 선택")
        has_season_col = "이적시즌" in history_df.columns
        has_name_col = "선수명" in history_df.columns

        if history_df.empty or not has_season_col or not has_name_col:
            st.warning("⚠️ 시트에 저장된 기존 데이터가 없거나 컬럼명을 찾을 수 없습니다.")
        else:
            c_ld1, c_ld2, c_ld3 = st.columns([1, 2, 1])
            with c_ld1:
                e_seasons = list(history_df["이적시즌"].dropna().unique())
                sel_e_season = st.selectbox("시즌 선택", e_seasons, key="edit_season_box")
            
            e_season_df = history_df[history_df["이적시즌"] == sel_e_season]
            e_players = list(e_season_df["선수명"].dropna().unique())
            
            with c_ld2:
                sel_e_player = st.selectbox("선수 선택", e_players, key="edit_player_box") if e_players else None

            with c_ld3:
                st.write("")
                st.write("")
                if st.button("📥 데이터 불러오기", type="primary", use_container_width=True):
                    if sel_e_player:
                        matched_rows = e_season_df[e_season_df["선수명"] == sel_e_player]
                        row_raw = matched_rows.iloc[-1]
                        
                        match_idx_list = e_season_df.index[e_season_df["선수명"] == sel_e_player].tolist()
                        if match_idx_list:
                            st.session_state["edit_row_index"] = match_idx_list[-1] + 2

                        # 시트 컬럼명에 맞춰 안전하게 데이터 추출 및 세션 저장
                        st.session_state["edit_data"] = {
                            "name": str(get_exact_val(row_raw, "선수명", "")),
                            "nat": str(get_exact_val(row_raw, "국적", "")),
                            "age": int(get_exact_val(row_raw, "만나이", 28)),
                            "from_team": str(get_exact_val(row_raw, "원소속팀명", "")),
                            "to_team": str(get_exact_val(row_raw, "이적팀명", "")),
                            "tm": int(get_exact_val(row_raw, "TM시장가치(만€)", 4500)),
                            "fee": int(get_exact_val(row_raw, "실제이적료(만€)", 0)),
                            "wage": float(get_exact_val(row_raw, "주급(만€)", 0.0)),
                            "note": str(get_exact_val(row_raw, "스카우팅메모", "")).split(" | [영입")[0].split(" | [방출")[0].strip(),
                            "season": str(get_exact_val(row_raw, "이적시즌", "26/27 여름 (Summer)")),
                            "from_league": str(get_exact_val(row_raw, "원소속리그", "잉글랜드 프리미어리그 (EPL 1부)")),
                            "to_league": str(get_exact_val(row_raw, "이적팀리그", "잉글랜드 프리미어리그 (EPL 1부)")),
                            "pos": str(get_exact_val(row_raw, "포지션", "센터백")),
                            "tier": str(get_exact_val(row_raw, "영입구단티어", "Tier 2")),
                            "ttype": str(get_exact_val(row_raw, "이적형태", "일반 완전 이적"))
                        }
                        st.success(f"✅ '{sel_e_player}' 데이터 불러오기 성공!")
                        st.rerun()
    else:
        st.session_state["edit_row_index"] = None
        if not edit_toggle:
            st.session_state["edit_data"] = {}

    ed = st.session_state.get("edit_data", {})

    st.markdown("---")
    
    with st.form(key="player_eval_form"):
        trade_type_choice = st.radio("거래 유형 구분", ["🔵 영입 (IN)", "🔴 방출 / 판매 (OUT)"], index=0, horizontal=True)
        is_out_trade = "방출" in trade_type_choice
        
        col1, col2 = st.columns([1, 1])

        with col1:
            st.subheader(f"📝 {'[수정 모드] ' if edit_toggle else ''}{'방출(OUT)' if is_out_trade else '영입(IN)'} 선수 & 계약 정보")
            c_s1, c_s2 = st.columns(2)
            with c_s1: 
                season_val = st.selectbox("이적 시즌 / 시장", ["26/27 여름 (Summer)", "26/27 겨울 (Winter)", "기타"], index=0)
            with c_s2: 
                transfer_type = st.selectbox("이적 형태 & 계약 조항", list(TRANSFER_TYPE_WEIGHTS.keys()), index=0)
                
            option_exercised = st.checkbox("📌 임대 후 옵션 발동 (완전 전환 완료된 건)", value=False)
            if option_exercised:
                transfer_type = "일반 완전 이적 (Permanent, 기준)"

            c_n1, c_n2, c_n3 = st.columns([2, 1, 1])
            with c_n1: player_name = st.text_input("선수 이름", value=ed.get("name", ""), placeholder="예: Ezri Konsa")
            with c_n2: player_nat = st.text_input("국적", value=ed.get("nat", ""), placeholder="예: 잉글랜드")
            with c_n3: player_age = st.number_input("만 나이", min_value=15, max_value=45, value=ed.get("age", 28))

            c_t1, c_t2, c_t3 = st.columns(3)
            with c_t1: in_from_team = st.text_input("원소속팀명 (보내는 팀)", value=ed.get("from_team", ""), placeholder="예: 아스톤 빌라")
            with c_t2: in_to_team = st.text_input("이적팀명 (영입 구단)", value=ed.get("to_team", ""), placeholder="예: 아스날")
            with c_t3: in_to_league_choice = st.selectbox("이적팀 리그", list(LEAGUE_WEIGHTS.keys()), index=0)

            pos_col1, pos_col2 = st.columns(2)
            with pos_col1: main_position = st.selectbox("주 포지션", list(POSITION_WEIGHTS.keys()), index=4)
            with pos_col2: versatility = st.selectbox("멀티 포지션 소화 능력", list(VERSATILITY_WEIGHTS.keys()), index=0)
                
            c_r1, c_r2 = st.columns(2)
            with c_r1: reg_status = st.selectbox("스쿼드 등록 / HG 쿼터", list(REGISTRATION_WEIGHTS.keys()), index=1)
            with c_r2: big_stage = st.selectbox("UCL / 빅매치 검증도", list(BIG_STAGE_WEIGHTS.keys()), index=0)
            
            c_i1, c_i2 = st.columns(2)
            with c_i1: injury_status = st.selectbox("부상 내구성 & 메디컬 리스크", list(INJURY_WEIGHTS.keys()), index=1)
            with c_i2: urgency_status = st.selectbox("영입 구단 절박성 & 취약 포지션", list(URGENCY_WEIGHTS.keys()), index=0)

            selling_league = st.selectbox("보내는 리그 (원소속 리그)", list(LEAGUE_WEIGHTS.keys()), index=0)
            buying_club_tier = st.selectbox("영입구단티어", list(CLUB_TIERS.keys()), index=1)
            remaining_contract = st.selectbox("이적 당시 잔여 계약 기간", list(CONTRACT_WEIGHTS.keys()), index=2)
            
            st.markdown("---")
            
            tm_market_value = st.number_input("TM시장가치(만€)", min_value=0, value=ed.get("tm", 4500), step=50)
            is_undisclosed = "비공개" in transfer_type
            actual_transfer_fee = st.number_input("실제이적료(만€)", min_value=0, value=ed.get("fee", 0), step=50, disabled=is_undisclosed)
            weekly_wage_in = st.number_input("주급(만€)", min_value=0.0, value=ed.get("wage", 0.0), step=0.5)

            player_notes = st.text_area("스카우팅메모", value=ed.get("note", ""), placeholder="예: 대인 방어 및 후방 빌드업 우수")

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

        base_calc_val = tm_market_value * league_w * age_w * club_w * contract_w * pos_w * vers_w * reg_w * 1.0 * ttype_w * stage_w * inj_w * urg_w
        fair_value = base_calc_val * season_factor
        calc_actual_fee = fair_value if is_undisclosed else actual_transfer_fee
        
        diff = calc_actual_fee - fair_value
        overpay_pct = (diff / fair_value) * 100 if fair_value > 0 else 0.0

        status_label = "⚖️ 적정가 (Fair Deal)" if abs(diff) <= (fair_value * 0.05) else (f"⚠️ 오버페이 (+{overpay_pct:.1f}%)" if diff > 0 else f"💎 저평가 ({overpay_pct:.1f}%)")
        final_deal_score = 7.50

        with col2:
            st.subheader("📊 분석 결과 및 12대 세부 지표")
            st.markdown(f"### **{player_name if player_name else '선수명 미입력'}** - `만 {player_age}세`")
            
            res_c1, res_c2, res_c3, res_c4 = st.columns(4)
            with res_c1: st.metric("산출 적정가", f"€{fair_value:,.1f}만")
            with res_c2: st.metric("실제 거래액", f"€{calc_actual_fee:,.1f}만")
            with res_c3: st.metric("평가율", f"{overpay_pct:+.1f}%")
            with res_c4: st.metric("이적 평점", f"★ {final_deal_score:.2f}")

        st.markdown("---")
        
        action_type = "update" if edit_toggle and st.session_state.get("edit_row_index") else "save_all"
        btn_label = f"🔄 '{player_name}' 수정된 데이터 덮어쓰기 (업데이트)" if action_type == "update" else f"💾 구글 시트에 신규 저장하기"
        
        submitted = st.form_submit_button(btn_label, use_container_width=True)

        if submitted:
            if not player_name.strip():
                st.warning("⚠️ 선수 이름을 먼저 입력해 주세요.")
            else:
                with st.spinner("구글 시트에 데이터를 전송 중입니다..."):
                    payload = {
                        "action": action_type,
                        "row_index": st.session_state.get("edit_row_index") if action_type == "update" else None,
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
                        "fee": float(calc_actual_fee),
                        "fair_val": round(fair_value, 1),
                        "diff": round(diff, 1),
                        "status": status_label,
                        "deal_score": float(final_deal_score),
                        "prev_matches": int(st.session_state.get("f_matches", 1)),
                        "prev_mins": int(st.session_state.get("f_mins", 90)),
                        "prev_goals": int(st.session_state.get("f_goals", 0)),
                        "prev_xg": float(st.session_state.get("f_xg", 0.0)),
                        "prev_assists": int(st.session_state.get("f_assists", 0)),
                        "prev_xa": float(st.session_state.get("f_xa", 0.0)),
                        "prev_shots": int(st.session_state.get("f_shots", 0)),
                        "prev_sot": int(st.session_state.get("f_sot", 0)),
                        "prev_chances": int(st.session_state.get("f_chances", 0)),
                        "prev_dribbles": int(st.session_state.get("f_dribbles", 0)),
                        "prev_touches_box": int(st.session_state.get("f_touches_box", 0)),
                        "prev_tackles": int(st.session_state.get("f_tackles", 0)),
                        "prev_rating": float(cur_rating),
                        "to_league": in_to_league_choice.split(" (")[0],
                        "proj_mins": 3000,
                        "proj_goals": 10.0,
                        "proj_xg": 9.0,
                        "proj_assists": 5.0,
                        "proj_xa": 4.5,
                        "proj_shots": 50.0,
                        "proj_rating": float(cur_rating),
                        "notes": player_notes.strip(),
                        "from_team": in_from_team.strip(),
                        "to_team": in_to_team.strip(),
                        "to_league_name": in_to_league_choice.split(" (")[0],
                        "trade_type": "OUT" if is_out_trade else "IN",
                        "weekly_wage": float(weekly_wage_in),
                        "gk_saves": 0, "gk_conceded": 0, "gk_prevented": 0.0, "gk_cs": 0, "gk_errors": 0, "gk_claims": 0,
                        "prev_starts": int(st.session_state.get("f_starts", 0)),
                        "big_chances": int(st.session_state.get("f_big_chances", 0)),
                        "pk_goals": int(st.session_state.get("f_pk_goals", 0)),
                        "pass_pct": float(st.session_state.get("f_pass_pct", 0.0)),
                        "duels_pct": float(st.session_state.get("f_duels_pct", 0.0)),
                        "aerial_pct": float(st.session_state.get("f_aerial_pct", 0.0))
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
                            st.session_state["last_saved_msg"] = f"✅ '{player_name}' 선수의 데이터가 성공적으로 {'수정(덮어쓰기)' if action_type == 'update' else '저장'}되었습니다!"
                            st.cache_data.clear()
                            st.session_state["edit_row_index"] = None
                            st.session_state["edit_data"] = {}
                            st.rerun()
                        else:
                            st.error(f"⚠️ 저장 실패: {res_json.get('message', '통신 오류')}")
                    except Exception as e:
                        st.error(f"⚠️ 저장 오류: {e}")
