import streamlit as st
import pandas as pd
import plotly.graph_objects as go

def render_tab5(history_df, LEAGUE_WEIGHTS, format_currency_desc, tab1_data):
    st.subheader("👥 신규 이적생 vs 과거 유사 이적 선수 다각도 벤치마크 (Multi-Comps)")
    st.caption("새로운 시즌 영입 선수의 프로필(나이, 포지션, 이적료 규모, 생산력)을 과거 시트에 누적된 다른 선수들의 실제 사례와 1:1 및 다차원으로 정밀 비교합니다.")

    if history_df.empty or len(history_df) == 0 or "선수명" not in history_df.columns:
        st.info("💡 **아직 과거 누적 데이터가 없습니다.**\n\n1번 및 2번 탭에서 선수 데이터를 2명 이상 저장하시면 과거 선수들과의 1:1 교차 비교 및 벤치마크 매칭이 활성화됩니다.")
    else:
        st.markdown("#### 1️⃣ 신규 분석 대상 선수 프로필 설정 (1번 탭 데이터 자동 연동)")

        p_curr_name = tab1_data.get("player_name", "")
        if not p_curr_name.strip():
            p_curr_name = "신규 영입 대상 선수"
        
        p_curr_age = int(tab1_data.get("player_age", 28))
        p_curr_pos = tab1_data.get("selling_league", "중앙 / 수비형 미드필더") # 포지션 값 안전 확보
        selling_league = tab1_data.get("selling_league", list(LEAGUE_WEIGHTS.keys())[0])
        p_curr_fee = float(tab1_data.get("calc_actual_fee", 5000.0))
        p_curr_score = float(tab1_data.get("final_deal_score", 7.50))
        
        f_mins_val = float(st.session_state.get("f_mins", 2206))
        f_p90 = (f_mins_val / 90.0) if f_mins_val > 0 else 1.0
        p_curr_p90 = (float(st.session_state.get("f_xg", 0.0)) + float(st.session_state.get("f_xa", 0.0))) / f_p90
        p_curr_rating = float(st.session_state.get("f_rating", 7.32))

        c_prof1, c_prof2, c_prof3, c_prof4 = st.columns(4)
        c_prof1.metric("선수명 & 나이", f"{p_curr_name}", f"만 {p_curr_age}세")
        c_prof2.metric("출발 리그", f"{selling_league.split(' ')[1] if ' ' in selling_league else selling_league}")
        c_prof3.metric("실제 거래액", f"€{p_curr_fee:,.0f}만", f"평점 ★{p_curr_score:.2f}")
        c_prof4.metric("90분당 xG+xA / 평점", f"{p_curr_p90:.2f}", f"FotMob ★{p_curr_rating:.2f}")

        st.markdown("---")
        st.markdown("#### 2️⃣ 과거 유사 프로필 선수 1:1 직접 선택 대조 (Head-to-Head)")

        past_player_names = [str(n).strip() for n in history_df["선수명"].dropna().unique() if str(n).strip() not in ["", "nan"]]

        if not past_player_names:
            st.info("💡 과거 시트에 유효한 선수 데이터가 아직 없습니다.")
        else:
            selected_past_player = st.selectbox(
                "과거 비교 대상 선수 선택",
                past_player_names,
                index=0,
                key="bench_player_select"
            )

            past_target = history_df[history_df["선수명"] == selected_past_player].iloc[-1]

            t_name = str(past_target.get("선수명", "선수"))
            t_season = str(past_target.get("이적시즌", "26/27"))
            t_age = int(past_target.get("나이", 25)) if pd.notnull(past_target.get("나이")) else 25
            t_pos = str(past_target.get("포지션", "CB"))
            t_league = str(past_target.get("원소속리그", "EPL"))
            t_fee = float(past_target.get("실제이적료(만€)", 0))
            t_fair = float(past_target.get("산출적정가(만€)", 0))
            t_score = float(past_target.get("이적평점", 7.50))
            t_xg = float(past_target.get("직전_xG", 0.0)) if pd.notnull(past_target.get("직전_xG")) else 0.0
            t_xa = float(past_target.get("직전_xA", 0.0)) if pd.notnull(past_target.get("직전_xA")) else 0.0
            t_mins = float(past_target.get("직전_출전시간", 2500)) if pd.notnull(past_target.get("직전_출전시간")) else 2500.0
            t_rating = float(past_target.get("직전_평점", 7.0)) if pd.notnull(past_target.get("직전_평점")) else 7.0
            t_p90 = (t_xg + t_xa) / (t_mins / 90.0) if t_mins > 0 else 0.0

            df_bench = pd.DataFrame({
                "스카우팅 비교 항목": [
                    "이적 시즌 (Season)", "나이 (만 나이)", "주 포지션", "출발 리그",
                    "실제 거래액", "데이터 기준 적정가", "이적 총 평점 (10점 만점)",
                    "FotMob 평균 평점", "90분당 기대 생산력 (xG+xA/90)"
                ],
                f"신규 대상: {p_curr_name}": [
                    f"{st.session_state.get('current_form', {}).get('season', '26/27').split(' (')[0]}",
                    f"만 {p_curr_age}세", f"중앙/수비형 미드필더",
                    f"{selling_league.split(' ')[1] if ' ' in selling_league else selling_league}",
                    f"€{p_curr_fee:,.0f}만 ({format_currency_desc(p_curr_fee).split(' | ')[0]})",
                    f"€{tab1_data.get('fair_value', 0):,.1f}만",
                    f"★ {p_curr_score:.2f} / 10.00", f"★ {p_curr_rating:.2f}", f"{p_curr_p90:.2f}"
                ],
                f"과거 비교: {t_name} ({t_season})": [
                    f"{t_season}", f"만 {t_age}세", f"{t_pos}", f"{t_league}",
                    f"€{t_fee:,.0f}만 ({format_currency_desc(t_fee).split(' | ')[0]})",
                    f"€{t_fair:,.1f}만", f"★ {t_score:.2f} / 10.00", f"★ {t_rating:.2f}", f"{t_p90:.2f}"
                ],
                "비교 격차 / 인사이트": [
                    "-", f"{p_curr_age - t_age:+d}세", "포지션 대조", "리그 대조",
                    f"{p_curr_fee - t_fee:+,.0f}만 €", f"{tab1_data.get('fair_value', 0) - t_fair:+,.1f}만 €",
                    f"{p_curr_score - t_score:+.2f}점", f"{p_curr_rating - t_rating:+.2f}점", f"{p_curr_p90 - t_p90:+.2f}"
                ]
            })

            st.table(df_bench)

            st.markdown("##### ⚔️ **두 선수의 1:1 스카우팅 프로필 레이더 비교**")
            bench_fig = go.Figure()
            comp_categories = ['이적료 규모', '이적 평점', '직전 FotMob 평점', '90분당 생산력', '나이(적정성)']

            p_val_scaled = [min(100, p_curr_fee/1000*10), p_curr_score*10, p_curr_rating*10, min(100, p_curr_p90*100), (35-p_curr_age)*5]
            t_val_scaled = [min(100, t_fee/1000*10), t_score*10, t_rating*10, min(100, t_p90*100), (35-t_age)*5]

            bench_fig.add_trace(go.Scatterpolar(r=p_val_scaled + [p_val_scaled[0]], theta=comp_categories + [comp_categories[0]], fill='toself', name=p_curr_name, line=dict(color='#1f77b4')))
            bench_fig.add_trace(go.Scatterpolar(r=t_val_scaled + [t_val_scaled[0]], theta=comp_categories + [comp_categories[0]], fill='toself', name=f"{t_name} ({t_season})", line=dict(color='#ff7f0e')))
            bench_fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), height=350, margin=dict(l=40, r=40, t=30, b=30))
            st.plotly_chart(bench_fig, use_container_width=True)
