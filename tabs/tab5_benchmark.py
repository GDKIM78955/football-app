import streamlit as st

def render(history_df):
    st.subheader("👥 신규 이적생 vs 과거 선수 다각도 벤치마크 교차 비교")
    if history_df.empty:
        st.warning("⚠️ 비교할 데이터가 부족합니다.")
    else:
        st.info("💡 두 선수를 선택하여 가중치와 스탯을 방사형 레이더 차트로 교차 비교하는 공간입니다.")
