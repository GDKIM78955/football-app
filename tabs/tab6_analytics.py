import streamlit as st

def render(history_df, webhook_url):
    st.subheader("🏆 구단별 결산, 파워 랭킹 & 데이터 관리실")
    if history_df.empty:
        st.warning("⚠️ 관리할 데이터가 없습니다.")
    else:
        st.dataframe(history_df, use_container_width=True)
        st.info("💡 구단별 순지출(Net Spend) 결산 및 잘못 입력된 데이터를 영구 삭제하는 관리 구역입니다.")
