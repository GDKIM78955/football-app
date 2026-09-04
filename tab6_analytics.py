import streamlit as st
import pandas as pd
import requests
import json

def render_tab6(history_df, GOOGLE_SHEET_WEBAPP_URL, format_currency_desc):
    st.subheader("🏆 이적시장 구단별 종합 성적표 & 리그 파워 랭킹 & 데이터룸")
    st.caption("시트에 누적된 영입(IN) 및 방출(OUT) 데이터를 종합하여 순지출(Net Spend)과 '이적료 가중 평균 평점' 기반의 구단/리그별 순위를 산출하고, 오기입된 데이터를 관리 및 삭제합니다.")

    if history_df.empty or len(history_df) == 0 or "이적시즌" not in history_df.columns:
        st.info("💡 **아직 구글 시트에 누적된 이적 데이터가 없습니다.**\n\n1번 및 2번 탭에서 팀명을 포함하여 이적 데이터를 저장하시면 이곳에 구단별 성적표 및 리그별/전체 통합 파워 랭킹이 자동으로 집계됩니다.")
    else:
        rank_mode = st.radio("분석 모드 선택", ["🏢 구단별 이적시장 종합 성적표 (Club Report Card)", "🌍 리그별 / 10대 리그 전체 통합 파워 랭킹 (Power Rankings)", "🛠️ 저장 데이터 조회 및 삭제 관리 (Data Management)"], horizontal=True)

        st.markdown("---")

        if "구단별" in rank_mode:
            st.markdown("#### 🏢 **특정 구단의 이적시장 결산 성적표 (IN/OUT & 순지출)**")

            c_rc1, c_rc2 = st.columns(2)
            all_seasons = list(history_df["이적시즌"].dropna().unique())
            with c_rc1:
                sel_season_club = st.selectbox("조회할 이적 시즌", ["전체 시즌"] + all_seasons, index=0, key="report_season_sel")

            club_filtered_df = history_df if sel_season_club == "전체 시즌" else history_df[history_df["이적시즌"] == sel_season_club]

            to_teams = [str(t).strip() for t in club_filtered_df["이적팀명"].dropna().unique() if str(t).strip() not in ["", "nan"]] if "이적팀명" in club_filtered_df.columns else []
            from_teams = [str(t).strip() for t in club_filtered_df["원소속팀명"].dropna().unique() if str(t).strip() not in ["", "nan"]] if "원소속팀명" in club_filtered_df.columns else []
            all_club_names = sorted(list(set(to_teams + from_teams)))

            if not all_club_names:
                st.warning("⚠️ 아직 시트에 구단명이 입력된 이적 데이터가 없습니다.")
            else:
                with c_rc2:
                    sel_team_name = st.selectbox("조회할 구단(팀) 선택", all_club_names, key="report_team_sel")

                team_in_df = club_filtered_df[club_filtered_df["이적팀명"].astype(str).str.strip() == sel_team_name].copy() if "이적팀명" in club_filtered_df.columns else pd.DataFrame()
                team_out_df = club_filtered_df[club_filtered_df["원소속팀명"].astype(str).str.strip() == sel_team_name].copy() if "원소속팀명" in club_filtered_df.columns else pd.DataFrame()

                total_in_spent = team_in_df["실제이적료(만€)"].astype(float).sum() if not team_in_df.empty and "실제이적료(만€)" in team_in_df.columns else 0.0
                total_out_income = team_out_df["실제이적료(만€)"].astype(float).sum() if not team_out_df.empty and "실제이적료(만€)" in team_out_df.columns else 0.0
                net_spend = total_in_spent - total_out_income

                def get_adjusted_deal_score(row, is_buy_side):
                    recorded_score = float(row.get("이적평점", 7.50))
                    orig_trade_type = str(row.get("거래구분", "IN")).strip()
                    if is_buy_side and orig_trade_type == "OUT":
                        return round(max(1.0, min(10.0, 15.00 - recorded_score)), 2)
                    elif not is_buy_side and orig_trade_type == "IN":
                        return round(max(1.0, min(10.0, 15.00 - recorded_score)), 2)
                    return recorded_score

                if not team_in_df.empty:
                    team_in_df["이적평점"] = team_in_df.apply(lambda r: get_adjusted_deal_score(r, is_buy_side=True), axis=1)
                if not team_out_df.empty:
                    team_out_df["이적평점"] = team_out_df.apply(lambda r: get_adjusted_deal_score(r, is_buy_side=False), axis=1)

                all_team_trades = pd.concat([team_in_df, team_out_df])
                if not all_team_trades.empty and "이적평점" in all_team_trades.columns:
                    fees = all_team_trades["실제이적료(만€)"].astype(float)
                    scores = all_team_trades["이적평점"].astype(float)
                    if fees.sum() > 0:
                        weights = fees.apply(lambda x: max(x, 500.0))
                        weighted_avg_score = (scores * weights).sum() / weights.sum()
                    else:
                        weighted_avg_score = scores.mean()
                else:
                    weighted_avg_score = 7.50

                if weighted_avg_score >= 8.5: club_grade = "💎 S등급 (이적시장 대성공)"
                elif weighted_avg_score >= 7.5: club_grade = "🌟 A등급 (매우 훌륭한 이적시장)"
                elif weighted_avg_score >= 6.8: club_grade = "⚖️ B등급 (준수한 실리 운영)"
                elif weighted_avg_score >= 6.0: club_grade = "⚠️ C등급 (다소 아쉬운 이적시장)"
                else: club_grade = "🚨 D등급 (패닉 / 재정 낭비)"

                st.markdown(f"### 🛡️ **'{sel_team_name}'** 이적시장 종합 성적표 ({sel_season_club})")

                t_m1, t_m2, t_m3, t_m4 = st.columns(4)
                t_m1.metric("총 영입 지출액 (IN)", f"€{total_in_spent:,.0f}만", f"{len(team_in_df)}명 영입")
                t_m2.metric("총 방출 수익 (OUT)", f"€{total_out_income:,.0f}만", f"{len(team_out_df)}명 방출")
                t_m3.metric("순지출 (Net Spend)", f"€{net_spend:+,.0f}만", delta=f"{format_currency_desc(abs(net_spend)).split(' | ')[0]} {'지출' if net_spend >= 0 else '수익'}", delta_color="inverse")
                t_m4.metric("이적시장 가중 평점", f"★ {weighted_avg_score:.2f} / 10.00", club_grade.split(" ")[0])
                st.caption(f"🏆 최종 구단 이적시장 종합 판정: **{club_grade}**")

                st.markdown("<br>", unsafe_allow_html=True)

                sub_tab1, sub_tab2 = st.tabs([f"🔵 영입 명단 ({len(team_in_df)}명)", f"🔴 방출 명단 ({len(team_out_df)}명)"])
                display_cols = ["선수명", "포지션", "원소속팀명", "이적팀명", "실제이적료(만€)", "산출적정가(만€)", "이적평점", "스카우팅메모"]

                with sub_tab1:
                    if team_in_df.empty: st.info("영입(IN) 데이터가 없습니다.")
                    else: st.dataframe(team_in_df[[c for c in display_cols if c in team_in_df.columns]], use_container_width=True)

                with sub_tab2:
                    if team_out_df.empty: st.info("방출(OUT) 데이터가 없습니다.")
                    else: st.dataframe(team_out_df[[c for c in display_cols if c in team_out_df.columns]], use_container_width=True)

        elif "리그별" in rank_mode:
            st.markdown("#### 🌍 **리그별 & 10대 리그 전체 통합 파워 랭킹 (Power Rankings)**")

            c_rk1, c_rk2 = st.columns(2)
            all_seasons_rk = list(history_df["이적시즌"].dropna().unique())
            with c_rk1:
                sel_season_rk = st.selectbox("조회할 이적 시즌", ["전체 시즌"] + all_seasons_rk, index=0, key="rk_season_sel")

            league_filtered_df = history_df if sel_season_rk == "전체 시즌" else history_df[history_df["이적시즌"] == sel_season_rk]
            auto_detected_leagues = [str(l).strip() for l in league_filtered_df["이적팀리그"].dropna().unique() if str(l).strip() not in ["", "nan"]] if "이적팀리그" in league_filtered_df.columns else []

            if not auto_detected_leagues:
                st.warning("⚠️ 아직 시트에 '이적팀리그'가 기록된 데이터가 없습니다.")
            else:
                league_options = ["🌐 [전체 10개 리그 통합 순위표 (All Leagues)]"] + sorted(auto_detected_leagues)
                with c_rk2:
                    sel_league_name = st.selectbox("조회할 리그 범위 선택", league_options, key="rk_league_sel")

                is_all_leagues = "전체 10개 리그" in sel_league_name
                l_target_df = league_filtered_df if is_all_leagues else league_filtered_df[league_filtered_df["이적팀리그"] == sel_league_name]

                if not l_target_df.empty:
                    unique_teams = sorted(list(l_target_df["이적팀명"].astype(str).str.strip().unique())) if "이적팀명" in l_target_df.columns else []
                    team_stat_rows = []

                    def get_adj_score(r, is_buy):
                        rec = float(r.get("이적평점", 7.50))
                        orig = str(r.get("거래구분", "IN")).strip()
                        if is_buy and orig == "OUT": return round(max(1.0, min(10.0, 15.00 - rec)), 2)
                        elif not is_buy and orig == "IN": return round(max(1.0, min(10.0, 15.00 - rec)), 2)
                        return rec

                    for t_name in unique_teams:
                        in_trades = l_target_df[l_target_df["이적팀명"].astype(str).str.strip() == t_name].copy()
                        out_trades = league_filtered_df[league_filtered_df["원소속팀명"].astype(str).str.strip() == t_name].copy() if "원소속팀명" in league_filtered_df.columns else pd.DataFrame()

                        in_spent = in_trades["실제이적료(만€)"].astype(float).sum() if not in_trades.empty and "실제이적료(만€)" in in_trades.columns else 0.0
                        out_income = out_trades["실제이적료(만€)"].astype(float).sum() if not out_trades.empty and "실제이적료(만€)" in out_trades.columns else 0.0
                        net_val = in_spent - out_income

                        if not in_trades.empty: in_trades["이적평점"] = in_trades.apply(lambda r: get_adj_score(r, True), axis=1)
                        if not out_trades.empty: out_trades["이적평점"] = out_trades.apply(lambda r: get_adj_score(r, False), axis=1)

                        all_trades = pd.concat([in_trades, out_trades])
                        if not all_trades.empty and "이적평점" in all_trades.columns:
                            fees = all_trades["실제이적료(만€)"].astype(float)
                            scores = all_trades["이적평점"].astype(float)
                            w_score = (scores * fees.apply(lambda x: max(x, 500.0))).sum() / fees.apply(lambda x: max(x, 500.0)).sum() if fees.sum() > 0 else scores.mean()
                        else:
                            w_score = 7.50

                        t_league_label = str(in_trades["이적팀리그"].iloc[0]).strip() if not in_trades.empty and "이적팀리그" in in_trades.columns else ""

                        team_stat_rows.append({
                            "이적팀명": t_name, "소속리그": t_league_label, "가중이적평점": round(w_score, 2),
                            "영입(IN)": len(in_trades), "방출(OUT)": len(out_trades),
                            "총영입액(만€)": int(in_spent), "총방출액(만€)": int(out_income), "순지출(만€)": int(net_val)
                        })

                    ranked_df = pd.DataFrame(team_stat_rows).sort_values(by="가중이적평점", ascending=False).reset_index(drop=True)
                    ranked_df.index = ranked_df.index + 1
                    ranked_df.index.name = "순위 (Rank)"

                    st.markdown(f"### 🏆 **{sel_league_name}** 구단 이적시장 파워 랭킹 ({sel_season_rk})")
                    show_cols = ["이적팀명", "소속리그", "가중이적평점", "영입(IN)", "방출(OUT)", "총영입액(만€)", "총방출액(만€)", "순지출(만€)"] if is_all_leagues else ["이적팀명", "가중이적평점", "영입(IN)", "방출(OUT)", "총영입액(만€)", "총방출액(만€)", "순지출(만€)"]
                    st.dataframe(ranked_df[show_cols], use_container_width=True)

        else:
            st.markdown("#### 🛠️ **구글 시트 저장 데이터 조회 및 삭제 관리 (Data Management)**")
            del_c1, del_c2 = st.columns(2)
            del_seasons = list(history_df["이적시즌"].dropna().unique())
            with del_c1:
                sel_del_season = st.selectbox("삭제 대상 이적 시즌 선택", del_seasons, key="del_season_sel")

            del_season_df = history_df[history_df["이적시즌"] == sel_del_season]
            del_players = list(del_season_df["선수명"].dropna().unique()) if "선수명" in del_season_df.columns else []

            with del_c2:
                sel_del_player = st.selectbox("삭제할 선수 선택", del_players, key="del_player_sel") if del_players else None

            if sel_del_player:
                target_del_row = del_season_df[del_season_df["선수명"] == sel_del_player].iloc[-1]
                st.warning(f"⚠️ 삭제 대상: **'{sel_del_player}'** (시즌: `{sel_del_season}` | 이적료: `€{target_del_row.get('실제이적료(만€)', 0):,.0f}만`)")

                if st.button(f"🗑️ '{sel_del_player}' 데이터 구글 시트에서 영구 삭제하기", type="primary", use_container_width=True, key="del_exec_btn"):
                    with st.spinner("구글 시트에서 데이터를 삭제 중입니다..."):
                        del_payload = {"action": "delete_row", "season": sel_del_season, "name": sel_del_player}
                        try:
                            res = requests.post(GOOGLE_SHEET_WEBAPP_URL, data=json.dumps(del_payload), headers={"Content-Type": "text/plain;charset=utf-8"}, timeout=30, allow_redirects=True)
                            if res.json().get("status") == "success":
                                st.success(f"✅ '{sel_del_player}' 선수의 데이터가 성공적으로 삭제되었습니다!")
                                st.cache_data.clear()
                                st.rerun()
                            else:
                                st.error("⚠️ 삭제 실패")
                        except Exception as e:
                            st.error(f"⚠️ 통신 오류: {e}")

            st.markdown("---")
            st.markdown("##### 📋 **전체 메인 시트 저장 데이터 목록**")
            st.dataframe(history_df, use_container_width=True)
