import streamlit as st

def render(history_df, webapp_url):
    st.subheader("💰 프로페셔널 적정 이적료 평가 시스템")
    st.markdown("선수의 기본 프로필과 계약 정보를 입력하여 12대 가중치 기반 적정 이적료를 산출합니다.")

    # 1. 거래 유형 선택 (영입 vs 방출)
    trade_type_choice = st.radio(
        "거래 유형 구분", 
        ["🔵 영입 (IN)", "🔴 방출 / 판매 (OUT)"], 
        index=0, 
        horizontal=True
    )
    is_out_trade = "방출" in trade_type_choice

    st.markdown("---")

    # 2. 기본 프로필 입력 폼
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("##### 👤 선수 기본 정보")
        player_name = st.text_input("선수 이름", placeholder="예: 해리 케인")
        player_nat = st.text_input("국적", placeholder="예: 잉글랜드")
        player_age = st.number_input("만 나이", min_value=15, max_value=45, value=25)
        
        main_position = st.selectbox(
            "주 포지션",
            [
                "스트라이커 / 센터포워드 (ST/CF, +2%)",
                "윙어 / 공격형 미드필더 (WG/CAM, +1%)",
                "중앙 / 수비형 미드필더 (CM/CDM, 기준)",
                "풀백 / 윙백 (RB/LB/WB, -1%)",
                "센터백 (CB, -1%)",
                "골키퍼 (GK, -3%)"
            ],
            index=0
        )

    with col2:
        st.markdown("##### 🏢 소속 및 시장가치 정보")
        
        league_options = [
            "잉글랜드 프리미어리그 (EPL 1부)",
            "스페인 라리가 (La Liga 1부)",
            "독일 분데스리가 (Bundesliga 1부)",
            "이탈리아 세리에 A (Serie A 1부)",
            "프랑스 리그 1 (Ligue 1 1부)",
            "기타 리그"
        ]
        selling_league = st.selectbox("원소속 리그 (보내는 리그)", league_options)
        
        in_from_team = st.text_input("원소속팀명 (보내는 팀)", placeholder="예: 토트넘 홋스퍼")
        in_to_team = st.text_input("이적팀명 (영입 구단)", placeholder="예: 바이에른 뮌헨")
        
        tm_market_value = st.number_input(
            "Transfermarkt 시장가치 (만 유로, €)", 
            min_value=0, 
            value=5000, 
            step=100,
            help="단위: 만 유로 (예: 5000 입력 시 5,000만 유로)"
        )

    st.markdown("---")
    
    if st.button("📊 기본 데이터 확인하기", type="primary"):
        st.success(f"입력 완료! [{player_name} / 만 {player_age}세 / {main_position.split(' ')[0]} / TM 시장가: €{tm_market_value:,}만]")
