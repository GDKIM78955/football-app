import streamlit as st
import pandas as pd
import requests
import json
import plotly.graph_objects as go
from datetime import datetime

def render_tab2(history_df, GOOGLE_SHEET_WEBAPP_URL, LEAGUE_WEIGHTS, TRACKED_LEAGUE_NAMES, format_currency_desc, rate_krw, rate_gbp, tab1_data):
    st.subheader("📱 FotMob 스타일 시즌 성적 및 이적 예측룸 (13대 풀 스탯)")

    player_name = tab1_data.get("player_name", "선수")
    is_out_trade = tab1_data.get("is_out_trade", False)
    selling_league = tab1_data.get("selling_league", list(LEAGUE_WEIGHTS.keys())[0])

    st.markdown(f"**분석 대상 선수**: `{'🔴 방출/판매' if is_out_trade else '🔵 영입/보강'}` **{player_name if player_name else '선수명 미입력'}**")

    # 세션 상태 기반 13대 스탯 입력 필드 구성
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.markdown("##### 📌 기본 출전 및 평점")
        f_matches = st.number_input("출전 경기 (Matches)", min_value=0, max_value=60, value=int(st.session_state.get("f_matches", 28)), key="f_matches")
        f_starts = st.number_input("선발 출전 (Starts)", min_value=0, max_value=60, value=int(st.session_state.get("f_starts", 25)), key="f_starts")
        f_mins = st.number_input("출전 시간 (Minutes)", min_value=0, max_value=5000, value=int(st.session_state.get("f_mins", 2206)), key="f_mins")
        f_rating = st.number_input("FotMob 평균 평점", min_value=1.0, max_value=10.0, value=float(st.session_state.get("f_rating", 7.32)), step=0.01, key="f_rating")

        st.markdown("##### 1️⃣ 슈팅 및 득점 (Shooting & Goals)")
        f_goals = st.number_input("득점 (Goals)", min_value=0, value=int(st.session_state.get("f_goals", 16)), key="f_goals")
        f_xg = st.number_input("기대 득점 (xG)", min_value=0.0, value=float(st.session_state.get("f_xg", 17.44)), step=0.1, key="f_xg")
        f_shots = st.number_input("총 슈팅 (Shots)", min_value=0, value=int(st.session_state.get("f_shots", 88)), key="f_shots")
        f_sot = st.number_input("유효 슈팅 (On Target)", min_value=0, value=int(st.session_state.get("f_sot", 43)), key="f_sot")
        f_pk_goals = st.number_input("PK 득점 (Penalty)", min_value=0, value=int(st.session_state.get("f_pk_goals", 0)), key="f_pk_goals")

    with col_b:
        st.markdown("##### 2️⃣ 패스 및 기회 창출 (Passing & Creativity)")
        f_assists = st.number_input("도움 (Assists)", min_value=0, value=int(st.session_state.get("f_assists", 4)), key="f_assists")
        f_xa = st.number_input("기대 도움 (xA)", min_value=0.0, value=float(st.session_state.get("f_xa", 3.33)), step=0.1, key="f_xa")
        f_chances = st.number_input("기회 창출 (Chances)", min_value=0, value=int(st.session_state.get("f_chances", 25)), key="f_chances")
        f_big_chances = st.number_input("빅 찬스 메이킹", min_value=0, value=int(st.session_state.get("f_big_chances", 0)), key="f_big_chances")
        f_pass_acc = st.number_input("패스 성공률 (%)", min_value=0.0, max_value=100.0, value=float(st.session_state.get("f_pass_acc", 85.0)), step=0.1, key="f_pass_acc")

        st.markdown("##### 3️⃣ 경합 및 수비 기여 (Duels & Defending)")
        f_dribbles = st.number_input("성공한 드리블", min_value=0, value=int(st.session_state.get("f_dribbles", 14)), key="f_dribbles")
        f_touches_box = st.number_input("박스 안 터치", min_value=0, value=int(st.session_state.get("f_touches_box", 153)), key="f_touches_box")
        f_ground_duels = st.number_input("지상 경합 승률 (%)", min_value=0.0, max_value=100.0, value=float(st.session_state.get("f_ground_duels", 55.0)), step=0.1, key="f_ground_duels")
        f_aerial_duels = st.number_input("공중볼 승률 (%)", min_value=0.0, max_value=100.0, value=float(st.session_state.get("f_aerial_duels", 50.0)), step=0.1, key="f_aerial_duels")
        f_tackles = st.number_input("태클 성공", min_value=0, value=int(st.session_state.get("f_tackles", 24)), key="f_tackles")

    st.markdown("---")
    with st.expander("🥅 골키퍼 전용 상세 지표 (GK Stats)", expanded=False):
        gk1, gk2, gk3, gk4, gk5, gk6 = st.columns(6)
        with gk1: f_gk_saves = st.number_input("선방 횟수", min_value=0, value=int(st.session_state.get("f_gk_saves", 78)), key="f_gk_saves")
        with gk2: f_gk_conceded = st.number_input("실점", min_value=0, value=int(st.session_state.get("f_gk_conceded", 28)), key="f_gk_conceded")
        with gk3: f_gk_prevented = st.number_input("득점 차단 (Prevented)", value=float(st.session_state.get("f_gk_prevented", 2.45)), step=0.1, key="f_gk_prevented")
        with gk4: f_gk_cs = st.number_input("클린시트", min_value=0, value=int(st.session_state.get("f_gk_cs", 10)), key="f_gk_cs")
        with gk5: f_gk_errors = st.number_input("실점 실수", min_value=0, value=int(st.session_state.get("f_gk_errors", 0)), key="f_gk_errors")
        with gk6: f_gk_claims = st.number_input("공중볼 캐칭", min_value=0, value=int(st.session_state.get("f_gk_claims", 18)), key="f_gk_claims")
