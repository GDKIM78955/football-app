import streamlit as st

def render():
    st.subheader("📱 FotMob 시즌 성적 입력 및 이적 예측 프로젝션 존")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1: st.session_state["f_matches"] = st.number_input("출전 경기", 0, 60, value=int(st.session_state.get("f_matches", 1)))
    with col2: st.session_state["f_starts"] = st.number_input("선발 출전", 0, 60, value=int(st.session_state.get("f_starts", 0)))
    with col3: st.session_state["f_mins"] = st.number_input("출전 시간(분)", 0, 4500, value=int(st.session_state.get("f_mins", 90)))
    with col4: st.session_state["f_rating"] = st.number_input("FotMob 평점", 0.0, 10.0, value=float(st.session_state.get("f_rating", 6.5)))

    s1, s2, s3 = st.columns(3)
    with s1: st.session_state["f_goals"] = st.number_input("득점", 0, 50, value=int(st.session_state.get("f_goals", 0)))
    with s2: st.session_state["f_xg"] = st.number_input("기대득점 (xG)", 0.0, 50.0, value=float(st.session_state.get("f_xg", 0.0)))
    with s3: st.session_state["f_assists"] = st.number_input("도움", 0, 50, value=int(st.session_state.get("f_assists", 0)))

    st.info("💡 2번 탭의 성적 데이터는 1번 탭의 신규 저장/수정 시 구글 시트로 함께 전송되어 프로젝션의 기초 자료로 활용됩니다.")
