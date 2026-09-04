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
                            "fee": int(row_data.get("실제이적료(만€)", 0)) if pd.notnull(row_data.get("실제이적료(만€)"))) else 0,
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

                        # 2번 탭 FotMob 스탯 및 골키퍼 지표 동기화
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

        if not edit_toggle and player_name.strip() and not history_df.empty and "선수명" in history_df.columns:
            dup_matches = history_df[
                (history_df["선수명"].astype(str).str.strip().str.lower() == player_name.strip().lower()) & 
                (history_df["이적시즌"].astype(str).str.strip() == season_val.strip())
            ]
            if not dup_matches.empty:
                last_dup = dup_matches.iloc[-1]
                dup_from = str(last_dup.get("원소속팀명", "미상"))
                dup_to = str(last_dup.get("이적팀명", "미상"))
                dup_fee = float(last_dup.get("실제이적료(만€)", 0))
                st.warning(f"⚠️ **중복 등록 알림**: **'{player_name.strip()}'** 선수는 이미 이번 `{season_val}` 시즌에 등록된 내역이 있습니다! (`[{dup_from} ➔ {dup_to}] | €{dup_fee:,.0f}만`)")

        c_t1, c_t2, c_t3 = st.columns(3)
        with c_t1: in_from_team = st.text_input("원소속팀명 (보내는 팀)", value=cf["from_team"], placeholder="예: 아스톤 빌라", key=f"from_team_{k_id}")
        with c_t2: in_to_team = st.text_input("이적팀명 (영입 구단)", value=cf["to_team"], placeholder="예: 아스날", key=f"to_team_{k_id}")
        with c_t3: in_to_league_choice = st.selectbox("이적팀 리그", list(LEAGUE_WEIGHTS.keys()), index=list(LEAGUE_WEIGHTS.keys()).index(cf["to_league"]) if cf["to_league"] in LEAGUE_WEIGHTS else 0, key=f"to_league_choice_{k_id}")

        is_tracked_target = any(k in in_to_league_choice for k in TRACKED_LEAGUE_NAMES)
        if is_tracked_target:
            st.caption("✅ **10대 핵심 리그 이적**: 시즌 종료 후 4번 탭 사후 검증 대상에 **자동 등록**됩니다.")
        else:
            st.caption("ℹ️ **기타 리그 이적**: 메인 결산 장부에만 기록되며, 검증 시트에는 등록되지 않습니다.")

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
            if "GK" in main_position:
                st.markdown(f"""
                - **골키퍼 실적**: 선방 `{st.session_state.get('f_gk_saves', 78)}회` / 실점 `{st.session_state.get('f_gk_conceded', 28)}` / 클린시트 `{st.session_state.get('f_gk_cs', 10)}경기`
                - **득점 차단 (선방력)**: `{st.session_state.get('f_gk_prevented', 2.45):+.2f}` (출전 {st.session_state['f_mins']:,}분)
                - **FotMob 평균 평점**: `★ {cur_rating:.2f}` ➔ **{opta_desc} (가중치 {opta_w:.2f})**
                """)
            else:
                st.markdown(f"""
                - **지난 시즌 실적**: `{st.session_state['f_goals']}골 {st.session_state['f_assists']}도움` (출전 {st.session_state['f_mins']:,}분)
                - **기대 생산력**: `xG {st.session_state['f_xg']:.2f}` / `xA {st.session_state['f_xa']:.2f}` (90분당 **{cur_p90_exp:.2f}**)
                - **FotMob 평균 평점**: `★ {cur_rating:.2f}` ➔ **{opta_desc} (가중치 {opta_w:.2f})**
                """)

        with st.expander("📚 [클릭하여 확인] 12대 가중치 전체 세부 산정 기준표 & 가이드", expanded=False):
            st.markdown("#### 1️⃣ 포지션별 나이(에이징 커브) 가중치 기준표")
            age_ref_df = pd.DataFrame({
                "나이 구간": ["19세 이하 (원더키드)", "20~23세 (유망주 성장기)", "24~27세 (전성기 피크)", "28~29세 (전성기 후반)", "30~31세 (에이징 초입)", "32~34세 (베테랑)", "35세 이상"],
                "공격수/윙어 (ST/WG/CAM)": ["1.05 (+5%)", "1.03 (+3%)", "1.00 (기준)", "0.97 (-3%)", "0.90 (-10%)", "0.80 (-20%)", "0.65 (-35%)"],
                "미드필더 (CM/CDM/FB)": ["1.03 (+3%)", "1.02 (+2%)", "1.00 (기준)", "0.98 (-2%)", "0.92 (-8%)", "0.84 (-16%)", "0.70 (-30%)"],
                "수비수/골키퍼 (CB/GK)": ["1.01 (+1%)", "1.01 (+1%)", "1.00 (기준)", "1.00 (기준)", "0.96 (-4%)", "0.90 (-10%)", "0.78 (-22%)"]
            })
            st.table(age_ref_df)

            st.markdown("#### 2️⃣ 주요 리그 난이도 가중치 기준")
            st.markdown("""
            - **1.00**: 잉글랜드 프리미어리그 (EPL 1부)
            - **0.90 ~ 0.92**: 라리가(0.92), 분데스리가(0.91), 세리에 A(0.90)
            - **0.88**: 프랑스 리그 1
            - **0.75 ~ 0.80**: 잉글랜드 챔피언십(0.80), 포르투갈(0.78), 네덜란드(0.77), 벨기에(0.75)
            - **0.60 ~ 0.68**: 브라질(0.68), 튀르키예(0.65), MLS(0.64), 스위스/오스트리아(0.62), 스코틀랜드(0.60)
            - **0.48 ~ 0.52**: 사우디 SPL(0.52), J1리그(0.50), K리그1(0.48)
            """)

            st.markdown("#### 3️⃣ 계약 형태 및 비공개 이적 처리 원칙")
            st.markdown("""
            - **비공개 이적 (Undisclosed)**: 보도된 추정치가 없으면 시장 적정가와 1:1 수렴한 것으로 간주 (평가율 0%, 기본 7.5점)
            - **단순 1년 임대**: 1년 감가상각 사용가치(20%)로 자동 환산하여 임대료와 비교
            - **FA 자유계약**: 지급 계약금(사이닝보너스) 기준 비교 및 평점 상한선 통제
            """)

        st.markdown("---")
        tm_market_value = st.number_input("트랜스퍼마르크트 시장 가치 (만 유로, €)", min_value=0, value=cf["tm"], step=50, key=f"tm_{k_id}")
        if tm_market_value > 0: st.caption(f"💡 시장가치 환산: **{format_currency_desc(tm_market_value)}**")

        is_loan_type = "임대" in transfer_type and "의무" not in transfer_type
        is_undisclosed = "비공개" in transfer_type

        fee_label = "실제 수령/지출 임대료 (Loan Fee, 만 유로, €)" if is_loan_type else ("실제 방출(판매) 이적료 (만 유로, €)" if is_out_trade else "실제 영입(지출) 이적료 (만 유로, €)")

        actual_transfer_fee = st.number_input(
            fee_label, 
            min_value=0, 
            value=0 if is_undisclosed else cf["fee"], 
            step=50, 
            key=f"fee_{k_id}",
            disabled=is_undisclosed
        )

        if is_undisclosed:
            st.info("💡 **비공개 이적 선택됨**: 실제 이적료가 공개되지 않아 시장 적정가와 동일하게 추정하여 분석합니다.")
        elif actual_transfer_fee > 0:
            st.caption(f"💡 실제금액 환산: **{format_currency_desc(actual_transfer_fee)}**")

        with st.expander("💼 [선택/수정 입력] 주급(Weekly Wage) & 연간 총비용 분석", expanded=True if cf["wage"] > 0 else False):
            weekly_wage_in = st.number_input("선수 주급 (만 유로, €/주)", min_value=0.0, value=float(cf["wage"]), step=0.5, key=f"wage_{k_id}")
            annual_wage_eur = weekly_wage_in * 52
            annual_transfer_amort = (actual_transfer_fee / 4.0) if actual_transfer_fee > 0 else 0.0
            total_annual_cost = annual_transfer_amort + annual_wage_eur
            if weekly_wage_in > 0:
                st.caption(f"📌 **주급 환산**: 주당 약 {weekly_wage_in*10000*rate_krw/100000000:.1f}억원 (£{weekly_wage_in*rate_gbp:.1f}만)")
                st.markdown(f"- **연간 총비용 (이적료 4년 분할상각 + 1년 연봉)**: `€{total_annual_cost:,.1f}만` (약 {total_annual_cost*10000*rate_krw/100000000:.0f}억원/년)")
            else:
                st.caption("ℹ️ 주급이 입력되지 않았습니다. (주급이 공개되었을 때 여기에 입력하고 수정 업데이트하세요)")

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

    base_calc_val = tm_market_value * league_w * age_w * club_w * contract_w * pos_w * vers_w * reg_w * opta_w * ttype_w * stage_w * inj_w * urg_w
    fair_value = base_calc_val * season_factor

    calc_actual_fee = fair_value if is_undisclosed else actual_transfer_fee

    diff = calc_actual_fee - fair_value
    diff_desc = format_currency_desc(abs(diff))
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

    if is_winter:
        market_min = base_calc_val * 1.15
        market_max = base_calc_val * 1.20
        market_mid = (market_min + market_max) / 2.0
        range_desc = "+15% ~ +20% 겨울 특수 프리미엄"
    else:
        market_min = base_calc_val * 1.05
        market_max = base_calc_val * 1.10
        market_mid = (market_min + market_max) / 2.0
        range_desc = "+5% ~ +10% 시장 프리미엄"

    ext_diff = calc_actual_fee - market_mid
    ext_overpay_pct = (ext_diff / market_mid) * 100 if market_mid > 0 else 0.0

    if is_undisclosed:
        ext_status_label = "⚖️ 비공개 (시장가 적정 추정)"
    elif fair_value == 0 and calc_actual_fee == 0:
        ext_status_label = "분석 대기 중"
    elif market_min <= calc_actual_fee <= market_max:
        ext_status_label = "⚖️ 시장가 적합 (Market Fair Deal)"
    elif calc_actual_fee > market_max:
        over_max_pct = ((calc_actual_fee - market_max) / market_max) * 100
        ext_status_label = f"⚠️ 시장 상한 초과 (+{over_max_pct:.1f}%)"
    else:
        under_min_pct = ((market_min - calc_actual_fee) / market_min) * 100
        ext_status_label = f"💎 시장가 대비 혜자 (-{under_min_pct:.1f}%)"

    if tm_market_value > 0 and (calc_actual_fee > 0 or is_loan_type or "FA" in transfer_type or is_undisclosed):
        base_deal_score = 7.50
        score_multiplier = 1.0 if is_out_trade else -1.0
        val_score_delta = 0.0 if is_undisclosed else max(-3.5, min(2.5, score_multiplier * (overpay_pct / 20.0)))
        rating_delta = max(-0.8, min(1.0, (cur_rating - 7.00) * 1.5))
        age_delta = max(-1.0, min(0.8, (age_w - 1.00) * 8.0))
        risk_delta = (stage_w - 1.00) * 5.0 + (inj_w - 1.00) * 5.0 + (reg_w - 1.00) * 3.0 + (urg_w - 1.00) * 2.0

        final_deal_score = round(max(1.00, min(10.00, base_deal_score + val_score_delta + rating_delta + age_delta + risk_delta)), 2)
        ext_val_score_delta = 0.0 if is_undisclosed else max(-3.5, min(2.5, score_multiplier * (ext_overpay_pct / 20.0)))
        ext_deal_score = round(max(1.00, min(10.00, base_deal_score + ext_val_score_delta + rating_delta + age_delta + risk_delta)), 2)

        def get_grade_info(score):
            if score >= 9.00: return "💎 S등급 (Masterclass Deal)", "success"
            elif score >= 8.00: return "🌟 A등급 (Excellent Deal)", "success"
            elif score >= 7.00: return "⚖️ B등급 (Solid / Fair Deal)", "info"
            elif score >= 6.00: return "⚠️ C등급 (Risky Deal)", "warning"
            else: return "🚨 D등급 (Panic / Bad Deal)", "error"

        deal_grade, deal_badge_type = get_grade_info(final_deal_score)
        ext_deal_grade, ext_badge_type = get_grade_info(ext_deal_score)
    else:
        final_deal_score = 0.00
        ext_deal_score = 0.00
        deal_grade = "분석 대기 중"
        ext_deal_grade = "분석 대기 중"

    with col2:
        st.subheader("📊 분석 결과 및 12대 세부 지표")
        display_name = player_name if player_name else "선수명 미입력"
        display_nat = f"({player_nat})" if player_nat else ""
        pos_short = main_position.split(" (")[0]
        ttype_short = transfer_type.split(" (")[0]
        reg_short = reg_status.split(" (")[0]
        urg_short = urgency_status.split(" (")[0]

        season_icon = "❄️" if is_winter else "☀️"
        transfer_route = f"[{in_from_team} ➔ {in_to_team}]" if in_from_team.strip() and in_to_team.strip() else ""
        tag_badge = "🔴 [방출/판매]" if is_out_trade else "🔵 [영입/보강]"
        mode_tag = "✏️ [기존데이터 수정]" if edit_toggle else ""
        st.markdown(f"### {tag_badge} {mode_tag} **{display_name}** {display_nat} {transfer_route} - `{pos_short}` {season_icon}")
        st.caption(f"📌 시장: **{season_val.split(' (')[0]}** | 형태: **{ttype_short}** | 쿼터: **{reg_short}** | 필요도: **{urg_short}**")

        res_c1, res_c2, res_c3, res_c4 = st.columns(4)
        with res_c1:
            st.metric("산출 적정가", f"€{fair_value:,.1f}만")
            if fair_value > 0: st.caption(f"{format_currency_desc(fair_value).split(' | ')[0]}")
        with res_c2:
            fee_display = "비공개 (추정)" if is_undisclosed else f"€{calc_actual_fee:,.1f}만"
            st.metric("실제 거래액", fee_display, delta=f"{diff:+,.1f}만 (€)" if not is_undisclosed and calc_actual_fee > 0 else None, delta_color="inverse" if not is_out_trade else "normal")
            if not is_undisclosed and calc_actual_fee > 0: st.caption(f"{format_currency_desc(calc_actual_fee).split(' | ')[0]}")
        with res_c3:
            st.metric("평가율 / 진단", f"{overpay_pct:+.1f}%" if fair_value > 0 and not is_undisclosed else "0.0%", delta=status_label.split(" ")[0])
            st.caption(status_label)
        with res_c4:
            st.metric("이적 거래 평점", f"★ {final_deal_score:.2f}", delta=deal_grade.split(" ")[0])
            st.caption(deal_grade.split(" (")[0])

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
            fig.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[50, 115])),
                showlegend=False,
                margin=dict(l=40, r=40, t=30, b=30),
                height=320
            )
            st.plotly_chart(fig, use_container_width=True)

        st.divider()

        st.markdown(f"#### 📢 **[외부 발표용] 시장가 범위 & 진단 평점 ({season_icon} {season_val.split(' ')[1] if ' ' in season_val else ''})**")

        if fair_value > 0:
            st.info(f"""
            📌 **현실 시장 거래 예상 범위 ({range_desc})**:  
            **€{market_min:,.1f}만 ~ €{market_max:,.1f}만** *(약 {((market_min*10000*rate_krw)/100000000.0):,.0f}억 ~ {((market_max*10000*rate_krw)/100000000.0):,.0f}억원)*
            """)

            ext_c1, ext_c2 = st.columns(2)
            with ext_c1:
                st.markdown(f"""
                - **외부 발표용 평점**: `★ {ext_deal_score:.2f} / 10.00`
                - **종합 판정 등급**: **{ext_deal_grade.split(' (')[0]}**
                """)
            with ext_c2:
                fee_ext_str = "비공개 (추정)" if is_undisclosed else f"€{calc_actual_fee:,.0f}만"
                st.markdown(f"""
                - **외부 시장 진단**: **{ext_status_label}**
                - **실제 거래액**: `{fee_ext_str}`
                """)

        with st.expander("🔍 [실시간 확인] 12대 세부 가중치 적용 현황표 & 누적 배율", expanded=True):
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
                    selling_league.split(" (")[0], f"만 {player_age}세 ({pos_short})", buying_club_tier.split(":")[0],
                    remaining_contract.split(" (")[0], pos_short, versatility.split(" (")[0],
                    reg_status.split(" (")[0], f"★{cur_rating:.2f} ({opta_desc.split(' (')[0]})", ttype_short,
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
    display_pname_t1 = player_name.strip() if player_name.strip() else "선수명 미입력"
    tag_btn_name_t1 = "🔴 방출(OUT) 데이터" if is_out_trade else "🔵 영입(IN) 데이터"

    btn_label_t1 = f"🔄 '{display_pname_t1}' 수정된 데이터 구글 시트에 업데이트(덮어쓰기)" if edit_toggle else f"💾 {tag_btn_name_t1} 구글 시트에 바로 저장하기 (총 48개 항목 동기화)"

    if st.button(btn_label_t1, type="primary", use_container_width=True, key="save_btn_tab1"):
        if not player_name.strip():
            st.warning("⚠️ 선수 이름을 먼저 입력해 주세요.")
        else:
            action_type = "update_existing" if edit_toggle else "save_all"
            spinner_msg = f"'{player_name}' 선수의 데이터를 구글 시트에 업데이트(수정) 중입니다..." if edit_toggle else "구글 시트에 신규 데이터를 기록 중입니다..."

            with st.spinner(spinner_msg):
                contract_desc = remaining_contract.split(" (")[0]
                nat_str = player_nat if player_nat.strip() else "미상"
                detailed_notes = f"[{'방출' if is_out_trade else '영입'}|{ttype_short}|{reg_short}|{urg_short}|UCL:{stage_w:.2f}|메디컬:{inj_w:.2f}] 계약:{contract_desc}"
                if player_notes.strip():
                    detailed_notes += f" | {player_notes.strip()}"

                is_gk = "GK" in main_position
                if is_gk:
                    detailed_notes += f" | GK[선방:{st.session_state.get('f_gk_saves', 78)}|실점:{st.session_state.get('f_gk_conceded', 28)}]"

                f_target_mins_t1 = 1440 if is_winter else 3036
                raw_lf_t1 = LEAGUE_WEIGHTS[selling_league] / (LEAGUE_WEIGHTS.get(in_to_league_choice, 1.0))
                adapt_p_t1 = max(0.80, 1.0 - (max(0.0, LEAGUE_WEIGHTS.get(in_to_league_choice, 1.0) - LEAGUE_WEIGHTS[selling_league]) * 0.45))
                final_lf_t1 = raw_lf_t1 * adapt_p_t1
                t_p90_t1 = f_target_mins_t1 / 90.0

                if not is_gk:
                    p90_xg_t1 = (float(st.session_state["f_xg"]) / f_p90) * final_lf_t1
                    p90_xa_t1 = (float(st.session_state["f_xa"]) / f_p90) * final_lf_t1
                    p90_shots_t1 = (float(st.session_state["f_shots"]) / f_p90) * final_lf_t1
                    fin_ratio_t1 = float(st.session_state["f_goals"]) / float(st.session_state["f_xg"]) if float(st.session_state["f_xg"]) > 0 else 1.0
                    pj_goals_t1 = round(p90_xg_t1 * t_p90_t1 * fin_ratio_t1, 1)
                    pj_xg_t1 = round(p90_xg_t1 * t_p90_t1, 2)
                    pj_assists_t1 = round(p90_xa_t1 * t_p90_t1, 1)
                    pj_xa_t1 = round(p90_xa_t1 * t_p90_t1, 2)
                    pj_shots_t1 = round(p90_shots_t1 * t_p90_t1, 0)
                else:
                    pj_goals_t1 = 0.0; pj_xg_t1 = 0.0; pj_assists_t1 = 0.0; pj_xa_t1 = 0.0; pj_shots_t1 = 0.0

                pj_rating_t1 = round(max(6.0, cur_rating - (1.0 - final_lf_t1) * 0.9), 2)

                payload = {
                    "action": action_type,
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
                    "fee": float(calc_actual_fee),
                    "fair_val": round(fair_value, 1),
                    "diff": round(diff, 1),
                    "status": status_label,
                    "deal_score": float(final_deal_score),
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
                    "prev_rating": float(cur_rating),
                    "to_league": in_to_league_choice.split(" (")[0],
                    "proj_mins": int(f_target_mins_t1),
                    "proj_goals": float(pj_goals_t1),
                    "proj_xg": float(pj_xg_t1),
                    "proj_assists": float(pj_assists_t1),
                    "proj_xa": float(pj_xa_t1),
                    "proj_shots": float(pj_shots_t1),
                    "proj_rating": float(pj_rating_t1),
                    "notes": detailed_notes,
                    "from_team": in_from_team.strip(),
                    "to_team": in_to_team.strip(),
                    "to_league_name": in_to_league_choice.split(" (")[0],
                    "trade_type": "OUT" if is_out_trade else "IN",
                    "weekly_wage": float(weekly_wage_in) if 'weekly_wage_in' in locals() else 0.0,
                    "gk_saves": int(st.session_state.get("f_gk_saves", 0)) if is_gk else 0,
                    "gk_conceded": int(st.session_state.get("f_gk_conceded", 0)) if is_gk else 0,
                    "gk_prevented": float(st.session_state.get("f_gk_prevented", 0.0)) if is_gk else 0.0,
                    "gk_cs": int(st.session_state.get("f_gk_cs", 0)) if is_gk else 0,
                    "gk_errors": int(st.session_state.get("f_gk_errors", 0)) if is_gk else 0,
                    "gk_claims": int(st.session_state.get("f_gk_claims", 0)) if is_gk else 0
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
                        st.session_state["last_saved_msg"] = f"✅ '{player_name}' 선수의 데이터가 성공적으로 {'수정(업데이트)' if edit_toggle else '저장'}되었습니다!"
                        st.cache_data.clear()
                        st.session_state["form_key_id"] += 1
                        st.rerun()
                    else:
                        st.error(f"⚠️ 저장/수정 실패: {res_json.get('message', '통신 오류')}")
                except Exception as e:
                    st.error(f"⚠️ 저장 오류: {e}")

    return {
        "fair_value": fair_value,
        "calc_actual_fee": calc_actual_fee,
        "overpay_pct": overpay_pct,
        "final_deal_score": final_deal_score,
        "deal_grade": deal_grade,
        "player_name": player_name,
        "player_age": player_age,
        "selling_league": selling_league,
        "is_out_trade": is_out_trade
    }
