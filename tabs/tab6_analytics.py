import streamlit as st
import pandas as pd
import requests
import json

def render(history_df, GOOGLE_SHEET_WEBAPP_URL):
    st.subheader("🏆 이적시장 구단별 종합 성적표 & 리그 파워 랭킹 & 데이터룸")
    st.caption("누적된 영입/방출 데이터를 종합하여 순지출과 구단별/리그별 순위를 산출하고 데이터를 관리합니다.")

    if history_df.empty or "이적시즌" not in history_df.columns:
        st.info("💡 시트에 저장된 데이터가 없습니다.")
    else:
        st.dataframe(history_df, use_container_width=True)
