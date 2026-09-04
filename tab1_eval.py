import streamlit as st
import pandas as pd
import requests
import json
import plotly.graph_objects as go
from datetime import datetime

def render_tab1(history_df, GOOGLE_SHEET_WEBAPP_URL, LEAGUE_WEIGHTS, CLUB_TIERS, CONTRACT_WEIGHTS, POSITION_WEIGHTS, VERSATILITY_WEIGHTS, REGISTRATION_WEIGHTS, TRANSFER_TYPE_WEIGHTS, BIG_STAGE_WEIGHTS, INJURY_WEIGHTS, URGENCY_WEIGHTS, TRACKED_LEAGUE_NAMES, get_positional_age_weight, format_currency_desc, rate_krw, rate_gbp):
    
    if st.session_state["last_saved_msg"]:
        st.success(st.session_state["last_saved_msg"])
        st.session_state["last_saved_msg"] = None

    if "current_form" not in st.session_state:
        st.session_state["current_form"] = {
            "name": "", "nat": "", "age": 28, "from_team": "", "to_team": "",
            "tm": 4500, "fee": 5960, "wage": 0.0, "notes": "", "season": "26/27 여름 (Summer)",
            "pos": list(POSITION_WEIGHTS.keys())[4],
            "from_league": list(LEAGUE_WEIGHTS.keys())[0],
            "to_league": list(LEAGUE_WEIGHTS.keys())[0],
            "buying_tier": list(CLUB_TIERS.keys())[1],
            "contract": list(CONTRACT_WEIGHTS.keys())[2],
            "transfer_type": list(TRANSFER_TYPE_WEIGHTS.keys())[0],
            "trade_type": "🔵 영입 (IN)"
        }

    c_mode1, c_mode2 = st.columns([1, 1])
    with c_mode1:
        edit_toggle = st.toggle("✏️ 기존 저장된 선수 불러와서 수정/주급 추가 모드", value=False)

    if edit_toggle:
        st.markdown("##### 🔍 불러올 선수 선택")
        if history_df.empty or "선수명" not in history_df.columns:
            st.warning("⚠️ 시트에 저장된 기존 데이터가 없습니다.")
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
                        row_data = e_season_df[e_season_df["선수명"] == sel_e_player].iloc[-1]

                        pos_match = list(POSITION_WEIGHTS.keys())[4]
                        for p_k in POSITION_WEIGHTS.keys():
                            if str(row_data.get("포지션", "")) in p_k:
                                pos_match = p_k
                                break

                        from_l_match = list(LEAGUE_WEIGHTS.keys())[0]
                        for l_k in LEAGUE_WEIGHTS.keys():
                            if str(row_data.get("원소속리그", "")) in l_k:
                                from_l_match = l_k
                                break

                        to_l_match = list(LEAGUE_WEIGHTS.keys())[0]
                        for l_k in LEAGUE_WEIGHTS.keys():
                            if str(row_data.get("이적팀리그", "")) in l_k:
                                to_l_match = l_k
                                break

                        st.session_state["current_form"] = {
                            "name": str(row_data.get("선수명", "")),
                            "nat": str(row_data.get("국적", "")),
                            "age": int(row_data.get("나이", 28)) if pd.notnull(row_data.get("나이")) else 28,
                            "from_team": str(row_data.get("원소속팀명", "")),
                            "to_team": str(row_data.get("이적팀명", "")),
                            "tm": int(row_data.get("TM시장가치(만€)", row_data.get("시장가치(만€)", 4500))) if pd.notnull(row_data.get("TM시장가치(만€)", row_data.get("시장가치(만€)"))) else 4500,
                            "fee": int(row_data.get("실제이적료(만€)", 0)) if pd.notnull(row_data.get("실제이적료(만€)")) else 0,
                            "wage": float(row_data.get("주급(만€)", row_data.get("선수주급(만€)", 0.0))) if pd.notnull(row_data.get("주급(만€)", row_data.get("선수주급(만€)"))) else 0.0,
                            "notes": str(row_data.get("스카우팅메모", "")),
                            "season": sel_e_season,
                            "pos": pos_match,
                            "from_league": from_l_match,
                            "to_league": to_l_match,
                            "buying_tier": list(CLUB_TIERS.keys())[1],
                            "contract": list(CONTRACT_WEIGHTS.keys())[2],
                            "transfer_type": list(TRANSFER_TYPE_WEIGHTS.keys())[0],
                            "trade_type": "🔴 방출 / 판매 (OUT)" if str(row_data.get("거래구분", "")).strip() == "OUT" else "🔵 영입 (IN)"
                        }

                        st.session_state["f_mins"] = int(row_data.get("이전_출전시간", row_data.get("직전_출전시간", 2206))) if pd.notnull(row_data.get("이전_출전시간", row_data.get("직전_출전시간"))) else 2206
                        st.session_state["f_goals"] = int(row_data.get("이전_골", row_data.get("직전_골", 0))) if pd.notnull(row_data.get("이전_골", row_data.get("직전_골"))) else 0
                        st.session_state["f_xg"] = float(row_data.get("이전_xG", row_data.get("직전_xG", 0.0))) if pd.notnull(row_data.get("이전_xG", row_data.get("직전_xG"))) else 0.0
                        st.session_state["f_assists"] = int(row_data.get("이전_도움", row_data.get("직전_도움", 0))) if pd.notnull(row_data.get("이전_도움", row_data.get("직전_도움"))) else 0
                        st.session_state["f_xa"] = float(row_data.get("이전_xA", row_data.get("직전_xA", 0.0))) if pd.notnull(row_data.get("이전_xA", row_data.get("직전_xA"))) else 0.0
                        st.session_state["f_rating"] = float(row_data.get("이전_FotMob평점", row_data.get("직전_평점", 7.0))) if pd.notnull(row_data.get("이전_FotMob평점", row_data.get("직전_평점"))) else 7.0
                        st.session_state["f_matches"] = int(row_data.get("이전_출전경기", row_data.get("직전_경기수", 28))) if pd.notnull(row_data.get("이전_출전경기", row_data.get("직전_경기수"))) else 28
                        st.session_state["f_starts"] = int(row_data.get("이전_선발", row_data.get("직전_선발", 25))) if pd.notnull(row_data.get("이전_선발", row_data.get("직전_선발"))) else 25
                        st.session_state["f_shots"] = int(row_data.get("이전_총슈팅", row_data.get("직전_슈팅", 0))) if pd.notnull(row_data.get("이전_총슈팅", row_data.get("직전_슈팅"))) else 0
                        st.session_state["f_sot"] = int(row_data.get("이전_유효슈팅", row_data.get("직전_유효슈팅", 0))) if pd.notnull(row_data.get("이전_유효슈팅", row_data.get("직전_유효슈팅"))) else 0
                        st.session_state["f_chances"] = int(row_data.get("이전_찬스메이킹", row_data.get("직전_기회창출", 0))) if pd.notnull(row_data.get("이전_찬스메이킹", row_data.get("직전_기회창출"))) else 0
                        st.session_state["f_dribbles"] = int(row_data.get("이전_성공드리블", row_data.get("직전_드리블", 0))) if pd.notnull(row_data.get("이전_성공드리블", row_data.get("직전_드리블"))) else 0
                        st.session_state["f_touches_box"] = int(row_data.get("이전_박스터치", row_data.get("직전_박스터치", 0))) if pd.notnull(row_data.get("이전_박스터치", row_data.get("직전_박스터치"))) else 0
                        st.session_state["f_tackles"] = int(row_data.get("이전_태클성공", row_data.get("직전_태클", 0))) if pd.notnull(row_data.get("이전_태클성공", row_data.get("직전_태클"))) else 0

                        st.session_state["f_gk_saves"] = int(row_data.get("GK_선방", 0)) if pd.notnull(row_data.get("GK_선방")) else 0
                        st.session_state["f_gk_conceded"] = int(row_data.get("GK_실점", 0)) if pd.notnull(row_data.get("GK_실점")) else 0
                        st.session_state["f_gk_prevented"] = float(row_data.get("GK_득점차단", 0.0)) if pd.notnull(row_data.get("GK_득점차단")) else 0.0
                        st.session_state["f_gk_cs"] = int(row_data.get("GK_클린시트", 0)) if pd.notnull(row_data.get("GK_클린시트")) else 0
                        st.session_state["f_gk_errors"] = int(row_data.get("GK_실수", 0)) if pd.notnull(row_data.get("GK_실수")) else 0
                        st.session_state["f_gk_claims"] = int(row_data.get("GK_공중볼", 0)) if pd.notnull(row_data.get("GK_공중볼")) else 0

                        st.session_state["form_key_id"] += 1
                        st.rerun()

    k_id = st.session_state["form_key_id"]
    cf = st.session_state["current_form"]

    st.markdown("---")
    trade_type_choice = st.radio("거래 유형 구분", ["🔵 영입 (IN)", "🔴 방출 / 판매 (OUT)"], index=0 if cf["trade_type"] == "🔵 영입 (IN)" else 1, horizontal=True, key=f"trade_type_{k_id}")
    is_out_trade = "방출" in trade_type_choice

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader(f"📝 {'[수정 모드] ' if edit_toggle else ''}{'방출(OUT)' if is_out_trade else '영입(IN)'} 선수 & 계약 정보")
        c_s1, c_s2 = st.columns(2)
        with c_s1: 
            season_val = st.selectbox("이적 시즌 / 시장", ["26/27 여름 (Summer)", "26/27 겨울 (Winter)", "기타"], index=["26/27 여름 (Summer)", "26/27 겨울 (Winter)", "기타"].index(cf["season"]) if cf["season"] in ["26/27 여름 (Summer)", "26/27 겨울 (Winter)", "기타"] else 0, key=f"season_{k_id}")
        with c_s2: 
            transfer_type = st.selectbox("이적 형태 & 계약 조항", list(TRANSFER_TYPE_WEIGHTS.keys()), index=list(TRANSFER_TYPE_WEIGHTS.keys()).index(cf["transfer_type"]) if cf["transfer_type"] in TRANSFER_TYPE_WEIGHTS else 0, key=f"ttype_{k_id}")

        c_n1, c_n2, c_n3 = st.columns([2, 1, 1])
        with c_n1: player_name = st.text_input("선수 이름", value=cf["name"], placeholder="예: Ezri Konsa", key=f"name_{k_id}")
        with c_n2: player_nat = st.text_input("국적", value=cf["nat"], placeholder="예: 잉글랜드", key=f"nat_{k_id}")
        with c_n3: player_age = st.number_input("나이(만)", min_value=15, max_value=45, value=cf["age"], key=f"age_{k_id}")

        c_t1, c_t2, c_t3 = st.columns(3)
        with c_t1: in_from_team = st.text_input("원소속팀명 (보내는 팀)", value=cf["from_team"], placeholder="예: 아스톤 빌라", key=f"from_team_{k_id}")
        with c_t2: in_to_team = st.text_input("이적팀명 (영입 구단)", value=cf["to_team"], placeholder="예: 아스날", key=f"to_team_{k_id}")
        with c_t3: in_to_league_choice = st.selectbox("이적팀 리그", list(LEAGUE_WEIGHTS.keys()), index=list(LEAGUE_WEIGHTS.keys()).index(cf["to_league"]) if cf["to_league"] in LEAGUE_WEIGHTS else 0, key=f"to_league_choice_{k_id}")

        pos_col1, pos_col2 = st.columns(2)
        with pos_col1: main_position = st.selectbox("주 포지션", list(POSITION_WEIGHTS.keys()), index=list(POSITION_WEIGHTS.keys()).index(cf["pos"]) if cf["pos"] in POSITION_WEIGHTS else 4, key=f"pos_{k_id}")
        with pos_col2: versatility = st.selectbox("멀티 포지션 소화 능력", list(VERSATILITY_WEIGHTS.keys()), index=0, key=f"vers_{k_id}")

        c_r1, c_r2 = st.columns(2)
        with c_r1: reg_status = st.selectbox("스쿼드 등록 / HG 쿼터", list(REGISTRATION_WEIGHTS.keys()), index=1, key=f"reg_{k_id}")
        with c_r2: big_stage = st.selectbox("UCL / 빅매치 검증도", list(BIG_STAGE_WEIGHTS.keys()), index=0, key=f"stage_{k_id}")

        c_i1, c_i2 = st.columns(2)
        with c_i1: injury_status = st.selectbox("부상 내구성 & 메디컬 리스크", list(INJURY_WEIGHTS.keys()), index=1, key=f"inj_{k_id}")
        with c_i2: urgency_status = st.selectbox("영입 구단 절박성 & 취약 포지션", list(URGENCY_WEIGHTS.keys()), index=0, key=f"urg_{k_id}")

        selling_league = st.selectbox("보내는 리그 (원소속 리그)", list(LEAGUE_WEIGHTS.keys()), index=list(LEAGUE_WEIGHTS.keys()).index(cf["from_league"]) if cf["from_league"] in LEAGUE_WEIGHTS else 0, key=f"league_{k_id}")
        buying_club_tier = st.selectbox("영입하는 구단 규모", list(CLUB_TIERS.keys()), index=list(CLUB_TIERS.keys()).index(cf["buying_tier"]) if cf["buying_tier"] in CLUB_TIERS else 1, key=f"tier_{k_id}")
        remaining_contract = st.selectbox("이적 당시 잔여 계약 기간", list(CONTRACT_WEIGHTS.keys()), index=list(CONTRACT_WEIGHTS.keys()).index(cf["contract"]) if cf["contract"] in CONTRACT_WEIGHTS else 2, key=f"contract_{k_id}")

        st.markdown("---")
        tm_market_value = st.number_input("트랜스퍼마르크트 시장 가치 (만 유로, €)", min_value=0, value=cf["tm"], step=50, key=f"tm_{k_id}")
        is_loan_type = "임대" in transfer_type and "의무" not in transfer_type
        is_undisclosed = "비공개" in transfer_type

        fee_label = "실제 수령/지출 임대료 (Loan Fee, 만 유로, €)" if is_loan_type else ("실제 방출(판매) 이적료 (만 유로, €)" if is_out_trade else "실제 영입(지출) 이적료 (만 유로, €)")
        actual_transfer_fee = st.number_input(fee_label, min_value=0, value=0 if is_undisclosed else cf["fee"], step=50, key=f"fee_{k_id}", disabled=is_undisclosed)

        weekly_wage_in = st.number_input("선수 주급 (만 유로, €/주)", min_value=0.0, value=float(cf["wage"]), step=0.5, key=f"wage_{k_id}")
        player_notes = st.text_area("개인 메모 / 스카우팅 코멘트", value=cf["notes"], placeholder="예: 대인 방어 및 후방 빌드업 우수", key=f"note_{k_id}")

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

    if is_undisclosed:
        status_label = "⚖️ 비공개 (적정가 추정)"
    elif fair_value == 0 and calc_actual_fee == 0: 
        status_label = "입력 대기 중"
    elif abs(diff) <= (fair_value * 0.05): 
        status_label = "⚖️ 적정가 (Fair Deal)"
    elif diff > 0: 
        status_label = f"⚠️ {'고가 매각 성공' if is_out_trade else '고평가/오버페이'} (+{overpay_pct:.1f}%)"
    else: 
        status_label = f"💎 {'헐값 매각 손해' if is_out_trade else '저평가/혜자'} ({overpay_pct:.1f}%)"

    final_deal_score = 7.50

    with col2:
        st.subheader("📊 분석 결과 및 12대 세부 지표")
        display_name = player_name if player_name else "선수명 미입력"
        st.markdown(f"### **{display_name}** - `{main_position.split(' (')[0]}`")

        res_c1, res_c2, res_c3, res_c4 = st.columns(4)
        with res_c1: st.metric("산출 적정가", f"€{fair_value:,.1f}만")
        with res_c2: st.metric("실제 거래액", "비공개" if is_undisclosed else f"€{calc_actual_fee:,.1f}만")
        with res_c3: st.metric("평가율", f"{overpay_pct:+.1f}%")
        with res_c4: st.metric("이적 평점", f"★ {final_deal_score:.2f}")

        # 🌟 12대 스카우팅 육각형 레이더 차트 복구
        st.markdown("---")
        with st.expander("📊 [이미지 캡처용] 선수 12대 스카우팅 육각형 레이더 차트", expanded=True):
            radar_categories = ['리그 템포', '나이/포텐', '구단 스케일', '계약 상태', '포지션 희소성', 'UCL/빅매치', '부상 내구성', '영입 절박성']
            radar_values = [league_w * 100, age_w * 100, club_w * 100, contract_w * 100, pos_w * 100, stage_w * 100, inj_w * 100, urg_w * 100]

            fig = go.Figure()
            fig.add_trace(go.Scatterpolar(
                r=radar_values + [radar_values[0]],
                theta=radar_categories + [radar_categories[0]],
                fill='toself',
                fillcolor='rgba(31, 119, 180, 0.3)' if not is_out_trade else 'rgba(214, 39, 40, 0.3)',
                line=dict(color='#1f77b4' if not is_out_trade else '#d62728', width=2),
                name=display_name
            ))
            fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[50, 115])), showlegend=False, margin=dict(l=40, r=40, t=30, b=30), height=320)
            st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    btn_label = f"🔄 '{player_name}' 수정된 데이터 구글 시트에 업데이트" if edit_toggle else f"💾 구글 시트에 바로 저장하기"

    if st.button(btn_label, type="primary", use_container_width=True, key=f"save_btn_{k_id}"):
        if not player_name.strip():
            st.warning("⚠️ 선수 이름을 먼저 입력해 주세요.")
        else:
            action_type = "update_existing" if edit_toggle else "save_all"
            with st.spinner("구글 시트에 동기화 중..."):
                payload = {
                    "action": action_type,
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
                    "prev_matches": int(st.session_state.get("f_matches", 28)),
                    "prev_mins": int(st.session_state.get("f_mins", 2206)),
                    "prev_goals": int(st.session_state.get("f_goals", 16)),
                    "prev_xg": float(st.session_state.get("f_xg", 17.44)),
                    "prev_assists": int(st.session_state.get("f_assists", 4)),
                    "prev_xa": float(st.session_state.get("f_xa", 3.33)),
                    "prev_shots": int(st.session_state.get("f_shots", 88)),
                    "prev_sot": int(st.session_state.get("f_sot", 43)),
                    "prev_chances": int(st.session_state.get("f_chances", 25)),
                    "prev_dribbles": int(st.session_state.get("f_dribbles", 14)),
                    "prev_touches_box": int(st.session_state.get("f_touches_box", 153)),
                    "prev_tackles": int(st.session_state.get("f_tackles", 24)),
                    "prev_rating": float(st.session_state.get("f_rating", 7.32)),
                    "to_league": in_to_league_choice.split(" (")[0],
                    "proj_mins": 3036,
                    "proj_goals": 15.0,
                    "proj_xg": 16.0,
                    "proj_assists": 5.0,
                    "proj_xa": 4.0,
                    "proj_shots": 85.0,
                    "proj_rating": 7.3,
                    "notes": player_notes.strip(),
                    "from_team": in_from_team.strip(),
                    "to_team": in_to_team.strip(),
                    "to_league_name": in_to_league_choice.split(" (")[0],
                    "trade_type": "OUT" if is_out_trade else "IN",
                    "weekly_wage": float(weekly_wage_in)
                }
                try:
                    res = requests.post(GOOGLE_SHEET_WEBAPP_URL, data=json.dumps(payload), headers={"Content-Type": "text/plain;charset=utf-8"}, timeout=30, allow_redirects=True)
                    if res.status_code in [200, 302]:
                        st.session_state["last_saved_msg"] = f"✅ 성공적으로 처리되었습니다!"
                        st.cache_data.clear()
                        st.session_state["form_key_id"] += 1
                        st.rerun()
                    else:
                        st.error("⚠️ 저장 실패")
                except Exception as e:
                    st.error(f"⚠️ 통신 오류: {e}")

    return {
        "fair_value": fair_value,
        "calc_actual_fee": calc_actual_fee,
        "overpay_pct": overpay_pct,
        "final_deal_score": final_deal_score,
        "deal_grade": "B등급",
        "player_name": player_name,
        "player_age": player_age,
        "selling_league": selling_league,
        "is_out_trade": is_out_trade,
        "status_label": status_label
    }
