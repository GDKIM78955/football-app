import streamlit as st
import pandas as pd
import requests
import json
import plotly.graph_objects as go
from datetime import datetime

def render_tab2(history_df, GOOGLE_SHEET_WEBAPP_URL, LEAGUE_WEIGHTS, TRACKED_LEAGUE_NAMES, format_currency_desc, rate_krw, rate_gbp, tab1_data):
    st.subheader("📱 FotMob 스타일 시즌 성적 및 이적 후 프로젝션 예측룸")
    
    player_name = tab1_data.get("player_name", "선수")
    is_out_trade = tab1_data.get("is_out_trade", False)
    
    st.markdown(f"**분석 대상 선수**: `{'🔴 방출/판매' if is_out_trade else '🔵 영입/보강'}` **{player_name if player_name else '선수명 미입력'}**")

    with st.expander("📊 지난 시즌 FotMob 스타일 상세 스탯 입력 (직전 시즌)", expanded=True):
        st.markdown("##### 📌 기본 출전 및 평점 지표")
        c1, c2, c3, c4 = st.columns(4)
        with c1: f_matches = st.number_input("출전 경기 (Matches)", min_value=0, max_value=60, value=int(st.session_state.get("f_matches", 28)), key="f_matches")
        with c2: f_starts = st.number_input("선발 출전 (Starts)", min_value=0, max_value=60, value=int(st.session_state.get("f_starts", 25)), key="f_starts")
        with c3: f_mins = st.number_input("출전 시간 (Minutes)", min_value=0, max_value=5000, value=int(st.session_state.get("f_mins", 2206)), key="f_mins")
        with c4: f_rating = st.number_input("FotMob 평균 평점", min_value=1.0, max_value=10.0, value=float(st.session_state.get("f_rating", 7.32)), step=0.01, key="f_rating")

        st.markdown("##### 1️⃣ 슈팅 및 득점 (Shooting & Goals)")
        sc1, sc2, sc3, sc4, sc5 = st.columns(5)
        with sc1: f_goals = st.number_input("득점 (Goals)", min_value=0, value=int(st.session_state.get("f_goals", 16)), key="f_goals")
        with sc2: f_xg = st.number_input("기대 득점 (xG)", min_value=0.0, value=float(st.session_state.get("f_xg", 17.44)), step=0.1, key="f_xg")
        with sc3: f_shots = st.number_input("총 슈팅 (Shots)", min_value=0, value=int(st.session_state.get("f_shots", 88)), key="f_shots")
        with sc4: f_sot = st.number_input("유효 슈팅 (On Target)", min_value=0, value=int(st.session_state.get("f_sot", 43)), key="f_sot")
        with sc5: f_pk_goals = st.number_input("PK 득점 (Penalty)", min_value=0, value=int(st.session_state.get("f_pk_goals", 0)), key="f_pk_goals")

        st.markdown("##### 2️⃣ 패스 및 기회 창출 (Passing & Creativity)")
        pc1, pc2, pc3, pc4, pc5 = st.columns(5)
        with pc1: f_assists = st.number_input("도움 (Assists)", min_value=0, value=int(st.session_state.get("f_assists", 4)), key="f_assists")
        with pc2: f_xa = st.number_input("기대 도움 (xA)", min_value=0.0, value=float(st.session_state.get("f_xa", 3.33)), step=0.1, key="f_xa")
        with pc3: f_chances = st.number_input("기회 창출 (Chances)", min_value=0, value=int(st.session_state.get("f_chances", 25)), key="f_chances")
        with pc4: f_big_chances = st.number_input("빅 찬스 메이킹", min_value=0, value=int(st.session_state.get("f_big_chances", 0)), key="f_big_chances")
        with pc5: f_pass_acc = st.number_input("패스 성공률 (%)", min_value=0.0, max_value=100.0, value=float(st.session_state.get("f_pass_acc", 85.0)), step=0.1, key="f_pass_acc")

        st.markdown("##### 3️⃣ 경합 및 수비 기여 (Duels & Defending)")
        dc1, dc2, dc3, dc4, dc5 = st.columns(5)
        with dc1: f_dribbles = st.number_input("성공한 드리블", min_value=0, value=int(st.session_state.get("f_dribbles", 14)), key="f_dribbles")
        with dc2: f_touches_box = st.number_input("박스 안 터치", min_value=0, value=int(st.session_state.get("f_touches_box", 153)), key="f_touches_box")
        with dc3: f_ground_duels = st.number_input("지상 경합 승률 (%)", min_value=0.0, max_value=100.0, value=float(st.session_state.get("f_ground_duels", 55.0)), step=0.1, key="f_ground_duels")
        with dc4: f_aerial_duels = st.number_input("공중볼 승률 (%)", min_value=0.0, max_value=100.0, value=float(st.session_state.get("f_aerial_duels", 50.0)), step=0.1, key="f_aerial_duels")
        with dc5: f_tackles = st.number_input("태클 성공", min_value=0, value=int(st.session_state.get("f_tackles", 24)), key="f_tackles")

    st.markdown("---")
    st.info("💡 1번 탭에서 선수를 불러온 후, 위 스탯들이 정상적으로 반영되었는지 2번 탭에서 확인하실 수 있습니다.")
