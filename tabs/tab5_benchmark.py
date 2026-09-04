import streamlit as st
import pandas as pd

def render(history_df):
    st.subheader("👥 신규 이적생 vs 과거 유사 이적 선수 다각도 벤치마크 (Multi-Comps)")
    st.caption("새로운 시즌 영입 선수의 프로필을 과거 시트에 누적된 다른 선수들의 실제 사례와 교차 비교합니다.")

    if history_df.empty or "선수명" not in history_df.columns:
        st.info("💡 아직 시트에 누적된 과거 이적 데이터가 없습니다.")
    else:
        past_players = list(history_df["선수명"].dropna().unique())
        if past_players:
            sel = st.selectbox("비교할 과거 선수 선택", past_players)
            st.write(f"선택한 선수: {sel}")
