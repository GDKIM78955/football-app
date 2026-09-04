import streamlit as st
import pandas as pd
import requests
import json
import plotly.graph_objects as go
from datetime import datetime

def render_tab2(history_df, GOOGLE_SHEET_WEBAPP_URL, LEAGUE_WEIGHTS, TRACKED_LEAGUE_NAMES, format_currency_desc, rate_krw, rate_gbp, tab1_data):
    st.subheader("📱 FotMob 스타일 시즌 성적 및 이적 예측룸 (13대 풀 스탯)")

    col_s1, col_s2 = st.columns([2, 1])
    with col_s1:
        st.markdown("##### 🔍 비교 및 분석 대상 선수 선택")
        if history_df.empty or "선수명" not in history_df.columns:
            st.info("💡 등록된 선수 히스토리가 없습니다. 아래에서 직접 스탯을 입력하거나 1번 탭에서 평가를 진행하세요.")
            p_list = []
        else:
            p_list = list(history_df["선수명"].dropna().unique())
        
        sel_player = st.selectbox("DB 선수 불러오기 (선택 시 자동 매핑)", ["직접 입력 / 커스텀"] + p_list, key="tab2_player_select")

    def_mins = 2206; def_goals = 16; def_xg = 17.44; def_assists = 4; def_xa = 3.33
    def_rating = 7.32; def_matches = 28; def_starts = 25; def_shots = 88; def_sot = 43
    def_chances = 25; def_dribbles = 14; def_touches = 153; def_tackles = 24

    if sel_player != "직접 입력 / 커스텀" and not history_df.empty:
        matched_rows = history_df[history_df["선수명"] == sel_player]
        if not matched_rows.empty:
            r = matched_rows.iloc[-1]
            def_mins = int(r.get("이전_출전시간", 2206)) if pd.notnull(r.get("이전_출전시간")) else 2206
            def_goals = int(r.get("이전_골", 16)) if pd.notnull(r.get("이전_골")) else 16
            def_xg = float(r.get("이전_xG", 17.44)) if pd.notnull(r.get("이전_xG")) else 17.44
            def_assists = int(r.get("이전_도움", 4)) if pd.notnull(r.get("이전_도움")) else 4
            def_xa = float(r.get("이전_xA", 3.33)) if pd.notnull(r.get("이전_xA")) else 3.33
            def_rating = float(r.get("이전_FotMob평점", 7.32)) if pd.notnull(r.get("이전_FotMob평점")) else 7.32
            def_matches = int(r.get("이전_출전경기", 28)) if pd.notnull(r.get("이전_출전경기")) else 28
            def_starts = int(r.get("이전_선발", 25)) if pd.notnull(r.get("이전_선발")) else 25
            def_shots = int(r.get("이전_총슈팅", 88)) if pd.notnull(r.get("이전_총슈팅")) else 88
            def_sot = int(r.get("이전_유효슈팅", 43)) if pd.notnull(r.get("이전_유효슈팅")) else 43
            def_chances = int(r.get("이전_찬스메이킹", 25)) if pd.notnull(r.get("이전_찬스메이킹")) else 25
            def_dribbles = int(r.get("이전_성공드리블", 14)) if pd.notnull(r.get("이전_성공드리블")) else 14
            def_touches = int(r.get("이전_박스터치", 153)) if pd.notnull(r.get("이전_박스터치")) else 153
            def_tackles = int(r.get("이전_태클성공", 24)) if pd.notnull(r.get("이전_태클성공")) else 24

    st.markdown("---")
    st.markdown("#### ⚽ 직전 시즌 13대 핵심 스탯 입력룸")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("##### 📌 기본 출전 및 평점 지표")
        f_matches = st.number_input("출전 경기 (Matches)", min_value=0, max_value=60, value=def_matches, key="t2_matches")
        f_starts = st.number_input("선발 출전 (Starts)", min_value=0, max_value=60, value=def_starts, key="t2_starts")
        f_mins = st.number_input("출전 시간 (Minutes)", min_value=0, max_value=5000, value=def_mins, key="t2_mins")
        f_rating = st.number_input("FotMob 평균 평점", min_value=1.0, max_value=10.0, value=def_rating, step=0.01, key="t2_rating")

        st.markdown("##### 1️⃣ 슈팅 및 득점 (Shooting & Goals)")
        f_goals = st.number_input("득점 (Goals)", min_value=0, value=def_goals, key="t2_goals")
        f_xg = st.number_input("기대 득점 (xG)", min_value=0.0, value=def_xg, step=0.1, key="t2_xg")
        f_shots = st.number_input("총 슈팅 (Shots)", min_value=0, value=def_shots, key="t2_shots")
        f_sot = st.number_input("유효 슈팅 (On Target)", min_value=0, value=def_sot, key="t2_sot")
        f_pk_goals = st.number_input("PK 득점 (Penalty)", min_value=0, value=0, key="t2_pk")

    with col2:
        st.markdown("##### 2️⃣ 패스 및 기회 창출 (Passing & Creativity)")
        f_assists = st.number_input("도움 (Assists)", min_value=0, value=def_assists, key="t2_assists")
        f_xa = st.number_input("기대 도움 (xA)", min_value=0.0, value=def_xa, step=0.1, key="t2_xa")
        f_chances = st.number_input("기회 창출 (Chances)", min_value=0, value=def_chances, key="t2_chances")
        f_big_chances = st.number_input("빅 찬스 메이킹", min_value=0, value=0, key="t2_big_chances")
        f_pass_acc = st.number_input("패스 성공률 (%)", min_value=0.0, max_value=100.0, value=85.0, step=0.1, key="t2_pass_acc")

        st.markdown("##### 3️⃣ 경합 및 수비 기여 (Duels & Defending)")
        f_dribbles = st.number_input("성공한 드리블", min_value=0, value=def_dribbles, key="t2_dribbles")
        f_touches_box = st.number_input("박스 안 터치", min_value=0, value=def_touches, key="t2_touches")
        f_ground_duels = st.number_input("지상 경합 승률 (%)", min_value=0.0, max_value=100.0, value=55.0, step=0.1, key="t2_g_duels")
        f_aerial_duels = st.number_input("공중볼 승률 (%)", min_value=0.0, max_value=100.0, value=50.0, step=0.1, key="t2_a_duels")
        f_tackles = st.number_input("태클 성공", min_value=0, value=def_tackles, key="t2_tackles")

    st.markdown("---")
    with st.expander("🥅 골키퍼 전용 상세 지표 (GK Stats)", expanded=False):
        gk1, gk2, gk3, gk4, gk5, gk6 = st.columns(6)
        with gk1: st.number_input("선방 횟수", min_value=0, value=78, key="t2_gk_saves")
        with gk2: st.number_input("실점", min_value=0, value=28, key="t2_gk_conceded")
        with gk3: st.number_input("득점 차단 (Prevented)", value=2.45, step=0.1, key="t2_gk_prevented")
        with gk4: st.number_input("클린시트", min_value=0, value=10, key="t2_gk_cs")
        with gk5: st.number_input("실점 실수", min_value=0, value=0, key="t2_gk_errors")
        with gk6: st.number_input("공중볼 캐칭", min_value=0, value=18, key="t2_gk_claims")
