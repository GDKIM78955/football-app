import streamlit as st
import pandas as pd
import requests
import json

def render(validation_df, GOOGLE_SHEET_WEBAPP_URL):
    st.subheader("🎯 이적 첫 시즌 실제 성적 입력 & 모델 예측 정확도 사후 검증")
    st.caption("시즌 종료 후 선수가 실제로 기록한 최종 스탯을 입력하여 모델 예측치와의 오차율을 산출합니다.")

    if validation_df.empty or "이적시즌" not in validation_df.columns:
        st.info("💡 아직 검증 데이터 시트에 등록된 선수가 없습니다. (10대 리그 이적 시 자동 등록됩니다)")
    else:
        st.dataframe(validation_df, use_container_width=True)
