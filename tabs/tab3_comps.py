import streamlit as st
import pandas as pd

def render_tab3(history_df, LEAGUE_WEIGHTS, format_currency_desc, tab1_data):
    st.subheader("🔍 과거 유사 이적 사례 검색 및 벤치마크 비교 (Comps TOP 5 & 10)")
    st.caption("구글 시트에 누적된 이전 이적 데이터 중 이적료, 총 평점, 평가율(고평가/저평가), 출발 리그가 가장 유사한 과거 사례를 매칭합니다.")

    # tab1에서 넘어온 주요 평가 지표 추출
    target_fee_val = int(tab1_data.get("calc_actual_fee", 5000))
    if target_fee_val <= 0:
        target_fee_val = 5000

    target_score_val = float(tab1_data.get("final_deal_score", 7.50))
    if target_score_val <= 0:
        target_score_val = 7.50

    target_overpay_val = float(tab1_data.get("overpay_pct", 0.0))
    selling_league = tab1_data.get("selling_league", list(LEAGUE_WEIGHTS.keys())[0])

    c_in1, c_in2, c_in3, c_in4, c_in5 = st.columns(5)
    with c_in1:
        target_fee = st.number_input("비교 기준 이적료 (만 €)", min_value=0, value=target_fee_val, step=100, key="comps_fee")
    with c_in2:
        target_score = st.number_input("비교 기준 이적 평점", min_value=1.00, max_value=10.00, value=target_score_val, step=0.1, key="comps_score")
    with c_in3:
        target_overpay = st.number_input("비교 기준 평가율 (%)", min_value=-100.0, max_value=200.0, value=target_overpay_val, step=1.0, key="comps_overpay")
    with c_in4:
        pos_filter = st.selectbox("포지션 필터", ["전체 포지션", "스트라이커 (ST/CF)", "윙어/공미 (WG/CAM)", "미드필더 (CM/CDM)", "수비수 (CB/FB/WB)", "골키퍼 (GK)"], index=0, key="comps_pos_filter")
    with c_in5:
        league_filter = st.selectbox("원소속 리그 필터", ["전체 리그"] + list(LEAGUE_WEIGHTS.keys()), index=0, key="comps_league_filter")

    st.markdown("---")

    if history_df.empty or len(history_df) == 0 or "선수명" not in history_df.columns:
        st.info("💡 **아직 구글 시트에 누적된 과거 이적 데이터가 없습니다.**\n\n1번 및 2번 탭에서 선수 데이터를 저장해 나가시면, 자동으로 이곳에 가장 유사한 과거 이적 사례 TOP 5 상세 카드 및 TOP 10 전체 목록이 나타나게 됩니다.")
    else:
        try:
            valid_rows = []
            for idx, row in history_df.iterrows():
                try:
                    p_name = str(row.get("선수명", f"선수 {idx+1}"))
                    p_fee = float(row.get("실제이적료(만€)", 0))
                    p_fair = float(row.get("산출적정가(만€)", 0))
                    p_pos = str(row.get("포지션", "기타"))
                    p_league = str(row.get("원소속리그", "기타"))
                    p_season = str(row.get("이적시즌", "26/27"))

                    p_score = float(row.get("이적평점", 7.50))
                    p_overpay = ((p_fee - p_fair) / p_fair * 100) if p_fair > 0 else 0.0
                    notes_str = str(row.get("스카우팅메모", ""))

                    if pos_filter != "전체 포지션":
                        f_pos_key = pos_filter.split(" (")[0]
                        if f_pos_key not in p_pos and p_pos not in pos_filter:
                            continue

                    if league_filter != "전체 리그":
                        f_l_key = league_filter.split(" (")[0]
                        if f_l_key not in p_league:
                            continue

                    fee_diff_norm = abs(p_fee - target_fee) / (max(target_fee, 1000) * 1.5)
                    score_diff_norm = abs(p_score - target_score) / 5.0
                    overpay_diff_norm = abs(p_overpay - target_overpay) / 50.0

                    target_l_w = LEAGUE_WEIGHTS.get(selling_league, 1.0)
                    row_l_w = 0.80
                    for l_k, l_v in LEAGUE_WEIGHTS.items():
                        if p_league in l_k:
                            row_l_w = l_v
                            break
                    league_diff_norm = abs(target_l_w - row_l_w) / 0.70

                    total_dist = (fee_diff_norm * 0.30) + (score_diff_norm * 0.25) + (overpay_diff_norm * 0.25) + (league_diff_norm * 0.20)
                    sim_pct = max(0.0, round((1.0 - total_dist) * 100, 1))

                    valid_rows.append({
                        "시즌": p_season,
                        "선수명": p_name,
                        "포지션": p_pos,
                        "원소속리그": p_league,
                        "실제이적료(만€)": p_fee,
                        "산출적정가(만€)": p_fair,
                        "평가율(%)": round(p_overpay, 1),
                        "이적평점": round(p_score, 2),
                        "유사도(%)": sim_pct,
                        "스카우팅메모": notes_str
                    })
                except Exception:
                    continue

            if len(valid_rows) > 0:
                match_df = pd.DataFrame(valid_rows).sort_values(by="유사도(%)", ascending=False).head(10)
                top5_df = match_df.head(5)

                st.markdown(f"### 🎯 **가장 유사한 과거 이적 사례 TOP {len(top5_df)} 상세 리포트**")

                for i in range(0, len(top5_df), 2):
                    cols = st.columns(2)
                    for j in range(2):
                        idx_card = i + j
                        if idx_card < len(top5_df):
                            row_data = top5_df.iloc[idx_card]
                            rank = idx_card + 1
                            with cols[j]:
                                st.markdown(f"#### **{rank}위. {row_data['선수명']}** ({row_data['시즌']})")
                                st.caption(f"📌 포지션: `{row_data['포지션']}` | 리그: `{row_data['원소속리그']}`")
                                st.metric("매칭 유사도", f"{row_data['유사도(%)']}%")
                                st.write(f"- **실제 이적료**: €{row_data['실제이적료(만€)']:,.0f}만 ({format_currency_desc(row_data['실제이적료(만€)']).split(' | ')[0]})")
                                st.write(f"- **이적 총 평점**: ★ {row_data['이적평점']:.2f} / 10.00")
                                st.write(f"- **평가율**: `{row_data['평가율(%)']:+.1f}%` (산출 적정가 €{row_data['산출적정가(만€)']:,.1f}만)")
                                st.markdown("---")

                st.markdown("#### 📋 **유사 이적 사례 전체 비교 테이블 (TOP 10 전체)**")
                st.dataframe(
                    match_df[[
                        "유사도(%)", "시즌", "선수명", "포지션", "원소속리그", 
                        "실제이적료(만€)", "산출적정가(만€)", "평가율(%)", "이적평점", "스카우팅메모"
                    ]], 
                    use_container_width=True
                )
            else:
                st.info("💡 선택하신 포지션 또는 리그 필터 조건에 일치하는 과거 이적 데이터가 없습니다.")
        except Exception as e:
            st.error(f"⚠️ 데이터 비교 중 오류: {e}")
