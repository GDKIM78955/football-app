import streamlit as st

def render(val_df, webhook_url):
    st.subheader("🎯 이적 첫 시즌 실제 성적 & 사후 검증 존 ([검증데이터] 2번 시트 연동)")
    if val_df.empty:
        st.warning("⚠️ 2번 시트(검증데이터)를 불러오지 못했거나 데이터가 비어 있습니다.")
    else:
        st.dataframe(val_df, use_container_width=True)
