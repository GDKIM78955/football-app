import streamlit as st
import pandas as pd
import requests
import json
from datetime import datetime

def render_tab2(history_df, GOOGLE_SHEET_WEBAPP_URL, LEAGUE_WEIGHTS, TRACKED_LEAGUE_NAMES, format_currency_desc, rate_krw, rate_gbp, tab1_data):
    st.subheader("📱 FotMob 스타일 시즌 스탯 입력 & 이적 첫 시즌 성적 프로젝션")

    # tab1에서 넘어온 주요 데이터 추출
    player_name = tab1_data.get("player_name", "")
    player_age = tab1_data.get("player_age", 28)
    selling_league = tab1_data.get("selling_league", list(LEAGUE_WEIGHTS.keys())[0])
    calc_actual_fee = tab1_data.get("calc_actual_fee", 0.0)
    fair_value = tab1_data.get("fair_value", 0.0)
    diff = tab1_data.get("diff", 0.0)
    overpay_pct = tab1_data.get("overpay_pct", 0.0)
    status_label = tab1_data.get("status_label", "")
    final_deal_score = tab1_data.get("final_deal_score", 0.0)
    is_out_trade = tab1_data.get("is_out_trade", False)

    k_id = st.session_state.get("form_key_id", 0)

    st.info("""
    💡 **FotMob 과거 기록 입력 가이드**:
    * **여름 이적 (Summer)**: 직전 풀 시즌(1년 전체, 약 2,500~3,200분) 실제 기록을 입력합니다.
    * **겨울 이적 (Winter - 원칙)**: 이번 시즌 **전반기(8월~1월, 약 1,200~1,600분)** 기록을 입력합니다.
    * **겨울 이적 (Winter - 예외)**: 전반기에 장기 부상이나 결장으로 **출전 시간이 300~400분 미만**인 경우 표본 왜곡 방지를 위해 **'직전 풀 시즌'** 기록을 입력해 주세요.
    """)

    winter_data_source = st.radio(
        "📋 데이터 입력 기준 모드 선택",
        [
            "☀️ 직전 풀 시즌 스탯 (여름 이적 표준 / 1년 전체)",
            "❄️ 이번 시즌 전반기 스탯 (겨울 이적 표준, 8월~1월)",
            "⚠️ 직전 풀 시즌 스탯 (겨울 이적생 중 전반기 300~400분 미만 결장/부상 시)"
        ],
        index=1 if "겨울" in str(st.session_state.get("season", "")) else 0,
        horizontal=True,
        key=f"global_data_source_radio_{k_id}"
    )

    is_winter_mode = "겨울" in winter_data_source
    default_proj_mins = 1440 if is_winter_mode else 3036

    f_c1, f_c2, f_c3, f_c4 = st.columns(4)
    with f_c1: f_pos = st.selectbox("선수 포지션 분류", ["⚽ 필드 플레이어 (공격수/미드필더/수비수)", "🧤 골키퍼 (Goalkeeper)"], index=0, key=f"f_tab_pos_{k_id}")
    with f_c2: f_from_l = st.selectbox("원소속 리그 (기록 기준)", list(LEAGUE_WEIGHTS.keys()), index=list(LEAGUE_WEIGHTS.keys()).index(selling_league) if selling_league in LEAGUE_WEIGHTS else 0, key=f"f_tab_from_l_{k_id}")
    with f_c3: f_to_l = st.selectbox("이적할 리그", list(LEAGUE_WEIGHTS.keys()), index=0, key=f"f_tab_to_l_{k_id}")
    with f_c4: f_target_mins = st.number_input("이적 팀 예상 출전 시간(분)", min_value=450, max_value=4500, value=min(int(default_proj_mins), 4500), step=90, key=f"f_tab_target_mins_{k_id}")

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
    st.markdown(f"### 📥 FotMob 시즌 실제 기록 입력 (`{winter_data_source.split(' (')[0]}` 기준)")

    b1, b2, b3, b4 = st.columns(4)
    with b1: in_matches = st.number_input("출전 경기 (Matches)", 1, 60, value=min(int(st.session_state.get("f_matches", 28)), 60), key=f"in_matches_box_{k_id}")
    with b2: in_starts = st.number_input("선발 출전 (Starts)", 0, 60, value=min(int(st.session_state.get("f_starts", 25)), 60), key=f"in_starts_box_{k_id}")
    with b3: in_mins = st.number_input("출전 시간 (Minutes)", 90, 4500, value=min(int(st.session_state.get("f_mins", 2206)), 4500), key=f"in_mins_box_{k_id}")
    with b4: in_rating = st.number_input("FotMob 평균 평점", 5.0, 10.0, value=float(st.session_state.get("f_rating", 7.32)), step=0.01, key=f"in_rating_box_{k_id}")

    st.session_state["f_mins"] = in_mins
    st.session_state["f_rating"] = in_rating
    st.session_state["f_matches"] = in_matches
    st.session_state["f_starts"] = in_starts

    base_p90 = in_mins / 90.0 if in_mins > 0 else 1.0
    target_p90 = f_target_mins / 90.0

    if "골키퍼" not in f_pos:
        st.markdown("#### 1️⃣ 슈팅 및 득점 (Shooting & Goals)")
        s1, s2, s3, s4, s5 = st.columns(5)
        with s1: in_goals = st.number_input("득점 (Goals)", 0, 50, value=min(int(st.session_state.get("f_goals", 16)), 50), key=f"in_goals_box_{k_id}")
        with s2: in_xg = st.number_input("기대 득점 (xG)", 0.0, 50.0, value=min(float(st.session_state.get("f_xg", 17.44)), 50.0), step=0.01, key=f"in_xg_box_{k_id}")
        with s3: in_shots = st.number_input("총 슈팅 (Shots)", 0, 200, value=min(int(st.session_state.get("f_shots", 88)), 200), key=f"in_shots_box_{k_id}")
        with s4: in_sot = st.number_input("유효 슈팅 (On Target)", 0, 100, value=min(int(st.session_state.get("f_sot", 43)), 100), key=f"in_sot_box_{k_id}")
        with s5: in_pk_goals = st.number_input("PK 득점 (Penalty)", 0, 20, 0, key=f"in_pk_box_{k_id}")

        st.session_state["f_goals"] = in_goals
        st.session_state["f_xg"] = in_xg
        st.session_state["f_shots"] = in_shots
        st.session_state["f_sot"] = in_sot

        st.markdown("#### 2️⃣ 패스 및 기회 창출 (Passing & Creativity)")
        p1, p2, p3, p4, p5 = st.columns(5)
        with p1: in_assists = st.number_input("도움 (Assists)", 0, 50, value=min(int(st.session_state.get("f_assists", 4)), 50), key=f"in_assists_box_{k_id}")
        with p2: in_xa = st.number_input("기대 도움 (xA)", 0.0, 50.0, value=min(float(st.session_state.get("f_xa", 3.33)), 50.0), step=0.01, key=f"in_xa_box_{k_id}")
        with p3: in_chances = st.number_input("기회 창출 (Chances)", 0, 150, value=min(int(st.session_state.get("f_chances", 25)), 150), key=f"in_chances_box_{k_id}")
        with p4: in_big_chances = st.number_input("빅 찬스 메이킹", 0, 50, 2, key=f"in_bc_box_{k_id}")
        with p5: in_pass_pct = st.number_input("패스 성공률 (%)", 30.0, 100.0, 88.2, 0.1, key=f"in_pass_pct_box_{k_id}")

        st.session_state["f_assists"] = in_assists
        st.session_state["f_xa"] = in_xa
        st.session_state["f_chances"] = in_chances

        st.markdown("#### 3️⃣ 경합 및 수비 기여 (Duels & Defending)")
        d1, d2, d3, d4, d5 = st.columns(5)
        with d1: in_dribbles = st.number_input("성공한 드리블", 0, 100, value=min(int(st.session_state.get("f_dribbles", 14)), 100), key=f"in_dribbles_box_{k_id}")
        with d2: in_touches_box = st.number_input("박스 안 터치", 0, 300, value=min(int(st.session_state.get("f_touches_box", 153)), 300), key=f"in_touches_box_{k_id}")
        with d3: in_duels_pct = st.number_input("지상 경합 승률 (%)", 20.0, 100.0, 62.4, 0.1, key=f"in_duels_box_{k_id}")
        with d4: in_aerial_pct = st.number_input("공중볼 승률 (%)", 20.0, 100.0, 65.8, 0.1, key=f"in_aerial_box_{k_id}")
        with d5: in_tackles = st.number_input("태클 성공", 0, 150, value=min(int(st.session_state.get("f_tackles", 24)), 150), key=f"in_tackles_box_{k_id}")

        st.session_state["f_dribbles"] = in_dribbles
        st.session_state["f_touches_box"] = in_touches_box
        st.session_state["f_tackles"] = in_tackles

    else:
        st.markdown("#### 🧤 골키퍼 실제 지표 입력 (Goalkeeping)")
        gk1, gk2, gk3 = st.columns(3)
        with gk1: in_gk_saves = st.number_input("선방 (Saves)", 0, 250, value=int(st.session_state.get("f_gk_saves", 78)), key=f"in_gk_saves_box_{k_id}")
        with gk2: in_gk_conceded = st.number_input("실점 수", 0, 120, value=int(st.session_state.get("f_gk_conceded", 28)), key=f"in_gk_conceded_box_{k_id}")
        with gk3: in_gk_prevented = st.number_input("득점 차단", -20.0, 30.0, value=float(st.session_state.get("f_gk_prevented", 2.45)), step=0.01, key=f"in_gk_prevented_box_{k_id}")

        gk4, gk5, gk6 = st.columns(3)
        with gk4: in_gk_cs = st.number_input("클린 시트", 0, 35, value=int(st.session_state.get("f_gk_cs", 10)), key=f"in_gk_cs_box_{k_id}")
        with gk5: in_gk_errors = st.number_input("골로 이어진 실수", 0, 15, value=int(st.session_state.get("f_gk_errors", 0)), key=f"in_gk_errors_box_{k_id}")
        with gk6: in_gk_claims = st.number_input("공중볼 캐칭", 0, 80, value=int(st.session_state.get("f_gk_claims", 18)), key=f"in_gk_claims_box_{k_id}")

        st.session_state["f_gk_saves"] = in_gk_saves
        st.session_state["f_gk_conceded"] = in_gk_conceded
        st.session_state["f_gk_prevented"] = in_gk_prevented
        st.session_state["f_gk_cs"] = in_gk_cs
        st.session_state["f_gk_errors"] = in_gk_errors
        st.session_state["f_gk_claims"] = in_gk_claims

        in_goals = 0; in_xg = 0.0; in_shots = 0; in_sot = 0; in_assists = 0; in_xa = 0.0
        in_chances = 0; in_dribbles = 0; in_touches_box = 0; in_tackles = 0

    st.divider()

    if "골키퍼" not in f_pos:
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

        season_type_desc = "후반기 잔여 시즌(약 16~19경기)" if is_winter_mode else "1시즌 풀 타임"
        st.markdown(f"### 🎯 **FotMob 스타일 이적 첫 시즌 성적 예측 리포트 (필드 플레이어 - {season_type_desc})**")
        st.caption(f"이적 환경: **{f_from_l.split(' ')[1]}** ➔ **{f_to_l.split(' ')[1]}** | 최종 환산 계수: **{final_l_factor:.2f}x** ({adapt_desc})")

        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("예상 평점 (Rating)", f"★ {proj_rating:.2f}", delta=f"{proj_rating - in_rating:+.2f}")
        m2.metric("예상 득점 (xG)", f"{proj_goals:.0f} 골", delta=f"xG {proj_xg:.2f}")
        m3.metric("예상 도움 (xA)", f"{proj_assists:.0f} 도움", delta=f"xA {proj_xa:.2f}")
        m4.metric("예상 공격포인트", f"{proj_goals + proj_assists:.0f} P", delta=f"{proj_goals:.0f}G+{proj_assists:.0f}A")
        m5.metric("예상 슈팅 (유효)", f"{int(proj_shots)} 회", delta=f"유효 {int(proj_sot)}회")

    else:
        proj_gk_saves = round((in_gk_saves / base_p90) * target_p90 * (1.0 / raw_l_factor), 0)
        proj_gk_conceded = round((in_gk_conceded / base_p90) * target_p90 * (1.0 / final_l_factor), 0)
        proj_gk_prevented = round((in_gk_prevented / base_p90) * target_p90 * final_l_factor, 2)
        proj_gk_cs = round((in_gk_cs / base_p90) * target_p90 * final_l_factor, 0)
        proj_rating = round(max(6.0, in_rating - (1.0 - final_l_factor) * 0.9), 2)
        proj_goals = 0.0; proj_xg = 0.0; proj_assists = 0.0; proj_xa = 0.0; proj_shots = 0.0

        season_type_desc = "후반기 잔여 시즌" if is_winter_mode else "1시즌 풀 타임"
        st.markdown(f"### 🧤 **골키퍼 성적 예측 리포트 ({season_type_desc})**")

        gk_m1, gk_m2, gk_m3, gk_m4, gk_m5 = st.columns(5)
        gk_m1.metric("예상 평점", f"★ {proj_rating:.2f}")
        gk_m2.metric("예상 클린 시트", f"{int(proj_gk_cs)} 경기")
        gk_m3.metric("예상 득점 차단", f"{proj_gk_prevented:+.2f}")
        gk_m4.metric("예상 선방", f"{int(proj_gk_saves)} 회")
        gk_m5.metric("예상 실점", f"{int(proj_gk_conceded)} 실점")

    st.markdown("---")
    tag_btn_name = "🔴 방출(OUT) 데이터" if is_out_trade else "🔵 영입(IN) 데이터"
    
    if st.button(f"💾 {tag_btn_name} 구글 시트에 저장하기", type="primary", use_container_width=True, key=f"save_btn_tab2_{k_id}"):
        if not player_name.strip():
            st.warning("⚠️ 선수 이름을 [💰 적정 이적료 평가] 탭에 먼저 입력해 주세요.")
        else:
            with st.spinner("구글 시트에 거래 데이터를 기록 중입니다..."):
                payload = {
                    "action": "save_all",
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "season": st.session_state.get("current_form", {}).get("season", "26/27 여름 (Summer)"),
                    "name": player_name,
                    "nat": str(st.session_state.get("current_form", {}).get("nat", "미상")),
                    "age": int(player_age),
                    "pos": main_position.split(" (")[0],
                    "from_league": selling_league.split(" (")[0],
                    "buying_tier": "Tier 2",
                    "transfer_type": "일반 완전 이적",
                    "tm_val": float(st.session_state.get("current_form", {}).get("tm", 4500)),
                    "fee": float(calc_actual_fee),
                    "fair_val": round(fair_value, 1),
                    "diff": round(diff, 1),
                    "status": status_label,
                    "deal_score": float(final_deal_score),
                    "prev_matches": int(in_matches),
                    "prev_mins": int(in_mins),
                    "prev_goals": int(in_goals),
                    "prev_xg": float(in_xg),
                    "prev_assists": int(in_assists),
                    "prev_xa": float(in_xa),
                    "prev_shots": int(in_shots),
                    "prev_sot": int(in_sot if 'in_sot' in locals() else 0),
                    "prev_chances": int(in_chances),
                    "prev_dribbles": int(in_dribbles),
                    "prev_touches_box": int(in_touches_box),
                    "prev_tackles": int(in_tackles),
                    "prev_rating": float(in_rating),
                    "to_league": f_to_l.split(" (")[0],
                    "proj_mins": int(f_target_mins),
                    "proj_goals": float(proj_goals),
                    "proj_xg": float(proj_xg),
                    "proj_assists": float(proj_assists),
                    "proj_xa": float(proj_xa),
                    "proj_shots": float(proj_shots),
                    "proj_rating": float(proj_rating),
                    "notes": f"[{'방출' if is_out_trade else '영입'}]",
                    "from_team": str(st.session_state.get("current_form", {}).get("from_team", "")),
                    "to_team": str(st.session_state.get("current_form", {}).get("to_team", "")),
                    "to_league_name": f_to_l.split(" (")[0],
                    "trade_type": "OUT" if is_out_trade else "IN",
                    "weekly_wage": float(st.session_state.get("current_form", {}).get("wage", 0.0))
                }

                try:
                    res = requests.post(GOOGLE_SHEET_WEBAPP_URL, data=json.dumps(payload), headers={"Content-Type": "text/plain;charset=utf-8"}, timeout=30, allow_redirects=True)
                    if res.status_code in [200, 302]:
                        st.session_state["last_saved_msg"] = f"✅ '{player_name}' 선수의 데이터가 성공적으로 저장되었습니다!"
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error("⚠️ 저장 실패")
                except Exception as e:
                    st.error(f"⚠️ 통신 오류: {e}")
