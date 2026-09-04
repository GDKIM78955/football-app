# 6개의 모듈화된 탭 구성
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "💰 적정 이적료 평가", 
    "📱 FotMob 시즌 성적 & 이적 예측",
    "🔍 과거 유사 이적 사례 비교",
    "🎯 이적 첫 시즌 실제 성적 & 사후 검증",
    "👥 다각도 벤치마크",
    "🏆 종합 결산 & 데이터룸"
])

# 각 탭별 부품 파일 임포트 및 실행
from tabs import tab1_eval, tab2_fotmob, tab3_comps, tab4_validation, tab5_benchmark, tab6_analytics

with tab1:
    tab1_eval.render(history_df, GOOGLE_SHEET_WEBAPP_URL)

with tab2:
    tab2_fotmob.render()

with tab3:
    tab3_comps.render(history_df)

with tab4:
    tab4_validation.render(val_df, GOOGLE_SHEET_WEBAPP_URL)

with tab5:
    tab5_benchmark.render(history_df)

with tab6:
    tab6_analytics.render(history_df, GOOGLE_SHEET_WEBAPP_URL)
