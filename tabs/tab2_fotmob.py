import streamlit as st
import pandas as pd
import requests
import json
from datetime import datetime

def render(GOOGLE_SHEET_WEBAPP_URL):
    st.subheader("📱 FotMob 스타일 시즌 스탯 입력 & 이적 첫 시즌 성적 프로젝션")
    
    # 세션 상태 안전 기본값 확보
    if "custom_proj_mins" not in st.session_state:
        st.session_state["custom_proj_mins"] = 3000
    if "f_mins" not in st.session_state:
        st.session_state["f_mins"] = 90
    if "f_rating" not in st.session_state:
        st.session_state["f_rating"] = 6.50

    winter_data_source = st.radio(
        "📋 데이터 입력 기준 모드 선택",
        [
            "☀️ 직전 풀 시즌 스탯 (여름 이적 표준 / 1년 전체)",
            "❄️ 이번 시즌 전반기 스탯 (겨울 이적 표준, 8월~1월)",
            "⚠️ 직전 풀 시즌 스탯 (겨울 이적생 중 전반기 300~400분 미만 결장/부상 시)"
        ],
        index=0,
        horizontal=True
    )

    is_winter_mode = "겨울" in winter_data_source
    
    f_c1, f_c2, f_c3 = st.columns(3)
    with f_c1: f_pos = st.selectbox("선수 포지션 분류", ["⚽ 필드 플레이어 (공격수/미드필더/수비수)", "🧤 골키퍼 (Goalkeeper)"], index=0)
    with f_c2: f_from_l = st.selectbox("원소속 리그 (기록 기준)", ["잉글랜드 프리미어리그 (EPL 1부)"], index=0)
    with f_c3: f_to_l = st.selectbox("이적할 리그", ["잉글랜드 프리미어리그 (EPL 1부)"], index=0)
    
    f_target_mins = st.number_input(
        "최종 적용될 예상 출전 시간(분)", 
        min_value=0, 
        max_value=4500, 
        value=int(st.session_state["custom_proj_mins"]), 
        step=90
    )
    st.session_state["custom_proj_mins"] = f_target_mins
    
    st.divider()
    st.markdown(f"### 📥 FotMob 시즌 실제 기록 입력")

    b1, b2, b3, b4 = st.columns(4)
    with b1: in_matches = st.number_input("출전 경기 (Matches)", 0, 60, value=30)
    with b2: in_starts = st.number_input("선발 출전 (Starts)", 0, 60, value=25)
    with b3: in_mins = st.number_input("출전 시간 (Minutes)", 0, 4500, value=int(st.session_state["f_mins"]))
    with b4: in_rating = st.number_input("FotMob 평균 평점", 0.0, 10.0, value=float(st.session_state["f_rating"]), step=0.01)

    st.session_state["f_mins"] = in_mins
    st.session_state["f_rating"] = in_rating

    if "골키퍼" not in f_pos:
        s1, s2, s3, s4, s5 = st.columns(5)
        with s1: in_goals = st.number_input("득점 (Goals)", 0, 50, value=5)
        with s2: in_xg = st.number_input("기대 득점 (xG)", 0.0, 50.0, value=4.5, step=0.01)
        with s3: in_shots = st.number_input("총 슈팅 (Shots)", 0, 200, value=30)
        with s4: in_sot = st.number_input("유효 슈팅 (On Target)", 0, 100, value=15)
        with s5: in_pk_goals = st.number_input("PK 득점 (Penalty)", 0, 20, value=0)

        p1, p2, p3, p4, p5 = st.columns(5)
        with p1: in_assists = st.number_input("도움 (Assists)", 0, 50, value=3)
        with p2: in_xa = st.number_input("기대 도움 (xA)", 0.0, 50.0, value=2.5, step=0.01)
        with p3: in_chances = st.number_input("기회 창출 (Chances)", 0, 150, value=20)
        with p4: in_big_chances = st.number_input("빅 찬스 메이킹", 0, 50, value=2)
        with p5: in_pass_pct = st.number_input("패스 성공률 (%)", 0.0, 100.0, value=85.0, step=0.1)
    else:
        in_goals = 0; in_xg = 0.0; in_assists = 0; in_xa = 0.0

    st.divider()
    if st.button("💾 FotMob 스탯 저장하기", type="primary", use_container_width=True):
        st.success("✅ FotMob 스탯이 임시 반영되었습니다. (1번 탭의 저장 버튼을 통해 최종 반영됩니다)")
