import streamlit as st
import pandas as pd

def render(history_df):
    st.subheader("🔍 과거 유사 이적 사례 검색 및 벤치마크 비교 (Comps TOP 5 & 10)")
    st.caption("구글 시트에 누적된 이전 이적 데이터 중 유사한 과거 사례를 매칭합니다.")

    if history_df.empty or "선수명" not in history_df.columns:
        st.info("💡 아직 시트에 누적된 과거 이적 데이터가 없습니다. 1번 탭에서 데이터를 저장해 보세요.")
    else:
        st.dataframe(history_df, use_container_width=True)
