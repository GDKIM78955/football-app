import streamlit as st
import pandas as pd
import requests
import json

def render_tab4(VAL_SHEET_CSV_URL, GOOGLE_SHEET_WEBAPP_URL):
    st.subheader("🎯 이적 첫 시즌 실제 성적 입력 & 모델 예측 정확도 사후 검증")
    st.caption("시즌 종료 후 선수가 실제로 기록한 최종 스탯(xG, xA 포함)을 입력하여 모델 예측치와의 오차율 및 적중률을 산출하고 [검증데이터] 시트에 업데이트합니다.")

    @st.cache_data(ttl=5)
    def fetch_validation_data():
        try:
            df = pd.read_csv(VAL_SHEET_CSV_URL)
            if not df.empty and "선수명" in df.columns:
                return df
        except Exception:
            pass
        return pd.DataFrame()

    val_df = fetch_validation_data()

    if val_df.empty or len(val_df) == 0 or "이적시즌" not in val_df.columns:
        st.info("💡 **아직 [검증데이터] 시트에 저장된 데이터가 없습니다.**\n\n- 2번 탭에서 10대 핵심 리그 이적 선수를 저장하시면 이곳에 자동으로 나타납니다.")
    else:
        def check_status(row):
            act_r = str(row.get("실제평점", "")).strip()
            act_m = str(row.get("실제출전시간", "")).strip()
            if act_r != "" and act_r != "nan" and act_m != "" and act_m != "nan" and act_m != "0":
                return "✅ 검증 완료"
            return "⏳ 검증 대기"

        val_df["입력상태"] = val_df.apply(check_status, axis=1)

        st.markdown("#### 1️⃣ 검증할 시즌 및 미입력 선수 필터링")
        available_seasons = list(val_df["이적시즌"].dropna().unique())

        v_top1, v_top2 = st.columns([1, 1])
        with v_top1:
            sel_val_season = st.selectbox("이적 시즌 선택", available_seasons, key="val_sel_season")

        filtered_season_df = val_df[val_df["이적시즌"] == sel_val_season]

        total_in_season = len(filtered_season_df)
        completed_cnt = len(filtered_season_df[filtered_season_df["입력상태"] == "✅ 검증 완료"])
        pending_cnt = total_in_season - completed_cnt
        progress_pct = (completed_cnt / total_in_season * 100) if total_in_season > 0 else 0.0

        with v_top2:
            st.info(f"📊 **`{sel_val_season}` 검증 진행도**: **총 {total_in_season}명 중 {completed_cnt}명 완료 / {pending_cnt}명 대기** (`{progress_pct:.0f}%` 달성)")

        show_pending_only = st.checkbox("⏳ 실제 성적 미입력(검증 대기) 선수만 모아보기", value=True if pending_cnt > 0 else False, key="filter_pending_only")

        if show_pending_only:
            target_player_pool = filtered_season_df[filtered_season_df["입력상태"] == "⏳ 검증 대기"]
        else:
            target_player_pool = filtered_season_df

        available_players = list(target_player_pool["선수명"].dropna().unique()) if "선수명" in target_player_pool.columns else []

        if not available_players:
            if show_pending_only:
                st.success("🎉 이번 시즌 모든 10대 리그 영입 선수의 실제 성적 입력 및 검증이 100% 완료되었습니다!")
            else:
                st.warning("선택하신 조건에 해당하는 선수가 없습니다.")
        else:
            sel_val_player = st.selectbox(
                f"선수 선택 ({len(available_players)}명 대상)", 
                available_players, 
                key="val_sel_player"
            )

            target_row = target_player_pool[target_player_pool["선수명"] == sel_val_player].iloc[-1]

            p_pos = str(target_row.get("포지션", "CB"))
            p_to_l = str(target_row.get("이적리그", "EPL"))
            proj_m = float(target_row.get("예측출전시간", 3000))
            proj_g = float(target_row.get("예측득점", 0))
            proj_xg = float(target_row.get("예측xG", 0))
            proj_a = float(target_row.get("예측도움", 0))
            proj_xa = float(target_row.get("예측xA", 0))
            proj_r = float(target_row.get("예측평점", 7.0))
            curr_status = str(target_row.get("입력상태", "⏳ 검증 대기"))

            st.markdown("---")
            st.markdown(f"#### 2️⃣ **'{sel_val_player}'** 선수의 [모델 예측치] vs [시즌 실제 기록 입력] ({curr_status})")
            st.caption(f"📌 포지션: **{p_pos}** | 활약 리그: **{p_to_l}**")

            st.markdown("##### 📌 모델이 예측했던 기대 수치")
            pm1, pm2, pm3, pm4, pm5 = st.columns(5)
            pm1.metric("예측 출전시간", f"{int(proj_m):,}분")
            pm2.metric("예측 득점 (xG)", f"{proj_g:.1f}골", delta=f"xG {proj_xg:.2f}")
            pm3.metric("예측 도움 (xA)", f"{proj_a:.1f}도움", delta=f"xA {proj_xa:.2f}")
            pm4.metric("예측 공격포인트", f"{proj_g + proj_a:.1f}P")
            pm5.metric("예측 평점", f"★ {proj_r:.2f}")

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("##### 📥 시즌 종료 후 실제 최종 기록 입력 (FotMob 기준)")

            exist_act_mins = int(target_row.get("실제출전시간", 0)) if pd.notnull(target_row.get("실제출전시간")) and str(target_row.get("실제출전시간")).strip() not in ["", "nan"] else int(proj_m)
            exist_act_goals = int(target_row.get("실제득점", 0)) if pd.notnull(target_row.get("실제득점")) and str(target_row.get("실제득점")).strip() not in ["", "nan"] else int(round(proj_g))
            exist_act_xg = float(target_row.get("실제xG", 0.0)) if pd.notnull(target_row.get("실제xG")) and str(target_row.get("실제xG")).strip() not in ["", "nan"] else float(proj_xg)
            exist_act_assists = int(target_row.get("실제도움", 0)) if pd.notnull(target_row.get("실제도움")) and str(target_row.get("실제도움")).strip() not in ["", "nan"] else int(round(proj_a))
            exist_act_xa = float(target_row.get("실제xA", 0.0)) if pd.notnull(target_row.get("실제xA")) and str(target_row.get("실제xA")).strip() not in ["", "nan"] else float(proj_xa)
            exist_act_rating = float(target_row.get("실제평점", 0.0)) if pd.notnull(target_row.get("실제평점")) and str(target_row.get("실제평점")).strip() not in ["", "nan"] else float(proj_r)
            exist_act_notes = str(target_row.get("검증메모", "")) if pd.notnull(target_row.get("검증메모")) else ""

            in_ac1, in_ac2, in_ac3, in_ac4, in_ac5, in_ac6 = st.columns(6)
            with in_ac1: act_mins_val = st.number_input("실제 출전 시간(분)", 0, 4500, value=exist_act_mins, step=90, key="val_act_mins")
            with in_ac2: act_goals_val = st.number_input("실제 득점(Goals)", 0, 60, value=exist_act_goals, step=1, key="val_act_goals")
            with in_ac3: act_xg_val = st.number_input("실제 기대득점(xG)", 0.0, 50.0, value=exist_act_xg, step=0.01, key="val_act_xg")
            with in_ac4: act_assists_val = st.number_input("실제 도움(Assists)", 0, 40, value=exist_act_assists, step=1, key="val_act_assists")
            with in_ac5: act_xa_val = st.number_input("실제 기대도움(xA)", 0.0, 30.0, value=exist_act_xa, step=0.01, key="val_act_xa")
            with in_ac6: act_rating_val = st.number_input("실제 FotMob 평균 평점", 4.0, 10.0, value=exist_act_rating, step=0.01, key="val_act_rating")

            act_notes_val = st.text_input("사후 검증 스카우팅 총평 / 비고", value=exist_act_notes, placeholder="예: 리그 적응 성공, 모델 예측 xG 및 평점 정확도 매우 우수", key="val_act_notes")

            rating_error = abs(act_rating_val - proj_r)
            rating_accuracy = max(0.0, round((1.0 - (rating_error / 1.5)) * 100, 1))

            mins_diff = act_mins_val - proj_m
            goals_diff = act_goals_val - proj_g
            xg_diff = act_xg_val - proj_xg
            assists_diff = act_assists_val - proj_a
            xa_diff = act_xa_val - proj_xa

            st.markdown("---")
            st.markdown("#### 3️⃣ **모델 예측 vs 실제 성적 1:1 정밀 대칭 비교 리포트**")

            comp_col1, comp_col2, comp_col3, comp_col4, comp_col5 = st.columns(5)
            comp_col1.metric("평점 적중률", f"{rating_accuracy}%", delta=f"{act_rating_val - proj_r:+.2f}점 오차")
            comp_col2.metric("실제 출전시간", f"{act_mins_val:,}분", delta=f"{mins_diff:+,.0f}분 차이")
            comp_col3.metric("실제 득점 (xG)", f"{act_goals_val}골", delta=f"xG 오차 {xg_diff:+.2f}")
            comp_col4.metric("실제 도움 (xA)", f"{act_assists_val}도움", delta=f"xA 오차 {xa_diff:+.2f}")
            comp_col5.metric("실제 공격포인트", f"{act_goals_val + act_assists_val}P", delta=f"{(act_goals_val + act_assists_val) - (proj_g + proj_a):+.1f}P 차이")

            if st.button("🚀 '검증데이터' 시트에 실제 최종 기록 업데이트하기", type="primary", use_container_width=True, key="update_actual_btn"):
                with st.spinner("구글 시트에 최종 실제 성적을 업데이트 중입니다..."):
                    update_payload = {
                        "action": "update_actual",
                        "season": sel_val_season,
                        "name": sel_val_player,
                        "act_mins": int(act_mins_val),
                        "act_goals": int(act_goals_val),
                        "act_xg": float(act_xg_val),
                        "act_assists": int(act_assists_val),
                        "act_xa": float(act_xa_val),
                        "act_rating": float(act_rating_val),
                        "notes": act_notes_val
                    }
                    try:
                        res = requests.post(
                            GOOGLE_SHEET_WEBAPP_URL, 
                            data=json.dumps(update_payload), 
                            headers={"Content-Type": "text/plain;charset=utf-8"}, 
                            timeout=30, 
                            allow_redirects=True
                        )
                        res_json = res.json()
                        if res_json.get("status") == "success":
                            st.success(f"✅ '{sel_val_player}' 선수의 실제 최종 성적이 성공적으로 기록되었습니다!")
                            st.cache_data.clear()
                            st.rerun()
                        else:
                            st.error(f"⚠️ 업데이트 실패: {res_json.get('message')}")
                    except Exception as e:
                        st.error(f"⚠️ 통신 오류: {e}")

        st.markdown("---")
        st.markdown("#### 📋 **[검증데이터] 시트 전체 누적 현황표 (상태 배지 포함)**")

        display_val_cols = ["입력상태", "이적시즌", "선수명", "포지션", "이적리그", "예측출전시간", "실제출전시간", "예측득점", "실제득점", "예측평점", "실제평점", "검증메모"]
        avail_v_cols = [c for c in display_val_cols if c in val_df.columns]
        st.dataframe(val_df[avail_v_cols], use_container_width=True)
