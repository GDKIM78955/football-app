import streamlit as st
import pandas as pd

def render(history_df):
    st.subheader("🔍 과거 유사 이적 사례 비교 (Top 5 / Top 10)")
    if history_df.empty:
        st.warning("⚠️ 시트에 저장된 기존 데이터가 없습니다.")
    else:
        st.dataframe(history_df, use_container_width=True)
        st.info("💡 현재 등록된 선수들과 포지션 및 이적료가 유사한 과거 데이터베이스 사례를 비교하는 공간입니다.")
