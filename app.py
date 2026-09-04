import streamlit as st
import pandas as pd
import numpy as np
import requests
import json
import plotly.graph_objects as go
from datetime import datetime

# 1. 페이지 기본 설정
st.set_page_config(
    page_title="축구 이적시장 12대 가중치 분석 & FotMob 프로젝션 Pro",
    page_icon="⚽",
    layout="wide"
)

GOOGLE_SHEET_WEBAPP_URL = "https://script.google.com/macros/s/AKfycbwUX4diDBw2jD8WufrSa_0PejibYm7tIfyf1ia7O-QTfj1Ae6SQb3bZZ9pmNvDUAT6C/exec"
SPREADSHEET_ID = "16CeAQp1-xqc-mhtvlP0vLlQu5k1pg8DW5A-m29WCFdw"

# 🌟 구글 시트 CSV Export 다이렉트 로드
@st.cache_data(ttl=0)
def fetch_sheet_history():
    try:
        csv_url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv&gid=0"
        df = pd.read_csv(csv_url)
        if not df.empty:
            return df
    except Exception:
        pass
    return pd.DataFrame()

history_df = fetch_sheet_history()

# 2번 탭(검증데이터) 데이터 로드용 함수
@st.cache_data(ttl=0)
def fetch_validation_data():
    try:
        val_url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv&gid=15389686"
        df = pd.read_csv(val_url)
        if not df.empty and "선수명" in df.columns:
            return df
    except Exception:
        pass
    return pd.DataFrame()

if "form_key_id" not in st.session_state:
    st.session_state["form_key_id"] = 0
if "stat_key_id" not in st.session_state:
    st.session_state["stat_key_id"] = 0
if "last_saved_msg" not in st.session_state:
    st.session_state["last_saved_msg"] = None
if "edit_row_index" not in st.session_state:
    st.session_state["edit_row_index"] = None

if "custom_proj_mins" not in st.session_state:
    st.session_state["custom_proj_mins"] = 3000

default_stats = {
    "f_mins": 90, "f_goals": 0, "f_xg": 0.0, "f_assists": 0, "f_xa": 0.0,
    "f_rating": 6.50, "f_matches": 1, "f_starts": 0, "f_shots": 0, "f_sot": 0,
    "f_chances": 0, "f_dribbles": 0, "f_touches_box": 0, "f_tackles": 0,
    "f_gk_saves": 0, "f_gk_conceded": 0, "f_gk_prevented": 0.0,
    "f_gk_cs": 0, "f_gk_errors": 0, "f_gk_claims": 0,
    "f_big_chances": 0, "f_pk_goals": 0, "f_pass_pct": 0.0, "f_duels_pct": 0.0, "f_aerial_pct": 0.0
}
for k, v in default_stats.items():
    if k not in st.session_state:
        st.session_state[k] = v

st.title("⚽ 프로페셔널 축구 이적시장 12대 가중치 분석 & 스카우팅 데이터룸")

# 2. 가중치 딕셔너리
LEAGUE_WEIGHTS = {
    "잉글랜드 프리미어리그 (EPL 1부)": 1.00,
    "스페인 라리가 (La Liga 1부)": 0.92,
    "독일 분데스리가 (Bundesliga 1부)": 0.91,
    "이탈리아 세리에 A (Serie A 1부)": 0.90,
    "프랑스 리그 1 (Ligue 1 1부)": 0.88,
    "잉글랜드 챔피언십 (EFL 2부)": 0.80,
    "포르투갈 프리메이라리가 (1부)": 0.78,
    "네덜란드 에레디비시 (Eredivisie 1부)": 0.77,
    "벨기에 주필러 프로 리그 (1부)": 0.75,
    "브라질 세리에 A (Brasileirão 1부)": 0.68,
    "독일 2. 분데스리가 (2부)": 0.67,
    "스페인 라리가 2 (세군다 2부)": 0.66,
    "튀르키예 쉬페르리그 (1부)": 0.65,
    "이탈리아 세리에 B (2부)": 0.64,
    "미국 메이저리그사커 (MLS 1부)": 0.64,
    "멕시코 리가 MX (1부)": 0.63,
    "스위스 슈퍼리그 (1부)": 0.62,
    "오스트리아 분데스리가 (1부)": 0.62,
    "덴마크 수페르리가 (1부)": 0.61,
    "스코틀랜드 프리미어십 (1부)": 0.60,
    "아르헨티나 프리메라 디비시온 (1부)": 0.60,
    "폴란드 엑스트라클라사 (1부)": 0.55,
    "프랑스 리그 2 (2부)": 0.55,
    "그리스 슈퍼리그 (1부)": 0.54,
    "사우디 프로리그 (SPL 1부)": 0.52,
    "일본 J1리그 (1부)": 0.50,
    "대한민국 K리그1 (1부)": 0.48,
    "스웨덴 알스벤스칸 (1부)": 0.48,
    "노르웨이 엘리테세리엔 (1부)": 0.47,
    "일본 J2리그 (2부)": 0.35,
    "대한민국 K리그2 (2부)": 0.33,
    "기타 리그": 0.30
}

TRACKED_LEAGUE_NAMES = [
    "프리미어리그", "라리가", "분데스리가", "세리에 A", "리그 1",
    "에레디비시", "포르투갈", "벨기에", "튀르키예", "챔피언십"
]

CLUB_TIERS = {
    "Tier 1: 엘리트 메가클럽 (레알, 맨시티, 바이에른, PSG 등)": 1.05,
    "Tier 2: 빅클럽 (아스날, 리버풀, 첼시, 바르샤, 유벤투스 등)": 1.02,
    "Tier 3: 중상위권 클럽 (토트넘, AT마드리드, 도르트문트 등)": 1.00,
    "Tier 4: 중하위권 클럽 (EPL 중하위, 타 빅리그 중위권)": 0.98,
    "Tier 5: 소형/셀링 클럽 (중소리그, 2부리그, K/J리그)": 0.95
}

CONTRACT_WEIGHTS = {
    "6개월 이하 (FA 임박/겨울 이적, -20%)": 0.80,
    "1년 남음 (재계약 분기점, -8%)": 0.92,
    "2년 남음 (표준 계약 기준선, 1.00)": 1.00,
    "3년 남음 (구단 협상 우위, +2%)": 1.02,
    "4년 이상 (장기 계약/바이아웃, +4%)": 1.04
}

POSITION_WEIGHTS = {
    "스트라이커 / 센터포워드 (ST/CF, +2%)": 1.02,
    "윙어 / 공격형 미드필더 (WG/CAM, +1%)": 1.01,
    "중앙 / 수비형 미드필더 (CM/CDM, 기준)": 1.00,
    "풀백 / 윙백 (RB/LB/WB, -1%)": 0.99,
    "센터백 (CB, -1%)": 0.99,
    "골키퍼 (GK, -3%)": 0.97
}

VERSATILITY_WEIGHTS = {
    "단일 포지션 전담 (1개 포지션, 기준)": 1.00,
    "듀얼 롤 (2개 포지션 소화, +1%)": 1.01,
    "만능 유틸리티 (3개 이상 소화, +2%)": 1.02
}

REGISTRATION_WEIGHTS = {
    "일반 (EU 국적자 / 쿼터 이슈 없음, 기준)": 1.00,
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿 EPL 홈그로운 (Home-Grown 충족, +4%)": 1.04,
    "🏛️ 구단 자체 유스 출신 (Club-Trained, +2%)": 1.02,
    "🇪🇸🇮🇹 비EU 쿼터 소모 (Non-EU Quota, -2%)": 0.98
}

TRANSFER_TYPE_WEIGHTS = {
    "일반 완전 이적 (Permanent, 기준)": 1.00,
    "단순 1년 임대 (Simple Loan, 1년사용가치 20% 자동환산)": 0.20,
    "임대 후 의무 영입 (Loan w/ Obligation, +2%)": 1.02,
    "임대 후 선택 영입 (Loan w/ Option, 1년사용가치 기준)": 0.20,
    "바이백 조항 포함 이적 (Buy-back Clause, -5%)": 0.95,
    "셀온 지분 포함 이적 (Sell-on Clause, -3%)": 0.97,
    "비공개 이적 (Undisclosed, 시장적정가 1:1 수렴 추정)": 1.00,
    "FA 자유계약 영입 (Free Transfer, 계약금 기준)": 1.00
}

BIG_STAGE_WEIGHTS = {
    "🌟 UCL 본선 16강+ / 주요 A매치 핵심 주전 (+3%)": 1.03,
    "🔥 UEL/UECL 본선 또는 국대 A매치 주전 (+1%)": 1.01,
    "⚖️ 유럽대항전 / 메이저 국대 경험 없음 (기준)": 1.00
}

INJURY_WEIGHTS = {
    "🛡️ 철강왕 (최근 2년 결장 거의 없음, +1%)": 1.01,
    "⚖️ 일반적인 수준 (경미한 1~2주 결장, 기준)": 1.00,
    "⚠️ 잦은 근육/잔부상 (시즌당 4~6주 결장, -3%)": 0.97,
    "🚨 최근 2년 내 장기 부상 이력 (십자인대/골절, -6%)": 0.94
}

URGENCY_WEIGHTS = {
    "⚖️ 일반 보강 / 뎁스 자원 (기준)": 1.00,
    "🔥 최우선 보강 타겟 (선발진 명확한 취약, +4%)": 1.04,
    "🚨 비상사태 / 대체불가 타겟 (핵심이탈·패닉바이, +8%)": 1.08
}

def get_positional_age_weight(age, position_name):
    if "ST/CF" in position_name or "WG/CAM" in position_name:
        if age <= 19: return 1.05
        elif age <= 23: return 1.03
        elif age <= 27: return 1.00
        elif age <= 29: return 0.97
        elif age <= 31: return 0.90
        elif age <= 34: return 0.80
        else: return 0.65
    elif "GK" in position_name or "CB" in position_name:
        if age <= 19: return 1.01
        elif age <= 23: return 1.01
        elif age <= 27: return 1.00
        elif age <= 29: return 1.00
        elif age <= 31: return 0.96
        elif age <= 34: return 0.90
        else: return 0.78
    else:
        if age <= 19: return 1.03
        elif age <= 23: return 1.02
        elif age <= 27: return 1.00
        elif age <= 29: return 0.98
        elif age <= 31: return 0.92
        elif age <= 34: return 0.84
        else: return 0.70

rate_krw = 1500
rate_gbp = 0.86

def format_currency_desc(eur_man_euro):
    if eur_man_euro <= 0: return "₩0억 | £0만"
    total_eur = eur_man_euro * 10000
    krw_eok = (total_eur * rate_krw) / 100000000.0
    gbp_man = eur_man_euro * rate_gbp
    return f"약 {krw_eok:,.1f}억원 | £{gbp_man:,.1f}만"

def get_exact_val(row, col_name, default_val=""):
    try:
        if col_name in row and pd.notnull(row[col_name]) and str(row[col_name]).strip() not in ["", "nan", "None"]:
            return type(default_val)(row[col_name])
    except:
        pass
    return default_val

# 3. 메인 6개 탭 구성
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "💰 적정 이적료 평가", 
    "📱 FotMob 시즌 성적 & 이적 예측 (13대 풀 스탯)",
    "🔍 과거 유사 이적 사례 비교 (Comps TOP 5 & 10)",
    "🎯 이적 첫 시즌 실제 성적 입력 & 모델 검증",
    "👥 신규 이적생 vs 과거 유사 선수 다각도 벤치마크",
    "🏆 이적시장 구단/리그별 종합 결산 & 데이터룸"
])

# ================= TAB 1: 적정 이적료 평가 =================
with tab1:
    if st.session_state["last_saved_msg"]:
        st.success(st.session_state["last_saved_msg"])
        st.session_state["last_saved_msg"] = None

    c_mode1, c_mode2 = st.columns([1, 1])
    with c_mode1:
        edit_toggle = st.toggle("✏️ 기존 저장된 선수 불러와서 수정/주급 추가 모드", value=False)

    if edit_toggle:
        st.markdown("##### 🔍 불러올 선수 선택")
        has_season_col = "이적시즌" in history_df.columns
        has_name_col = "선수명" in history_df.columns

        if history_df.empty or not has_season_col or not has_name_col:
            st.warning("⚠️ 시트에 저장된 기존 데이터가 없거나 컬럼명(`이적시즌`, `선수명`)을 찾을 수 없습니다.")
        else:
            c_ld1, c_ld2, c_ld3 = st.columns([1, 2, 1])
            with c_ld1:
                e_seasons = list(history_df["이적시즌"].dropna().unique())
                sel_e_season = st.selectbox("시즌 선택", e_seasons, key="edit_season_box")
            
            e_season_df = history_df[history_df["이적시즌"] == sel_e_season]
            e_players = list(e_season_df["선수명"].dropna().unique())
            
            with c_ld2:
                sel_e_player = st.selectbox("선수 선택", e_players, key="edit_player_box") if e_players else None

            with c_ld3:
                st.write("")
                st.write("")
                if st.button("📥 데이터 불러오기", type="primary", use_container_width=True):
                    if sel_e_player:
                        matched_rows = e_season_df[e_season_df["선수명"] == sel_e_player]
                        row_raw = matched_rows.iloc[-1]
                        
                        match_idx_list = e_season_df.index[e_season_df["선수명"] == sel_e_player].tolist()
                        if match_idx_list:
                            st.session_state["edit_row_index"] = match_idx_list[-1] + 2

                        # 🌟 [완벽 해결] 불러온 즉시 st.session_state 위젯 키에 값을 직접 박아넣어 리셋 방지
                        k_id = st.session_state["form_key_id"] + 1
                        st.session_state["form_key_id"] = k_id
                        st.session_state["stat_key_id"] += 1

                        st.session_state[f"name_{k_id}"] = str(get_exact_val(row_raw, "선수명", ""))
                        st.session_state[f"nat_{k_id}"] = str(get_exact_val(row_raw, "국적", ""))
                        st.session_state[f"age_{k_id}"] = int(get_exact_val(row_raw, "만나이", 28))
                        st.session_state[f"from_team_{k_id}"] = str(get_exact_val(row_raw, "원소속팀명", ""))
                        st.session_state[f"to_team_{k_id}"] = str(get_exact_val(row_raw, "이적팀명", ""))
                        st.session_state[f"tm_{k_id}"] = int(get_exact_val(row_raw, "TM시장가치(만€)", 4500))
                        st.session_state[f"fee_{k_id}"] = int(get_exact_val(row_raw, "실제이적료(만€)", 0))
                        st.session_state[f"wage_{k_id}"] = float(get_exact_val(row_raw, "주급(만€)", 0.0))
                        
                        p_notes = str(get_exact_val(row_raw, "스카우팅메모", ""))
                        st.session_state[f"note_{k_id}"] = p_notes.split(" | [영입")[0].split(" | [방출")[0].strip()

                        # 셀렉트박스 매칭 저장
                        p_pos_str = str(get_exact_val(row_raw, "포지션", ""))
                        for p_k in POSITION_WEIGHTS.keys():
                            if p_pos_str and p_pos_str in p_k:
                                st.session_state[f"pos_{k_id}"] = p_k
                                break

                        p_from_league = str(get_exact_val(row_raw, "원소속리그", ""))
                        for l_k in LEAGUE_WEIGHTS.keys():
                            if p_from_league and p_from_league in l_k:
                                st.session_state[f"league_{k_id}"] = l_k
                                break

                        p_to_league_name = str(get_exact_val(row_raw, "이적팀리그", ""))
                        for l_k in LEAGUE_WEIGHTS.keys():
                            if p_to_league_name and p_to_league_name in l_k:
                                st.session_state[f"to_league_choice_{k_id}"] = l_k
                                break

                        p_tier = str(get_exact_val(row_raw, "영입구단티어", ""))
                        for t_k in CLUB_TIERS.keys():
                            if p_tier and p_tier in t_k:
                                st.session_state[f"tier_{k_id}"] = t_k
                                break

                        p_ttype = str(get_exact_val(row_raw, "이적형태", ""))
                        for tt_k in TRANSFER_TYPE_WEIGHTS.keys():
                            if p_ttype and p_ttype in tt_k:
                                st.session_state[f"ttype_{k_id}"] = tt_k
                                break

                        # 2번 탭 스탯 동기화
                        st.session_state["f_matches"] = int(get_exact_val(row_raw, "이전_출전경기", 1))
                        st.session_state["f_starts"] = int(get_exact_val(row_raw, "이전_선발", 0))
                        st.session_state["f_mins"] = int(get_exact_val(row_raw, "이전_출전시간", 90))
                        st.session_state["f_goals"] = int(get_exact_val(row_raw, "이전_골", 0))
                        st.session_state["f_xg"] = float(get_exact_val(row_raw, "이전_xG", 0.0))
                        st.session_state["f_assists"] = int(get_exact_val(row_raw, "이전_도움", 0))
                        st.session_state["f_xa"] = float(get_exact_val(row_raw, "이전_xA", 0.0))
                        st.session_state["f_shots"] = int(get_exact_val(row_raw, "이전_총슈팅", 0))
                        st.session_state["f_sot"] = int(get_exact_val(row_raw, "이전_유효슈팅", 0))
                        st.session_state["f_chances"] = int(get_exact_val(row_raw, "이전_찬스메이킹", 0))
                        st.session_state["f_dribbles"] = int(get_exact_val(row_raw, "이전_성공드리블", 0))
                        st.session_state["f_touches_box"] = int(get_exact_val(row_raw, "이전_박스터치", 0))
                        st.session_state["f_tackles"] = int(get_exact_val(row_raw, "이전_태클성공", 0))
                        st.session_state["f_rating"] = float(get_exact_val(row_raw, "이전_FotMob평점", 6.5))

                        st.session_state["f_big_chances"] = int(get_exact_val(row_raw, "빅찬스메이킹", 0))
                        st.session_state["f_pk_goals"] = int(get_exact_val(row_raw, "pk득점", 0))
                        st.session_state["f_pass_pct"] = float(get_exact_val(row_raw, "패스성공률%", 0.0))
                        st.session_state["f_duels_pct"] = float(get_exact_val(row_raw, "지상경합승률%", 0.0))
                        st.session_state["f_aerial_pct"] = float(get_exact_val(row_raw, "공중볼승률%", 0.0))

                        st.session_state["f_gk_saves"] = int(get_exact_val(row_raw, "gk_선방", 0))
                        st.session_state["f_gk_conceded"] = int(get_exact_val(row_raw, "gk_실점", 0))
                        st.session_state["f_gk_prevented"] = float(get_exact_val(row_raw, "gk_득점차단", 0.0))
                        st.session_state["f_gk_cs"] = int(get_exact_val(row_raw, "gk_클린시트", 0))
                        st.session_state["f_gk_errors"] = int(get_exact_val(row_raw, "gk_실수", 0))
                        st.session_state["f_gk_claims"] = int(get_exact_val(row_raw, "gk_공중볼", 0))

                        st.session_state["custom_proj_mins"] = int(get_exact_val(row_raw, "예측_출전시간", 3000))

                        st.rerun()
    else:
        st.session_state["edit_row_index"] = None

    k_id = st.session_state["form_key_id"]
    s_id = st.session_state["stat_key_id"]

    st.markdown("---")
    trade_type_choice = st.radio("거래 유형 구분", ["🔵 영입 (IN)", "🔴 방출 / 판매 (OUT)"], index=0, horizontal=True, key=f"trade_type_{k_id}")
    is_out_trade = "방출" in trade_type_choice
    
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader(f"📝 {'[수정 모드] ' if edit_toggle else ''}{'방출(OUT)' if is_out_trade else '영입(IN)'} 선수 & 계약 정보")
        c_s1, c_s2 = st.columns(2)
        with c_s1: 
            season_val = st.selectbox("이적 시즌 / 시장", ["26/27 여름 (Summer)", "26/27 겨울 (Winter)", "기타"], index=0, key=f"season_{k_id}")
        with c_s2: 
            transfer_type = st.selectbox("이적 형태 & 계약 조항", list(TRANSFER_TYPE_WEIGHTS.keys()), index=0, key=f"ttype_{k_id}")
            
        option_exercised = st.checkbox("📌 임대 후 옵션 발동 (완전 전환 완료된 건)", value=False, key=f"opt_exec_{k_id}", help="체크하시면 모델 계산 시 '일반 완전 이적(Permanent)' 기준으로 공정하게 평가됩니다.")
        if option_exercised:
            transfer_type = "일반 완전 이적 (Permanent, 기준)"
            st.info("💡 **안내**: 임대 후 옵션이 발동되어 완전 이적으로 처리되므로, 평점 평가 시 일반 완전 이적 기준(1.00)으로 자동 적용됩니다.")

        c_n1, c_n2, c_n3 = st.columns([2, 1, 1])
        with c_n1: player_name = st.text_input("선수 이름", placeholder="예: Ezri Konsa", key=f"name_{k_id}")
        with c_n2: player_nat = st.text_input("국적", placeholder="예: 잉글랜드", key=f"nat_{k_id}")
        with c_n3: player_age = st.number_input("만 나이", min_value=15, max_value=45, value=28, key=f"age_{k_id}")

        if not edit_toggle and player_name.strip() and not history_df.empty and "선수명" in history_df.columns and "이적시즌" in history_df.columns:
            dup_matches = history_df[
                (history_df["선수명"].astype(str).str.strip().str.lower() == player_name.strip().lower()) & 
                (history_df["이적시즌"].astype(str).str.strip() == season_val.strip())
            ]
            if not dup_matches.empty:
                last_dup = dup_matches.iloc[-1]
                dup_from = str(last_dup.get("원소속팀명", "미상"))
                dup_to = str(last_dup.get("이적팀명", "미상"))
                dup_fee = float(last_dup.get("실제이적료(만€)", 0))
                st.warning(f"⚠️ **중복 등록 알림**: **'{player_name.strip()}'** 선수는 이미 이번 `{season_val}` 시즌에 등록된 내역이 있습니다! (`[{dup_from} ➔ {dup_to}] | €{dup_fee:,.0f}만`)")

        c_t1, c_t2, c_t3 = st.columns(3)
        with c_t1: in_from_team = st.text_input("원소속팀명 (보내는 팀)", placeholder="예: 아스톤 빌라", key=f"from_team_{k_id}")
        with c_t2: in_to_team = st.text_input("이적팀명 (영입 구단)", placeholder="예: 아스날", key=f"to_team_{k_id}")
        with c_t3: in_to_league_choice = st.selectbox("이적팀 리그", list(LEAGUE_WEIGHTS.keys()), index=0, key=f"to_league_choice_{k_id}")
        
        is_tracked_target = any(k in in_to_league_choice for k in TRACKED_LEAGUE_NAMES)
        if is_tracked_target:
            st.caption("✅ **10대 핵심 리그 이적**: 시즌 종료 후 4번 탭 사후 검증 대상에 **자동 등록**됩니다.")
        else:
            st.caption("ℹ️ **기타 리그 이적**: 메인 결산 장부에만 기록되며, 검증 시트에는 등록되지 않습니다.")

        pos_col1, pos_col2 = st.columns(2)
        with pos_col1: main_position = st.selectbox("주 포지션", list(POSITION_WEIGHTS.keys()), index=4, key=f"pos_{k_id}")
        with pos_col2: versatility = st.selectbox("멀티 포지션 소화 능력", list(VERSATILITY_WEIGHTS.keys()), index=0, key=f"vers_{k_id}")
            
        c_r1, c_r2 = st.columns(2)
        with c_r1: reg_status = st.selectbox("스쿼드 등록 / HG 쿼터", list(REGISTRATION_WEIGHTS.keys()), index=1, key=f"reg_{k_id}")
        with c_r2: big_stage = st.selectbox("UCL / 빅매치 검증도", list(BIG_STAGE_WEIGHTS.keys()), index=0, key=f"stage_{k_id}")
        
        c_i1, c_i2 = st.columns(2)
        with c_i1: injury_status = st.selectbox("부상 내구성 & 메디컬 리스크", list(INJURY_WEIGHTS.keys()), index=1, key=f"inj_{k_id}")
        with c_i2: urgency_status = st.selectbox("영입 구단 절박성 & 취약 포지션", list(URGENCY_WEIGHTS.keys()), index=0, key=f"urg_{k_id}")

        selling_league = st.selectbox("보내는 리그 (원소속 리그)", list(LEAGUE_WEIGHTS.keys()), index=0, key=f"league_{k_id}")
        buying_club_tier = st.selectbox("영입구단티어", list(CLUB_TIERS.keys()), index=1, key=f"tier_{k_id}")
        remaining_contract = st.selectbox("이적 당시 잔여 계약 기간", list(CONTRACT_WEIGHTS.keys()), index=2, key=f"contract_{k_id}")
        
        st.markdown("---")
        
        f_p90 = (st.session_state["f_mins"] / 90.0) if st.session_state["f_mins"] > 0 else 1.0
        cur_p90_exp = (st.session_state["f_xg"] + st.session_state["f_xa"]) / f_p90
        cur_rating = st.session_state["f_rating"]
        
        if cur_rating >= 7.45 or cur_p90_exp >= 0.75:
            opta_w = 1.02
            opta_desc = "🌟 최상위권 엘리트 활약 (+2%)"
        elif cur_rating >= 7.15 or cur_p90_exp >= 0.50:
            opta_w = 1.01
            opta_desc = "🔥 주전급 준수한 활약 (+1%)"
        elif cur_rating >= 6.80 or cur_p90_exp >= 0.25:
            opta_w = 1.00
            opta_desc = "⚖️ 리그 평균 수준 (기준 1.00)"
        else:
            opta_w = 0.98
            opta_desc = "⚠️ 기대 이하 / 부진 (-2%)"

        with st.expander("🔗 [FotMob 탭 연동] 지난 시즌 실적 및 평점 가중치", expanded=True):
            if "GK" in main_position:
                st.markdown(f"""
                - **골키퍼 실적**: 선방 `{st.session_state.get('f_gk_saves', 0)}회` / 실점 `{st.session_state.get('f_gk_conceded', 0)}` / 클린시트 `{st.session_state.get('f_gk_cs', 0)}경기`
                - **득점 차단 (선방력)**: `{st.session_state.get('f_gk_prevented', 0.0):+.2f}` (출전 {st.session_state['f_mins']:,}분)
                - **FotMob 평균 평점**: `★ {cur_rating:.2f}` ➔ **{opta_desc} (가중치 {opta_w:.2f})**
                """)
            else:
                st.markdown(f"""
                - **지난 시즌 실적**: `{st.session_state['f_goals']}골 {st.session_state['f_assists']}도움` (출전 {st.session_state['f_mins']:,}분)
                - **기대 생산력**: `xG {st.session_state['f_xg']:.2f}` / `xA {st.session_state['f_xa']:.2f}` (90분당 **{cur_p90_exp:.2f}**)
                - **FotMob 평균 평점**: `★ {cur_rating:.2f}` ➔ **{opta_desc} (가중치 {opta_w:.2f})**
                """)

        st.markdown("---")
        tm_market_value = st.number_input("TM시장가치(만€)", min_value=0, value=4500, step=50, key=f"tm_{k_id}")
        if tm_market_value > 0: st.caption(f"💡 시장가치 환산: **{format_currency_desc(tm_market_value)}**")
        
        is_loan_type = "임대" in transfer_type and "의무" not in transfer_type and not option_exercised
        is_undisclosed = "비공개" in transfer_type
        is_fa = "FA" in transfer_type
        
        fee_label = "실제 수령/지출 임대료 (Loan Fee, 만 유로, €)" if is_loan_type else ("실제 방출(판매) 이적료 (만 유로, €)" if is_out_trade else "실제이적료(만€)")
        
        actual_transfer_fee = st.number_input(
            fee_label, 
            min_value=0, 
            value=0 if is_undisclosed else 0, 
            step=50, 
            key=f"fee_{k_id}",
            disabled=is_undisclosed
        )
        
        if is_undisclosed:
            st.info("💡 **비공개 이적 선택됨**: 실제 이적료가 공개되지 않아 시장 적정가와 동일하게 추정하여 분석합니다.")
        elif actual_transfer_fee > 0:
            st.caption(f"💡 실제금액 환산: **{format_currency_desc(actual_transfer_fee)}**")

        with st.expander("💼 [선택/수정 입력] 주급(Weekly Wage) & 연간 총비용 분석", expanded=True):
            weekly_wage_in = st.number_input("주급(만€)", min_value=0.0, value=0.0, step=0.5, key=f"wage_{k_id}")
            annual_wage_eur = weekly_wage_in * 52
            annual_transfer_amort = (actual_transfer_fee / 4.0) if actual_transfer_fee > 0 else 0.0
            total_annual_cost = annual_transfer_amort + annual_wage_eur
            if weekly_wage_in > 0:
                st.caption(f"📌 **주급 환산**: 주당 약 {weekly_wage_in*10000*rate_krw/100000000:.1f}억원 (£{weekly_wage_in*rate_gbp:.1f}만)")
                st.markdown(f"- **연간 총비용 (이적료 4년 분할상각 + 1년 연봉)**: `€{total_annual_cost:,.1f}만` (약 {total_annual_cost*10000*rate_krw/100000000:.0f}억원/년)")
            else:
                if is_fa:
                    st.warning("⚠️ **FA 영입 주의**: FA는 이적료가 없으므로 주급(연봉)을 입력해야 실제 계약 가성비(오버페이/적정 평점)가 정확하게 평가됩니다.")
                elif is_loan_type:
                    st.info("💡 **임대 영입 안내**: 주급 보조액이 있다면 주급을 입력해 주세요. (연간 총 사용가치와 직접 대조됩니다)")
                else:
                    st.caption("ℹ️ 주급이 입력되지 않았습니다. (주급 미입력 시 순수 이적료 기준으로 분석)")

        player_notes = st.text_area("스카우팅메모", placeholder="예: 대인 방어 및 후방 빌드업 우수", key=f"note_{k_id}")

    league_w = LEAGUE_WEIGHTS[selling_league]
    age_w = get_positional_age_weight(player_age, main_position)
    club_w = CLUB_TIERS[buying_club_tier]
    contract_w = CONTRACT_WEIGHTS[remaining_contract]
    pos_w = POSITION_WEIGHTS[main_position]
    vers_w = VERSATILITY_WEIGHTS[versatility]
    reg_w = REGISTRATION_WEIGHTS[reg_status]
    ttype_w = TRANSFER_TYPE_WEIGHTS[transfer_type]
    stage_w = BIG_STAGE_WEIGHTS[big_stage]
    inj_w = INJURY_WEIGHTS[injury_status]
    urg_w = URGENCY_WEIGHTS[urgency_status]

    is_winter = "겨울" in season_val
    season_factor = 1.10 if is_winter else 1.00

    base_calc_val = tm_market_value * league_w * age_w * club_w * contract_w * pos_w * vers_w * reg_w * opta_w * ttype_w * stage_w * inj_w * urg_w
    fair_value = base_calc_val * season_factor
    
    calc_actual_fee = fair_value if is_undisclosed else actual_transfer_fee
    
    expected_fair_weekly_wage = (fair_value * 0.0025) if fair_value > 0 else 5.0
    
    if is_fa:
        if weekly_wage_in > 0:
            wage_overpay_pct = ((weekly_wage_in - expected_fair_weekly_wage) / expected_fair_weekly_wage) * 100
            overpay_pct = wage_overpay_pct
            diff = (weekly_wage_in - expected_fair_weekly_wage) * 52
        else:
            overpay_pct = 0.0
            diff = 0.0
    elif is_loan_type:
        expected_1yr_use_val = (fair_value / 0.20) * 0.20 if "임대" in transfer_type else fair_value
        actual_1yr_cost = calc_actual_fee + (weekly_wage_in * 52)
        if expected_1yr_use_val > 0:
            overpay_pct = ((actual_1yr_cost - expected_1yr_use_val) / expected_1yr_use_val) * 100
            diff = actual_1yr_cost - expected_1yr_use_val
        else:
            overpay_pct = 0.0
            diff = 0.0
    else:
        diff = calc_actual_fee - fair_value
        overpay_pct = (diff / fair_value) * 100 if fair_value > 0 else 0.0

    if is_undisclosed:
        status_label = "⚖️ 비공개 (적정가 추정)"
    elif is_fa and weekly_wage_in > 0:
        if abs(overpay_pct) <= 10.0:
            status_label = "⚖️ 적정 주급 FA 영입 (Fair Package)"
        elif overpay_pct > 0:
            status_label = f"⚠️ 주급 오버페이 FA (+{overpay_pct:.1f}%)"
        else:
            status_label = f"💎 주급 혜자 FA 계약 ({overpay_pct:.1f}%)"
    elif fair_value == 0 and calc_actual_fee == 0: 
        status_label = "입력 대기 중"
    elif abs(diff) <= (fair_value * 0.05): 
        status_label = "⚖️ 적정가 (Fair Deal)"
    elif diff > 0: 
        status_label = f"⚠️ {'고가 매각 성공' if is_out_trade else '고평가/오버페이'} (+{overpay_pct:.1f}%)"
    else: 
        status_label = f"💎 {'헐값 매각 손해' if is_out_trade else '저평가/혜자'} ({overpay_pct:.1f}%)"

    if is_winter:
        market_min = base_calc_val * 1.15
        market_max = base_calc_val * 1.20
        market_mid = (market_min + market_max) / 2.0
        range_desc = "+15% ~ +20% 겨울 특수 프리미엄"
    else:
        market_min = base_calc_val * 1.05
        market_max = base_calc_val * 1.10
        market_mid = (market_min + market_max) / 2.0
        range_desc = "+5% ~ +10% 시장 프리미엄"
    
    ext_diff = calc_actual_fee - market_mid
    ext_overpay_pct = (ext_diff / market_mid) * 100 if market_mid > 0 else 0.0

    if is_undisclosed:
        ext_status_label = "⚖️ 비공개 (시장가 적정 추정)"
    elif fair_value == 0 and calc_actual_fee == 0:
        ext_status_label = "분석 대기 중"
    elif market_min <= calc_actual_fee <= market_max:
        ext_status_label = "⚖️ 시장가 적합 (Market Fair Deal)"
    elif calc_actual_fee > market_max:
        over_max_pct = ((calc_actual_fee - market_max) / market_max) * 100
        ext_status_label = f"⚠️ 시장 상한 초과 (+{over_max_pct:.1f}%)"
    else:
        under_min_pct = ((market_min - calc_actual_fee) / market_min) * 100
        ext_status_label = f"💎 시장가 대비 혜자 (-{under_min_pct:.1f}%)"

    if tm_market_value > 0 and (calc_actual_fee > 0 or is_loan_type or is_fa or is_undisclosed):
        if is_fa:
            base_deal_score = 8.00
            if weekly_wage_in > 0:
                wage_score_delta = max(-3.0, min(1.5, -(overpay_pct / 30.0)))
            else:
                wage_score_delta = 0.5
            val_score_delta = wage_score_delta
        elif is_loan_type:
            base_deal_score = 7.50
            val_score_delta = max(-3.0, min(2.0, -(overpay_pct / 25.0)))
        else:
            base_deal_score = 7.50
            score_multiplier = 1.0 if is_out_trade else -1.0
            val_score_delta = 0.0 if is_undisclosed else max(-3.5, min(2.5, score_multiplier * (overpay_pct / 20.0)))
            
            if weekly_wage_in > 0 and expected_fair_weekly_wage > 0:
                if weekly_wage_in > expected_fair_weekly_wage * 1.5:
                    val_score_delta -= min(0.6, (weekly_wage_in - expected_fair_weekly_wage * 1.5) / 10.0)

        rating_delta = max(-0.8, min(1.0, (cur_rating - 7.00) * 1.5))
        age_delta = max(-1.0, min(0.8, (age_w - 1.00) * 8.0))
        risk_delta = (stage_w - 1.00) * 5.0 + (inj_w - 1.00) * 5.0 + (reg_w - 1.00) * 3.0 + (urg_w - 1.00) * 2.0
        
        final_deal_score = round(max(1.00, min(10.00, base_deal_score + val_score_delta + rating_delta + age_delta + risk_delta)), 2)
        
        ext_val_score_delta = val_score_delta if (is_fa or is_loan_type) else (0.0 if is_undisclosed else max(-3.5, min(2.5, score_multiplier * (ext_overpay_pct / 20.0))))
        ext_deal_score = round(max(1.00, min(10.00, base_deal_score + ext_val_score_delta + rating_delta + age_delta + risk_delta)), 2)

        def get_grade_info(score):
            if score >= 9.00: return "💎 S등급 (Masterclass Deal)", "success"
            elif score >= 8.00: return "🌟 A등급 (Excellent Deal)", "success"
            elif score >= 7.00: return "⚖️ B등급 (Solid / Fair Deal)", "info"
            elif score >= 6.00: return "⚠️ C등급 (Risky Deal)", "warning"
            else: return "🚨 D등급 (Panic / Bad Deal)", "error"

        deal_grade, deal_badge_type = get_grade_info(final_deal_score)
        ext_deal_grade, ext_badge_type = get_grade_info(ext_deal_score)
    else:
        final_deal_score = 0.00
        ext_deal_score = 0.00
        deal_grade = "분석 대기 중"
        ext_deal_grade = "분석 대기 중"

    with col2:
        st.subheader("📊 분석 결과 및 12대 세부 지표")
        display_name = player_name if player_name else "선수명 미입력"
        display_nat = f"({player_nat})" if player_nat else ""
        pos_short = main_position.split(" (")[0]
        ttype_short = transfer_type.split(" (")[0]
        reg_short = reg_status.split(" (")[0]
        urg_short = urgency_status.split(" (")[0]
        
        season_icon = "❄️" if is_winter else "☀️"
        transfer_route = f"[{in_from_team} ➔ {in_to_team}]" if in_from_team.strip() and in_to_team.strip() else ""
        tag_badge = "🔴 [방출/판매]" if is_out_trade else "🔵 [영입/보강]"
        mode_tag = "✏️ [기존데이터 수정]" if edit_toggle else ""
        st.markdown(f"### {tag_badge} {mode_tag} **{display_name}** {display_nat} {transfer_route} - `{pos_short}` {season_icon}")
        st.caption(f"📌 시장: **{season_val.split(' (')[0]}** | 형태: **{ttype_short}** | 쿼터: **{reg_short}** | 필요도: **{urg_short}**")
        
        res_c1, res_c2, res_c3, res_c4 = st.columns(4)
        with res_c1:
            st.metric("산출 적정가", f"€{fair_value:,.1f}만")
            if fair_value > 0: st.caption(f"{format_currency_desc(fair_value).split(' | ')[0]}")
        with res_c2:
            fee_display = "비공개 (추정)" if is_undisclosed else (f"€{calc_actual_fee:,.1f}만" if not is_fa else "FA (이적료 €0)")
            st.metric("실제 거래액", fee_display, delta=f"{diff:+,.1f}만 (€)" if not is_undisclosed and not is_fa and calc_actual_fee > 0 else None, delta_color="inverse" if not is_out_trade else "normal")
            if not is_undisclosed and calc_actual_fee > 0: st.caption(f"{format_currency_desc(calc_actual_fee).split(' | ')[0]}")
        with res_c3:
            st.metric("평가율 / 진단", f"{overpay_pct:+.1f}%" if (fair_value > 0 or is_fa) and not is_undisclosed else "0.0%", delta=status_label.split(" ")[0])
            st.caption(status_label)
        with res_c4:
            st.metric("이적 거래 평점", f"★ {final_deal_score:.2f}", delta=deal_grade.split(" ")[0])
            st.caption(deal_grade.split(" (")[0])

        st.markdown("---")
        
        with st.expander("📊 [이미지 캡처용] 선수 12대 스카우팅 육각형 레이더 차트", expanded=True):
            radar_categories = ['리그 템포', '나이/포텐', '구단 스케일', '계약 상태', '포지션 희소성', 'UCL/빅매치', '부상 내구성', '영입 절박성']
            radar_values = [league_w * 100, age_w * 100, club_w * 100, contract_w * 100, pos_w * 100, stage_w * 100, inj_w * 100, urg_w * 100]
            
            fig = go.Figure()
            fig.add_trace(go.Scatterpolar(
                r=radar_values + [radar_values[0]],
                theta=radar_categories + [radar_categories[0]],
                fill='toself',
                fillcolor='rgba(31, 119, 180, 0.3)' if not is_out_trade else 'rgba(214, 39, 40, 0.3)',
                line=dict(color='#1f77b4' if not is_out_trade else '#d62728', width=2),
                name=display_name
            ))
            fig.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[50, 115])),
                showlegend=False,
                margin=dict(l=40, r=40, t=30, b=30),
                height=320
            )
            st.plotly_chart(fig, use_container_width=True)

        st.divider()
        
        st.markdown(f"#### 📢 **[외부 발표용] 시장가 범위 & 진단 평점 ({season_icon} {season_val.split(' ')[1] if ' ' in season_val else ''})**")

        if fair_value > 0:
            st.info(f"""
            📌 **현실 시장 거래 예상 범위 ({range_desc})**:  
            **€{market_min:,.1f}만 ~ €{market_max:,.1f}만** *(약 {((market_min*10000*rate_krw)/100000000.0):,.0f}억 ~ {((market_max*10000*rate_krw)/100000000.0):,.0f}억원)*
            """)

            ext_c1, ext_c2 = st.columns(2)
            with ext_c1:
                st.markdown(f"""
                - **외부 발표용 평점**: `★ {ext_deal_score:.2f} / 10.00`
                - **종합 판정 등급**: **{ext_deal_grade.split(' (')[0]}**
                """)
            with ext_c2:
                fee_ext_str = "비공개 (추정)" if is_undisclosed else (f"€{calc_actual_fee:,.0f}만" if not is_fa else "FA (자유계약)")
                st.markdown(f"""
                - **외부 시장 진단**: **{ext_status_label}**
                - **실제 거래액**: `{fee_ext_str}`
                """)

        with st.expander("🔍 [실시간 확인] 12대 세부 가중치 적용 현황표 & 누적 배율", expanded=True):
            total_multiplier = league_w * age_w * club_w * contract_w * pos_w * vers_w * reg_w * opta_w * ttype_w * stage_w * inj_w * urg_w * season_factor
            
            df_weights_live = pd.DataFrame({
                "가중치 세부 항목": [
                    "① 원소속 리그 템포 난이도", "② 포지션별 나이(에이징 커브)", "③ 영입 구단 규모 (클럽 티어)",
                    "④ 이적 당시 잔여 계약 기간", "⑤ 주 포지션 시장 희소성", "⑥ 멀티 포지션 소화 능력",
                    "⑦ 스쿼드 등록 / HG 쿼터", "⑧ FotMob 실적 및 평점 가중치", "⑨ 이적 형태 & 계약 조항",
                    "⑩ UCL / 빅매치 검증도", "⑪ 부상 내구성 & 메디컬 리스크", "⑫ 영입 구단 절박성 & 취약 포지션",
                    "❄️ 계절성 프리미엄 (겨울 특수)", "🎯 [종합] 최종 누적 가중치 배율"
                ],
                "선택된 조건 / 등급": [
                    selling_league.split(" (")[0], f"만 {player_age}세 ({pos_short})", buying_club_tier.split(":")[0],
                    remaining_contract.split(" (")[0], pos_short, versatility.split(" (")[0],
                    reg_status.split(" (")[0], f"★{cur_rating:.2f} ({opta_desc.split(' (')[0]})", ttype_short,
                    big_stage.split(" (")[0], injury_status.split(" (")[0], urgency_status.split(" (")[0],
                    "+10% 겨울 프리미엄" if is_winter else "여름 표준 시장", "12대 가중치 총 곱셈 합산"
                ],
                "실시간 배율": [
                    f"{league_w:.2f}x", f"{age_w:.2f}x", f"{club_w:.2f}x", f"{contract_w:.2f}x",
                    f"{pos_w:.2f}x", f"{vers_w:.2f}x", f"{reg_w:.2f}x", f"{opta_w:.2f}x",
                    f"{ttype_w:.2f}x", f"{stage_w:.2f}x", f"{inj_w:.2f}x", f"{urg_w:.2f}x",
                    f"{season_factor:.2f}x", f"✨ {total_multiplier:.3f}x"
                ]
            })
            st.table(df_weights_live)

    st.markdown("---")
    display_pname_t1 = player_name.strip() if player_name.strip() else "선수명 미입력"
    tag_btn_name_t1 = "🔴 방출(OUT) 데이터" if is_out_trade else "🔵 영입(IN) 데이터"
    
    action_type = "update" if edit_toggle else "save_all"
    btn_label_t1 = f"🔄 '{display_pname_t1}' 수정된 데이터 구글 시트에 업데이트(덮어쓰기)" if edit_toggle else f"💾 {tag_btn_name_t1} 구글 시트에 바로 저장하기 (총 54개 항목 동기화)"
    
    if st.button(btn_label_t1, type="primary", use_container_width=True, key="save_btn_tab1"):
        if not player_name.strip():
            st.warning("⚠️ 선수 이름을 먼저 입력해 주세요.")
        else:
            spinner_msg = f"'{player_name}' 선수의 데이터를 구글 시트에 업데이트(수정) 중입니다..." if edit_toggle else "구글 시트에 신규 데이터를 기록 중입니다..."
            
            with st.spinner(spinner_msg):
                contract_desc = remaining_contract.split(" (")[0]
                nat_str = player_nat if player_nat.strip() else "미상"
                detailed_notes = f"[{'방출' if is_out_trade else '영입'}|{ttype_short}|{reg_short}|{urg_short}|UCL:{stage_w:.2f}|메디컬:{inj_w:.2f}] 계약:{contract_desc}"
                if option_exercised:
                    detailed_notes += " | [임대후옵션발동완료]"
                if player_notes.strip():
                    detailed_notes += f" | {player_notes.strip()}"
                
                is_gk = "GK" in main_position
                if is_gk:
                    detailed_notes += f" | GK[선방:{st.session_state.get('f_gk_saves', 0)}|실점:{st.session_state.get('f_gk_conceded', 0)}]"

                f_target_mins_t1 = st.session_state.get("custom_proj_mins", 3000)
                if f_target_mins_t1 <= 0:
                    f_target_mins_t1 = 1440 if is_winter else 3036

                raw_lf_t1 = LEAGUE_WEIGHTS[selling_league] / (LEAGUE_WEIGHTS.get(in_to_league_choice, 1.0))
                adapt_p_t1 = max(0.80, 1.0 - (max(0.0, LEAGUE_WEIGHTS.get(in_to_league_choice, 1.0) - LEAGUE_WEIGHTS[selling_league]) * 0.45))
                final_lf_t1 = raw_lf_t1 * adapt_p_t1
                t_p90_t1 = f_target_mins_t1 / 90.0

                if not is_gk:
                    p90_xg_t1 = (float(st.session_state["f_xg"]) / f_p90) * final_lf_t1
                    p90_xa_t1 = (float(st.session_state["f_xa"]) / f_p90) * final_lf_t1
                    p90_shots_t1 = (float(st.session_state["f_shots"]) / f_p90) * final_lf_t1
                    fin_ratio_t1 = float(st.session_state["f_goals"]) / float(st.session_state["f_xg"]) if float(st.session_state["f_xg"]) > 0 else 1.0
                    pj_goals_t1 = round(p90_xg_t1 * t_p90_t1 * fin_ratio_t1, 1)
                    pj_xg_t1 = round(p90_xg_t1 * t_p90_t1, 2)
                    pj_assists_t1 = round(p90_xa_t1 * t_p90_t1, 1)
                    pj_xa_t1 = round(p90_xa_t1 * t_p90_t1, 2)
                    pj_shots_t1 = round(p90_shots_t1 * t_p90_t1, 0)
                else:
                    pj_goals_t1 = 0.0; pj_xg_t1 = 0.0; pj_assists_t1 = 0.0; pj_xa_t1 = 0.0; pj_shots_t1 = 0.0

                pj_rating_t1 = round(max(6.0, cur_rating - (1.0 - final_lf_t1) * 0.9), 2)

                payload = {
                    "action": action_type,
                    "row_index": st.session_state.get("edit_row_index"),
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "season": season_val,
                    "name": player_name,
                    "nat": nat_str,
                    "age": int(player_age),
                    "pos": pos_short,
                    "from_league": selling_league.split(" (")[0],
                    "buying_tier": buying_club_tier.split(":")[0],
                    "transfer_type": ttype_short,
                    "tm_val": float(tm_market_value),
                    "fee": float(calc_actual_fee),
                    "fair_val": round(fair_value, 1),
                    "diff": round(diff, 1),
                    "status": status_label,
                    "deal_score": float(final_deal_score),
                    "prev_matches": int(st.session_state["f_matches"]),
                    "prev_starts": int(st.session_state.get("f_starts", 0)),
                    "prev_mins": int(st.session_state["f_mins"]),
                    "prev_goals": int(st.session_state["f_goals"]),
                    "prev_xg": float(st.session_state["f_xg"]),
                    "prev_assists": int(st.session_state["f_assists"]),
                    "prev_xa": float(st.session_state["f_xa"]),
                    "prev_shots": int(st.session_state["f_shots"]),
                    "prev_sot": int(st.session_state["f_sot"]),
                    "prev_chances": int(st.session_state["f_chances"]),
                    "prev_dribbles": int(st.session_state["f_dribbles"]),
                    "prev_touches_box": int(st.session_state["f_touches_box"]),
                    "prev_tackles": int(st.session_state["f_tackles"]),
                    "prev_rating": float(cur_rating),
                    "big_chances": int(st.session_state.get("f_big_chances", 0)),
                    "pk_goals": int(st.session_state.get("f_pk_goals", 0)),
                    "pass_pct": float(st.session_state.get("f_pass_pct", 0.0)),
                    "duels_pct": float(st.session_state.get("f_duels_pct", 0.0)),
                    "aerial_pct": float(st.session_state.get("f_aerial_pct", 0.0)),
                    "to_league": in_to_league_choice.split(" (")[0],
                    "proj_mins": int(f_target_mins_t1),
                    "proj_goals": float(pj_goals_t1),
                    "proj_xg": float(pj_xg_t1),
                    "proj_assists": float(pj_assists_t1),
                    "proj_xa": float(pj_xa_t1),
                    "proj_shots": float(pj_shots_t1),
                    "proj_rating": float(pj_rating_t1),
                    "notes": detailed_notes,
                    "from_team": in_from_team.strip(),
                    "to_team": in_to_team.strip(),
                    "to_league_name": in_to_league_choice.split(" (")[0],
                    "trade_type": "OUT" if is_out_trade else "IN",
                    "weekly_wage": float(weekly_wage_in) if 'weekly_wage_in' in locals() else 0.0,
                    "gk_saves": int(st.session_state.get("f_gk_saves", 0)) if is_gk else 0,
                    "gk_conceded": int(st.session_state.get("f_gk_conceded", 0)) if is_gk else 0,
                    "gk_prevented": float(st.session_state.get("f_gk_prevented", 0.0)) if is_gk else 0,
                    "gk_cs": int(st.session_state.get("f_gk_cs", 0)) if is_gk else 0,
                    "gk_errors": int(st.session_state.get("f_gk_errors", 0)) if is_gk else 0,
                    "gk_claims": int(st.session_state.get("f_gk_claims", 0)) if is_gk else 0
                }
                
                try:
                    res = requests.post(
                        GOOGLE_SHEET_WEBAPP_URL, 
                        data=json.dumps(payload), 
                        headers={"Content-Type": "text/plain;charset=utf-8"}, 
                        timeout=30, 
                        allow_redirects=True
                    )
                    res_json = res.json()
                    if res.status_code in [200, 302] and res_json.get("status") == "success":
                        st.session_state["last_saved_msg"] = f"✅ '{player_name}' 선수의 데이터가 성공적으로 {'수정(업데이트)' if edit_toggle else '저장'}되었습니다!"
                        st.cache_data.clear()
                        
                        st.session_state["edit_row_index"] = None
                        reset_stats = {
                            "f_mins": 90, "f_goals": 0, "f_xg": 0.0, "f_assists": 0, "f_xa": 0.0,
                            "f_rating": 6.50, "f_matches": 1, "f_starts": 0, "f_shots": 0, "f_sot": 0,
                            "f_chances": 0, "f_dribbles": 0, "f_touches_box": 0, "f_tackles": 0,
                            "f_gk_saves": 0, "f_gk_conceded": 0, "f_gk_prevented": 0.0,
                            "f_gk_cs": 0, "f_gk_errors": 0, "f_gk_claims": 0,
                            "f_big_chances": 0, "f_pk_goals": 0, "f_pass_pct": 0.0, "f_duels_pct": 0.0, "f_aerial_pct": 0.0,
                            "custom_proj_mins": 3000
                        }
                        for r_k, r_v in reset_stats.items():
                            st.session_state[r_k] = r_v

                        st.session_state["form_key_id"] += 1
                        st.session_state["stat_key_id"] += 1
                        st.rerun()
                    else:
                        st.error(f"⚠️ 저장/수정 실패: {res_json.get('message', '통신 오류')}")
                except Exception as e:
                    st.error(f"⚠️ 저장 오류: {e}")

# ================= TAB 2: FotMob 시즌 성적 & 이적 예측 =================
with tab2:
    st.subheader("📱 FotMob 스타일 시즌 스탯 입력 & 이적 첫 시즌 성적 프로젝션")
    
    winter_data_source = st.radio(
        "📋 데이터 입력 기준 모드 선택",
        [
            "☀️ 직전 풀 시즌 스탯 (여름 이적 표준 / 1년 전체)",
            "❄️ 이번 시즌 전반기 스탯 (겨울 이적 표준, 8월~1월)",
            "⚠️ 직전 풀 시즌 스탯 (겨울 이적생 중 전반기 300~400분 미만 결장/부상 시)"
        ],
        index=1 if is_winter else 0,
        horizontal=True,
        key=f"global_data_source_radio_{k_id}"
    )

    is_winter_mode = "겨울" in winter_data_source
    
    f_c1, f_c2, f_c3 = st.columns(3)
    with f_c1: f_pos = st.selectbox("선수 포지션 분류", ["⚽ 필드 플레이어 (공격수/미드필더/수비수)", "🧤 골키퍼 (Goalkeeper)"], index=1 if "GK" in main_position else 0, key=f"f_tab_pos_{k_id}")
    with f_c2: f_from_l = st.selectbox("원소속 리그 (기록 기준)", list(LEAGUE_WEIGHTS.keys()), index=list(LEAGUE_WEIGHTS.keys()).index(selling_league) if selling_league in LEAGUE_WEIGHTS else 0, key=f"f_tab_from_l_{k_id}")
    with f_c3: f_to_l = st.selectbox("이적할 리그", list(LEAGUE_WEIGHTS.keys()), index=list(LEAGUE_WEIGHTS.keys()).index(in_to_league_choice) if in_to_league_choice in LEAGUE_WEIGHTS else 0, key=f"f_tab_to_l_{k_id}")
    
    time_preset_options = [
        "직접 수동 입력 (아래 입력창 사용)",
        "🔥 메인 핵심 주전 (3,000분 / 34~38경기 풀타임)",
        "⭐ 준주전 / 주력 로테이션 (2,200분 / 22~25경기 선발급)",
        "⚖️ 로테이션 뎁스 자원 (1,500분 / 15~18경기 선발급)",
        "🌱 유망주 / 로테이션 벤치 자원 (900분 / 8~10경기 선발급)",
        "❄️ 겨울 이적생 후반기 잔여 소화 (1,440분 / 후반기 풀타임)"
    ]
    
    preset_mapping = {
        "🔥 메인 핵심 주전 (3,000분 / 34~38경기 풀타임)": 3000,
        "⭐ 준주전 / 주력 로테이션 (2,200분 / 22~25경기 선발급)": 2200,
        "⚖️ 로테이션 뎁스 자원 (1,500분 / 15~18경기 선발급)": 1500,
        "🌱 유망주 / 로테이션 벤치 자원 (900분 / 8~10경기 선발급)": 900,
        "❄️ 겨울 이적생 후반기 잔여 소화 (1,440분 / 후반기 풀타임)": 1440
    }
    
    sel_time_preset = st.selectbox("출전 시간 세분화 프리셋 선택", time_preset_options, index=0, key=f"time_preset_box_{k_id}_{s_id}")
    
    if sel_time_preset != "직접 수동 입력 (아래 입력창 사용)":
        new_mins = preset_mapping[sel_time_preset]
        if st.session_state["custom_proj_mins"] != new_mins:
            st.session_state["custom_proj_mins"] = new_mins
            st.session_state["stat_key_id"] += 1
            st.rerun()

    f_target_mins = st.number_input(
        "최종 적용될 예상 출전 시간(분)", 
        min_value=0, 
        max_value=4500, 
        value=int(st.session_state["custom_proj_mins"]), 
        step=90, 
        key=f"f_tab_target_mins_{k_id}_{s_id}"
    )
    st.session_state["custom_proj_mins"] = f_target_mins
    
    raw_l_factor = LEAGUE_WEIGHTS[f_from_l] / LEAGUE_WEIGHTS[f_to_l]
    if LEAGUE_WEIGHTS[f_to_l] > LEAGUE_WEIGHTS[f_from_l]:
        diff_level = LEAGUE_WEIGHTS[f_to_l] - LEAGUE_WEIGHTS[f_from_l]
        adapt_penalty = max(0.80, 1.0 - (diff_level * 0.45))
        adapt_desc = f"⚠️ 상위 리그 스텝업 적응 감가 적용 ({adapt_penalty:.2f}x)"
    else:
        adapt_penalty = 1.00
        adapt_desc = "✅ 동급/하위 리그 이적 (적응 페널티 없음)"
        
    final_l_factor = raw_l_factor * adapt_penalty
    
    st.divider()
    st.markdown(f"### 📥 FotMob 시즌 실제 기록 입력 (`{winter_data_source.split(' (')[0]}` 기준)")

    b1, b2, b3, b4 = st.columns(4)
    with b1: in_matches = st.number_input("출전 경기 (Matches)", 0, 60, value=min(int(st.session_state["f_matches"]), 60), key=f"in_matches_box_{k_id}_{s_id}")
    with b2: in_starts = st.number_input("선발 출전 (Starts)", 0, 60, value=min(int(st.session_state["f_starts"]), 60), key=f"in_starts_box_{k_id}_{s_id}")
    with b3: in_mins = st.number_input("출전 시간 (Minutes)", 0, 4500, value=min(int(st.session_state["f_mins"]), 4500), key=f"in_mins_box_{k_id}_{s_id}")
    
    safe_rating_val = max(0.0, min(10.0, float(st.session_state["f_rating"])))
    with b4: in_rating = st.number_input("FotMob 평균 평점", 0.0, 10.0, value=safe_rating_val, step=0.01, key=f"in_rating_box_{k_id}_{s_id}")
    
    st.session_state["f_mins"] = in_mins
    st.session_state["f_rating"] = in_rating
    st.session_state["f_matches"] = in_matches
    st.session_state["f_starts"] = in_starts

    base_p90 = in_mins / 90.0 if in_mins > 0 else 1.0
    target_p90 = f_target_mins / 90.0

    if "골키퍼" not in f_pos:
        s1, s2, s3, s4, s5 = st.columns(5)
        with s1: in_goals = st.number_input("득점 (Goals)", 0, 50, value=min(int(st.session_state["f_goals"]), 50), key=f"in_goals_box_{k_id}_{s_id}")
        with s2: in_xg = st.number_input("기대 득점 (xG)", 0.0, 50.0, value=min(float(st.session_state["f_xg"]), 50.0), step=0.01, key=f"in_xg_box_{k_id}_{s_id}")
        with s3: in_shots = st.number_input("총 슈팅 (Shots)", 0, 200, value=min(int(st.session_state["f_shots"]), 200), key=f"in_shots_box_{k_id}_{s_id}")
        with s4: in_sot = st.number_input("유효 슈팅 (On Target)", 0, 100, value=min(int(st.session_state["f_sot"]), 100), key=f"in_sot_box_{k_id}_{s_id}")
        with s5: in_pk_goals = st.number_input("PK 득점 (Penalty)", 0, 20, value=min(int(st.session_state["f_pk_goals"]), 20), key=f"in_pk_box_{k_id}_{s_id}")

        st.session_state["f_goals"] = in_goals
        st.session_state["f_xg"] = in_xg
        st.session_state["f_shots"] = in_shots
        st.session_state["f_sot"] = in_sot
        st.session_state["f_pk_goals"] = in_pk_goals

        p1, p2, p3, p4, p5 = st.columns(5)
        with p1: in_assists = st.number_input("도움 (Assists)", 0, 50, value=min(int(st.session_state["f_assists"]), 50), key=f"in_assists_box_{k_id}_{s_id}")
        with p2: in_xa = st.number_input("기대 도움 (xA)", 0.0, 50.0, value=min(float(st.session_state["f_xa"]), 50.0), step=0.01, key=f"in_xa_box_{k_id}_{s_id}")
        with p3: in_chances = st.number_input("기회 창출 (Chances)", 0, 150, value=min(int(st.session_state["f_chances"]), 150), key=f"in_chances_box_{k_id}_{s_id}")
        with p4: in_big_chances = st.number_input("빅 찬스 메이킹", 0, 50, value=min(int(st.session_state["f_big_chances"]), 50), key=f"in_bc_box_{k_id}_{s_id}")
        with p5: in_pass_pct = st.number_input("패스 성공률 (%)", 0.0, 100.0, value=float(st.session_state["f_pass_pct"]), step=0.1, key=f"in_pass_pct_box_{k_id}_{s_id}")

        st.session_state["f_assists"] = in_assists
        st.session_state["f_xa"] = in_xa
        st.session_state["f_chances"] = in_chances
        st.session_state["f_big_chances"] = in_big_chances
        st.session_state["f_pass_pct"] = in_pass_pct

        d1, d2, d3, d4, d5 = st.columns(5)
        with d1: in_dribbles = st.number_input("성공한 드리블", 0, 100, value=min(int(st.session_state["f_dribbles"]), 100), key=f"in_dribbles_box_{k_id}_{s_id}")
        with d2: in_touches_box = st.number_input("박스 안 터치 (Box Touches)", 0, 300, value=min(int(st.session_state["f_touches_box"]), 300), key=f"in_touches_box_{k_id}_{s_id}")
        with d3: in_duels_pct = st.number_input("지상 경합 승률 (%)", 0.0, 100.0, value=float(st.session_state["f_duels_pct"]), step=0.1, key=f"in_duels_box_{k_id}_{s_id}")
        with d4: in_aerial_pct = st.number_input("공중볼 승률 (%)", 0.0, 100.0, value=float(st.session_state["f_aerial_pct"]), step=0.1, key=f"in_aerial_box_{k_id}_{s_id}")
        with d5: in_tackles = st.number_input("태클 성공 (Tackles)", 0, 150, value=min(int(st.session_state["f_tackles"]), 150), key=f"in_tackles_box_{k_id}_{s_id}")

        st.session_state["f_dribbles"] = in_dribbles
        st.session_state["f_touches_box"] = in_touches_box
        st.session_state["f_tackles"] = in_tackles
        st.session_state["f_duels_pct"] = in_duels_pct
        st.session_state["f_aerial_pct"] = in_aerial_pct

    else:
        gk1, gk2, gk3 = st.columns(3)
        with gk1: in_gk_saves = st.number_input("선방 (Saves)", 0, 250, value=int(st.session_state["f_gk_saves"]), key=f"in_gk_saves_box_{k_id}_{s_id}")
        with gk2: in_gk_conceded = st.number_input("실점 수 (Goals Conceded)", 0, 120, value=int(st.session_state["f_gk_conceded"]), key=f"in_gk_conceded_box_{k_id}_{s_id}")
        with gk3: in_gk_prevented = st.number_input("득점 차단 (Goals Prevented)", -20.0, 30.0, value=float(st.session_state["f_gk_prevented"]), step=0.01, key=f"in_gk_prevented_box_{k_id}_{s_id}")

        gk4, gk5, gk6 = st.columns(3)
        with gk4: in_gk_cs = st.number_input("클린 시트 (Clean Sheets)", 0, 35, value=int(st.session_state["f_gk_cs"]), key=f"in_gk_cs_box_{k_id}_{s_id}")
        with gk5: in_gk_errors = st.number_input("골로 이어진 실수 (Errors Led to Goal)", 0, 15, value=int(st.session_state["f_gk_errors"]), key=f"in_gk_errors_box_{k_id}_{s_id}")
        with gk6: in_gk_claims = st.number_input("공중에서 잡기 (High Claims)", 0, 80, value=int(st.session_state["f_gk_claims"]), key=f"in_gk_claims_box_{k_id}_{s_id}")

        st.session_state["f_gk_saves"] = in_gk_saves
        st.session_state["f_gk_conceded"] = in_gk_conceded
        st.session_state["f_gk_prevented"] = in_gk_prevented
        st.session_state["f_gk_cs"] = in_gk_cs
        st.session_state["f_gk_errors"] = in_gk_errors
        st.session_state["f_gk_claims"] = in_gk_claims

        in_goals = 0; in_xg = 0.0; in_shots = 0; in_sot = 0; in_assists = 0; in_xa = 0.0
        in_chances = 0; in_dribbles = 0; in_touches_box = 0; in_tackles = 0
        in_big_chances = 0; in_pk_goals = 0; in_pass_pct = 0.0; in_duels_pct = 0.0; in_aerial_pct = 0.0

    st.divider()

    if "골키퍼" not in f_pos:
        p90_xg = (in_xg / base_p90) * final_l_factor
        p90_xa = (in_xa / base_p90) * final_l_factor
        p90_shots = (in_shots / base_p90) * final_l_factor
        p90_sot = (in_sot / base_p90) * final_l_factor
        p90_chances = (in_chances / base_p90) * final_l_factor
        p90_dribbles = (in_dribbles / base_p90) * final_l_factor
        p90_box_touches = (in_touches_box / base_p90) * final_l_factor
        p90_tackles = (in_tackles / base_p90) * (1.0 / raw_l_factor)
        
        finishing_ratio = in_goals / in_xg if in_xg > 0 else 1.0
        proj_goals = round(p90_xg * target_p90 * finishing_ratio, 1)
        proj_xg = round(p90_xg * target_p90, 2)
        proj_assists = round(p90_xa * target_p90, 1)
        proj_xa = round(p90_xa * target_p90, 2)
        proj_shots = round(p90_shots * target_p90, 0)
        proj_rating = round(max(6.0, in_rating - (1.0 - final_l_factor) * 0.9), 2)
    else:
        proj_goals = 0.0; proj_xg = 0.0; proj_assists = 0.0; proj_xa = 0.0; proj_shots = 0.0
        proj_rating = round(max(6.0, in_rating - (1.0 - final_l_factor) * 0.9), 2)

    st.markdown("---")
    tag_btn_name = "🔴 방출(OUT) 데이터" if is_out_trade else "🔵 영입(IN) 데이터"
    
    if st.button(f"💾 {tag_btn_name} 구글 시트에 저장하기 (총 54개 항목 동기화)", type="primary", use_container_width=True, key="save_btn_tab2"):
        if not player_name.strip():
            st.warning("⚠️ 선수 이름을 [💰 적정 이적료 평가] 탭에 먼저 입력해 주세요.")
        else:
            with st.spinner("구글 시트에 거래 데이터를 기록 중입니다..."):
                contract_desc = remaining_contract.split(" (")[0]
                nat_str = player_nat if player_nat.strip() else "미상"
                detailed_notes = f"[{'방출' if is_out_trade else '영입'}|{ttype_short}|{reg_short}|{urg_short}|UCL:{stage_w:.2f}|메디컬:{inj_w:.2f}] 계약:{contract_desc}"
                if option_exercised:
                    detailed_notes += " | [임대후옵션발동완료]"
                if is_winter_mode:
                    detailed_notes += f" | 겨울기준:{winter_data_source.split(' (')[0]}"
                if player_notes.strip():
                    detailed_notes += f" | {player_notes.strip()}"
                    
                f_target_mins_t2 = st.session_state.get("custom_proj_mins", 3000)
                if f_target_mins_t2 <= 0:
                    f_target_mins_t2 = 1440 if is_winter else 3036

                payload = {
                    "action": "save_all",
                    "row_index": None,
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "season": season_val,
                    "name": player_name,
                    "nat": nat_str,
                    "age": int(player_age),
                    "pos": pos_short,
                    "from_league": selling_league.split(" (")[0],
                    "buying_tier": buying_club_tier.split(":")[0],
                    "transfer_type": ttype_short,
                    "tm_val": float(tm_market_value),
                    "fee": float(calc_actual_fee),
                    "fair_val": round(fair_value, 1),
                    "diff": round(diff, 1),
                    "status": status_label,
                    "deal_score": float(final_deal_score),
                    "prev_matches": int(st.session_state["f_matches"]),
                    "prev_starts": int(st.session_state.get("f_starts", 0)),
                    "prev_mins": int(st.session_state["f_mins"]),
                    "prev_goals": int(in_goals),
                    "prev_xg": float(in_xg),
                    "prev_assists": int(in_assists),
                    "prev_xa": float(in_xa),
                    "prev_shots": int(in_shots),
                    "prev_sot": int(in_sot if 'in_sot' in locals() else 0),
                    "prev_chances": int(in_chances),
                    "prev_dribbles": int(in_dribbles),
                    "prev_touches_box": int(in_touches_box),
                    "prev_tackles": int(in_tackles),
                    "prev_rating": float(st.session_state["f_rating"]),
                    "big_chances": int(st.session_state.get("f_big_chances", 0)),
                    "pk_goals": int(st.session_state.get("f_pk_goals", 0)),
                    "pass_pct": float(st.session_state.get("f_pass_pct", 0.0)),
                    "duels_pct": float(st.session_state.get("f_duels_pct", 0.0)),
                    "aerial_pct": float(st.session_state.get("f_aerial_pct", 0.0)),
                    "to_league": f_to_l.split(" (")[0],
                    "proj_mins": int(f_target_mins_t2),
                    "proj_goals": float(proj_goals),
                    "proj_xg": float(proj_xg),
                    "proj_assists": float(proj_assists),
                    "proj_xa": float(proj_xa),
                    "proj_shots": float(proj_shots),
                    "proj_rating": float(proj_rating),
                    "notes": detailed_notes,
                    "from_team": in_from_team.strip(),
                    "to_team": in_to_team.strip(),
                    "to_league_name": in_to_league_choice.split(" (")[0],
                    "trade_type": "OUT" if is_out_trade else "IN",
                    "weekly_wage": float(weekly_wage_in) if 'weekly_wage_in' in locals() else 0.0,
                    "gk_saves": int(st.session_state.get("f_gk_saves", 0)) if "골키퍼" in f_pos else 0,
                    "gk_conceded": int(st.session_state.get("f_gk_conceded", 0)) if "골키퍼" in f_pos else 0,
                    "gk_prevented": float(st.session_state.get("f_gk_prevented", 0.0)) if "골키퍼" in f_pos else 0.0,
                    "gk_cs": int(st.session_state.get("f_gk_cs", 0)) if "골키퍼" in f_pos else 0,
                    "gk_errors": int(st.session_state.get("f_gk_errors", 0)) if "골키퍼" in f_pos else 0,
                    "gk_claims": int(st.session_state.get("f_gk_claims", 0)) if "골키퍼" in f_pos else 0
                }
                
                try:
                    res = requests.post(
                        GOOGLE_SHEET_WEBAPP_URL, 
                        data=json.dumps(payload), 
                        headers={"Content-Type": "text/plain;charset=utf-8"}, 
                        timeout=30, 
                        allow_redirects=True
                    )
                    if res.status_code in [200, 302]:
                        st.session_state["last_saved_msg"] = f"✅ '{player_name}' 선수의 데이터가 성공적으로 저장되었습니다!"
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error("⚠️ 저장 실패")
                except Exception as e:
                    st.error(f"⚠️ 저장 오류: {e}")

# ================= TAB 3: 과거 유사 이적 사례 비교 =================
with tab3:
    st.subheader("🔍 과거 유사 이적 사례 검색 및 벤치마크 비교 (Comps TOP 5 & 10)")
    st.caption("구글 시트에 누적된 이전 이적 데이터 중 이적료, 총 평점, 평가율(고평가/저평가), 출발 리그가 가장 유사한 과거 사례를 매칭합니다.")
    
    c_in1, c_in2, c_in3, c_in4, c_in5 = st.columns(5)
    with c_in1:
        target_fee = st.number_input("비교 기준 이적료 (만 €)", min_value=0, value=int(calc_actual_fee) if calc_actual_fee > 0 else 5000, step=100, key="comps_fee")
    with c_in2:
        target_score = st.number_input("비교 기준 이적 평점", min_value=1.00, max_value=10.00, value=float(final_deal_score) if final_deal_score > 0 else 7.50, step=0.1, key="comps_score")
    with c_in3:
        target_overpay = st.number_input("비교 기준 평가율 (%)", min_value=-100.0, max_value=200.0, value=float(overpay_pct), step=1.0, key="comps_overpay")
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

# ================= TAB 4: 이적 첫 시즌 실제 성적 입력 & 모델 검증 =================
with tab4:
    st.subheader("🎯 이적 첫 시즌 실제 성적 입력 & 모델 예측 정확도 사후 검증")
    st.caption("시즌 종료 후 선수가 실제로 기록한 최종 스탯(xG, xA 포함)을 입력하여 모델 예측치와의 오차율 및 적중률을 산출하고 [검증데이터] 시트에 업데이트합니다.")

    val_df = fetch_validation_data()

    if val_df.empty or len(val_df) == 0 or "이적시즌" not in val_df.columns:
        st.info("💡 **아직 [검증데이터] 탭에 저장된 데이터가 없습니다.**\n\n- 2번 탭에서 10대 핵심 리그 이적 선수를 저장하시면 이곳에 자동으로 나타납니다.")
    else:
        def check_status(row):
            act_r = str(row.get("실제_평점", "")).strip()
            act_m = str(row.get("실제_출전시간", "")).strip()
            if act_r != "" and act_r != "nan" and act_r != "None" and act_m != "" and act_m != "nan" and act_m != "None" and act_m != "0":
                return "✅ 검증 완료"
            return "⏳ 검증 대기"

        val_df["입력상태"] = val_df.apply(check_status, axis=1)

        st.markdown("#### 1️⃣ 검증할 시즌 및 미입력 선수 필터링")
        available_seasons = list(val_df["이적시즌"].dropna().unique())
        
        v_top1, v_top2 = st.columns([1, 1])
        with v_top1:
            sel_val_season = st.selectbox("이적 시즌 선택", available_seasons, key="val_sel_season")

        filtered_season_df = val_df[val_df["이적시즌"] == sel_val_season]
        
        total_in_season = len(filtered_season_df)
        completed_cnt = len(filtered_season_df[filtered_season_df["입력상태"] == "✅ 검증 완료"])
        pending_cnt = total_in_season - completed_cnt
        progress_pct = (completed_cnt / total_in_season * 100) if total_in_season > 0 else 0.0

        with v_top2:
            st.info(f"📊 **`{sel_val_season}` 검증 진행도**: **총 {total_in_season}명 중 {completed_cnt}명 완료 / {pending_cnt}명 대기** (`{progress_pct:.0f}%` 달성)")

        show_pending_only = st.checkbox("⏳ 실제 성적 미입력(검증 대기) 선수만 모아보기", value=True if pending_cnt > 0 else False, key="filter_pending_only")

        if show_pending_only:
            target_player_pool = filtered_season_df[filtered_season_df["입력상태"] == "⏳ 검증 대기"]
        else:
            target_player_pool = filtered_season_df

        available_players = list(target_player_pool["선수명"].dropna().unique()) if "선수명" in target_player_pool.columns else []

        if not available_players:
            if show_pending_only:
                st.success("🎉 이번 시즌 모든 10대 리그 영입 선수의 실제 성적 입력 및 검증이 100% 완료되었습니다!")
            else:
                st.warning("선택하신 조건에 해당하는 선수가 없습니다.")
        else:
            sel_val_player = st.selectbox(
                f"선수 선택 ({len(available_players)}명 대상)", 
                available_players, 
                key="val_sel_player"
            )

            target_row = target_player_pool[target_player_pool["선수명"] == sel_val_player].iloc[-1]

            p_pos = str(target_row.get("포지션", "CB"))
            p_to_l = str(target_row.get("이적리그", "EPL"))
            proj_m = float(target_row.get("예측_출전시간", 3000))
            proj_g = float(target_row.get("예측_골", 0))
            proj_xg = float(target_row.get("예측_xG", 0))
            proj_a = float(target_row.get("예측_도움", 0))
            proj_xa = float(target_row.get("예측_xA", 0))
            proj_r = float(target_row.get("예측_평점", 7.0))
            curr_status = str(target_row.get("입력상태", "⏳ 검증 대기"))

            st.markdown("---")
            st.markdown(f"#### 2️⃣ **'{sel_val_player}'** 선수의 [모델 예측치] vs [시즌 실제 기록 입력] ({curr_status})")
            st.caption(f"📌 포지션: **{p_pos}** | 활약 리그: **{p_to_l}**")

            st.markdown("##### 📌 모델이 예측했던 기대 수치")
            pm1, pm2, pm3, pm4, pm5 = st.columns(5)
            pm1.metric("예측 출전시간", f"{int(proj_m):,}분")
            pm2.metric("예측 득점 (xG)", f"{proj_g:.1f}골", delta=f"xG {proj_xg:.2f}")
            pm3.metric("예측 도움 (xA)", f"{proj_a:.1f}도움", delta=f"xA {proj_xa:.2f}")
            pm4.metric("예측 공격포인트", f"{proj_g + proj_a:.1f}P")
            pm5.metric("예측 평점", f"★ {proj_r:.2f}")

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("##### 📥 시즌 종료 후 실제 최종 기록 입력 (FotMob 기준)")
            
            def safe_get_val(row, col_name, default_val):
                try:
                    val = row.get(col_name)
                    if pd.notnull(val) and str(val).strip() not in ["", "nan", "None"]:
                        return float(val) if isinstance(default_val, float) else int(float(val))
                except:
                    pass
                return default_val

            exist_act_mins = safe_get_val(target_row, "실제_출전시간", int(proj_m))
            exist_act_goals = safe_get_val(target_row, "실제_골", int(round(proj_g)))
            exist_act_xg = safe_get_val(target_row, "실제_xG", float(proj_xg))
            exist_act_assists = safe_get_val(target_row, "실제_도움", int(round(proj_a)))
            exist_act_xa = safe_get_val(target_row, "실제_xA", float(proj_xa))
            exist_act_rating = safe_get_val(target_row, "실제_평점", float(proj_r))
            exist_act_notes = str(target_row.get("검증메모", "")) if pd.notnull(target_row.get("검증메모")) else ""

            in_ac1, in_ac2, in_ac3, in_ac4, in_ac5, in_ac6 = st.columns(6)
            with in_ac1: act_mins_val = st.number_input("실제 출전 시간(분)", 0, 4500, value=exist_act_mins, step=90, key="val_act_mins")
            with in_ac2: act_goals_val = st.number_input("실제 득점(Goals)", 0, 60, value=exist_act_goals, step=1, key="val_act_goals")
            with in_ac3: act_xg_val = st.number_input("실제 기대득점(xG)", 0.0, 50.0, value=exist_act_xg, step=0.01, key="val_act_xg")
            with in_ac4: act_assists_val = st.number_input("실제 도움(Assists)", 0, 40, value=exist_act_assists, step=1, key="val_act_assists")
            with in_ac5: act_xa_val = st.number_input("실제 기대도움(xA)", 0.0, 30.0, value=exist_act_xa, step=0.01, key="val_act_xa")
            with in_ac6: act_rating_val = st.number_input("실제 FotMob 평균 평점", 4.0, 10.0, value=exist_act_rating, step=0.01, key="val_act_rating")

            act_notes_val = st.text_input("사후 검증 스카우팅 총평 / 비고", value=exist_act_notes, placeholder="예: 리그 적응 성공, 모델 예측 xG 및 평점 정확도 매우 우수", key="val_act_notes")

            rating_error = abs(act_rating_val - proj_r)
            rating_accuracy = max(0.0, round((1.0 - (rating_error / 1.5)) * 100, 1))

            mins_diff = act_mins_val - proj_m
            goals_diff = act_goals_val - proj_g
            xg_diff = act_xg_val - proj_xg
            assists_diff = act_assists_val - proj_a
            xa_diff = act_xa_val - proj_xa

            st.markdown("---")
            st.markdown("#### 3️⃣ **모델 예측 vs 실제 성적 1:1 정밀 대칭 비교 리포트**")
            
            comp_col1, comp_col2, comp_col3, comp_col4, comp_col5 = st.columns(5)
            comp_col1.metric("평점 적중률", f"{rating_accuracy}%", delta=f"{act_rating_val - proj_r:+.2f}점 오차")
            comp_col2.metric("실제 출전시간", f"{act_mins_val:,}분", delta=f"{mins_diff:+,.0f}분 차이")
            comp_col3.metric("실제 득점 (xG)", f"{act_goals_val}골", delta=f"xG 오차 {xg_diff:+.2f}")
            comp_col4.metric("실제 도움 (xA)", f"{act_assists_val}도움", delta=f"xA 오차 {xa_diff:+.2f}")
            comp_col5.metric("실제 공격포인트", f"{act_goals_val + act_assists_val}P", delta=f"{(act_goals_val + act_assists_val) - (proj_g + proj_a):+.1f}P 차이")

            if st.button("🚀 '검증데이터' 시트에 실제 최종 기록 업데이트하기", type="primary", use_container_width=True, key="update_actual_btn"):
                with st.spinner("구글 시트에 최종 실제 성적을 업데이트 중입니다..."):
                    update_payload = {
                        "action": "update_actual",
                        "season": sel_val_season,
                        "name": sel_val_player,
                        "act_mins": int(act_mins_val),
                        "act_goals": int(act_goals_val),
                        "act_xg": float(act_xg_val),
                        "act_assists": int(act_assists_val),
                        "act_xa": float(act_xa_val),
                        "act_rating": float(act_rating_val),
                        "notes": act_notes_val
                    }
                    try:
                        res = requests.post(
                            GOOGLE_SHEET_WEBAPP_URL, 
                            data=json.dumps(update_payload), 
                            headers={"Content-Type": "text/plain;charset=utf-8"}, 
                            timeout=30, 
                            allow_redirects=True
                        )
                        res_json = res.json()
                        if res_json.get("status") == "success":
                            st.success(f"✅ '{sel_val_player}' 선수의 실제 최종 성적이 성공적으로 기록되었습니다!")
                            st.cache_data.clear()
                            st.rerun()
                        else:
                            st.error(f"⚠️ 업데이트 실패: {res_json.get('message')}")
                    except Exception as e:
                        st.error(f"⚠️ 통신 오류: {e}")

        st.markdown("---")
        st.markdown("#### 📋 **[검증데이터] 시트 전체 누적 현황표 (상태 배지 포함)**")
        st.dataframe(val_df, use_container_width=True)

# ================= TAB 5: 신규 이적생 vs 과거 유사 선수 다각도 벤치마크 =================
with tab5:
    st.subheader("👥 신규 이적생 vs 과거 유사 이적 선수 다각도 벤치마크 (Multi-Comps)")
    st.caption("새로운 시즌 영입 선수의 프로필(나이, 포지션, 이적료 규모, 생산력)을 과거 시트에 누적된 다른 선수들의 실제 사례와 1:1 및 다차원으로 정밀 비교합니다.")

    if history_df.empty or len(history_df) == 0 or "선수명" not in history_df.columns:
        st.info("💡 **아직 구글 시트에 누적된 과거 이적 데이터가 없습니다.**\n\n1번 및 2번 탭에서 선수 데이터를 2명 이상 저장하시면 과거 선수들과의 1:1 교차 비교 및 벤치마크 매칭이 활성화됩니다.")
    else:
        st.markdown("#### 1️⃣ 신규 분석 대상 선수 프로필 설정 (1번 탭 데이터 자동 연동)")
        
        p_curr_name = player_name.strip() if player_name.strip() else "신규 영입 대상 선수"
        p_curr_age = int(player_age)
        p_curr_pos = main_position.split(" (")[0]
        p_curr_fee = float(calc_actual_fee) if calc_actual_fee > 0 else 5000.0
        p_curr_score = float(final_deal_score) if final_deal_score > 0 else 7.50
        p_curr_p90 = (st.session_state["f_xg"] + st.session_state["f_xa"]) / ((st.session_state["f_mins"] / 90.0) if st.session_state["f_mins"] > 0 else 1.0)
        p_curr_rating = float(st.session_state["f_rating"])

        c_prof1, c_prof2, c_prof3, c_prof4 = st.columns(4)
        c_prof1.metric("선수명 & 나이", f"{p_curr_name}", f"만 {p_curr_age}세")
        c_prof2.metric("포지션 & 리그", f"{p_curr_pos}", f"{selling_league.split(' ')[1]}")
        c_prof3.metric("실제 거래액", f"€{p_curr_fee:,.0f}만", f"평점 ★{p_curr_score:.2f}")
        c_prof4.metric("90분당 xG+xA / 평점", f"{p_curr_p90:.2f}", f"FotMob ★{p_curr_rating:.2f}")

        st.markdown("---")
        st.markdown("#### 2️⃣ 과거 유사 프로필 선수 1:1 직접 선택 대조 (Head-to-Head)")
        
        past_player_names = [str(n).strip() for n in history_df["선수명"].dropna().unique() if str(n).strip() not in ["", "nan"]]
        
        if not past_player_names:
            st.info("💡 과거 시트에 유효한 선수 데이터가 아직 없습니다.")
        else:
            selected_past_player = st.selectbox(
                "과거 비교 대상 선수 선택",
                past_player_names,
                index=0,
                key="bench_player_select"
            )

            past_target = history_df[history_df["선수명"] == selected_past_player].iloc[-1]

            t_name = str(past_target.get("선수명", "선수"))
            t_season = str(past_target.get("이적시즌", "26/27"))
            t_age = int(past_target.get("만나이", 25)) if pd.notnull(past_target.get("만나이")) else 25
            t_pos = str(past_target.get("포지션", "CB"))
            t_league = str(past_target.get("원소속리그", "EPL"))
            t_fee = float(past_target.get("실제이적료(만€)", 0))
            t_fair = float(past_target.get("산출적정가(만€)", 0))
            t_score = float(past_target.get("이적평점", 7.50))
            t_xg = float(past_target.get("이전_xG", 0.0)) if pd.notnull(past_target.get("이전_xG")) else 0.0
            t_xa = float(past_target.get("이전_xA", 0.0)) if pd.notnull(past_target.get("이전_xA")) else 0.0
            t_mins = float(past_target.get("이전_출전시간", 2500)) if pd.notnull(past_target.get("이전_출전시간")) else 2500.0
            t_rating = float(past_target.get("이전_FotMob평점", 7.0)) if pd.notnull(past_target.get("이전_FotMob평점")) else 7.0
            t_p90 = (t_xg + t_xa) / (t_mins / 90.0) if t_mins > 0 else 0.0

            df_bench = pd.DataFrame({
                "스카우팅 비교 항목": [
                    "이적 시즌 (Season)",
                    "만 나이",
                    "주 포지션",
                    "출발 리그",
                    "실제 거래액",
                    "데이터 기준 적정가",
                    "이적 총 평점 (10점 만점)",
                    "FotMob 평균 평점",
                    "90분당 기대 생산력 (xG+xA/90)"
                ],
                f"신규 대상: {p_curr_name}": [
                    f"{season_val.split(' (')[0]}",
                    f"만 {p_curr_age}세",
                    f"{p_curr_pos}",
                    f"{selling_league.split(' ')[1]}",
                    f"€{p_curr_fee:,.0f}만 ({format_currency_desc(p_curr_fee).split(' | ')[0]})",
                    f"€{fair_value:,.1f}만",
                    f"★ {final_deal_score:.2f} / 10.00",
                    f"★ {p_curr_rating:.2f}",
                    f"{p_curr_p90:.2f}"
                ],
                f"과거 비교: {t_name} ({t_season})": [
                    f"{t_season}",
                    f"만 {t_age}세",
                    f"{t_pos}",
                    f"{t_league}",
                    f"€{t_fee:,.0f}만 ({format_currency_desc(t_fee).split(' | ')[0]})",
                    f"€{t_fair:,.1f}만",
                    f"★ {t_score:.2f} / 10.00",
                    f"★ {t_rating:.2f}",
                    f"{t_p90:.2f}"
                ],
                "비교 격차 / 인사이트": [
                    "-",
                    f"{p_curr_age - t_age:+d}세",
                    "동일 포지션" if p_curr_pos in t_pos or t_pos in p_curr_pos else "포지션 상이",
                    "동일 리그 출신" if selling_league.split(' ')[1] in t_league else "리그 상이",
                    f"{p_curr_fee - t_fee:+,.0f}만 €",
                    f"{fair_value - t_fair:+,.1f}만 €",
                    f"{final_deal_score - t_score:+.2f}점",
                    f"{p_curr_rating - t_rating:+.2f}점",
                    f"{p_curr_p90 - t_p90:+.2f}"
                ]
            })

            st.table(df_bench)

            st.markdown("##### ⚔️ **두 선수의 1:1 스카우팅 프로필 레이더 비교**")
            bench_fig = go.Figure()
            comp_categories = ['이적료 규모', '이적 평점', '직전 FotMob 평점', '90분당 생산력', '나이(적정성)']
            
            p_val_scaled = [min(100, p_curr_fee/1000*10), final_deal_score*10, p_curr_rating*10, min(100, p_curr_p90*100), (35-p_curr_age)*5]
            t_val_scaled = [min(100, t_fee/1000*10), t_score*10, t_rating*10, min(100, t_p90*100), (35-t_age)*5]

            bench_fig.add_trace(go.Scatterpolar(r=p_val_scaled + [p_val_scaled[0]], theta=comp_categories + [comp_categories[0]], fill='toself', name=p_curr_name, line=dict(color='#1f77b4')))
            bench_fig.add_trace(go.Scatterpolar(r=t_val_scaled + [t_val_scaled[0]], theta=comp_categories + [comp_categories[0]], fill='toself', name=f"{t_name} ({t_season})", line=dict(color='#ff7f0e')))
            bench_fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), height=350, margin=dict(l=40, r=40, t=30, b=30))
            st.plotly_chart(bench_fig, use_container_width=True)

# ================= TAB 6: 이적시장 구단/리그별 종합 결산 & 데이터룸 =================
with tab6:
    st.subheader("🏆 이적시장 구단별 종합 성적표 & 리그 파워 랭킹 & 데이터룸")
    st.caption("시트에 누적된 영입(IN) 및 방출(OUT) 데이터를 종합하여 순지출(Net Spend)과 '이적료 가중 평균 평점' 기반의 구단/리그별 순위를 산출하고, 오기입된 데이터를 관리 및 삭제합니다.")

    if history_df.empty or len(history_df) == 0 or "이적시즌" not in history_df.columns:
        st.info("💡 **아직 구글 시트에 누적된 과거 이적 데이터가 없습니다.**\n\n1번 및 2번 탭에서 팀명을 포함하여 이적 데이터를 저장하시면 이곳에 구단별 성적표 및 리그별/전체 통합 파워 랭킹이 자동으로 집계됩니다.")
    else:
        rank_mode = st.radio("분석 모드 선택", ["🏢 구단별 이적시장 종합 성적표 (Club Report Card)", "🌍 리그별 / 10대 리그 전체 통합 파워 랭킹 (Power Rankings)", "🛠️ 저장 데이터 조회 및 삭제 관리 (Data Management)"], horizontal=True)

        st.markdown("---")

        if "구단별" in rank_mode:
            st.markdown("#### 🏢 **특정 구단의 이적시장 결산 성적표 (IN/OUT & 순지출)**")
            
            c_rc1, c_rc2 = st.columns(2)
            all_seasons = list(history_df["이적시즌"].dropna().unique())
            with c_rc1:
                sel_season_club = st.selectbox("조회할 이적 시즌", ["전체 시즌"] + all_seasons, index=0, key="report_season_sel")

            club_filtered_df = history_df if sel_season_club == "전체 시즌" else history_df[history_df["이적시즌"] == sel_season_club]
            
            to_teams = [str(t).strip() for t in club_filtered_df["이적팀명"].dropna().unique() if str(t).strip() not in ["", "nan"]] if "이적팀명" in club_filtered_df.columns else []
            from_teams = [str(t).strip() for t in club_filtered_df["원소속팀명"].dropna().unique() if str(t).strip() not in ["", "nan"]] if "원소속팀명" in club_filtered_df.columns else []
            all_club_names = sorted(list(set(to_teams + from_teams)))

            if not all_club_names:
                st.warning("⚠️ 아직 시트에 구단명이 입력된 이적 데이터가 없습니다. 1번 탭에서 구단명이 입력된 선수를 저장해보세요.")
            else:
                with c_rc2:
                    sel_team_name = st.selectbox("조회할 구단(팀) 선택", all_club_names, key="report_team_sel")

                team_in_df = club_filtered_df[club_filtered_df["이적팀명"].astype(str).str.strip() == sel_team_name].copy() if "이적팀명" in club_filtered_df.columns else pd.DataFrame()
                team_out_df = club_filtered_df[club_filtered_df["원소속팀명"].astype(str).str.strip() == sel_team_name].copy() if "원소속팀명" in club_filtered_df.columns else pd.DataFrame()

                total_in_spent = team_in_df["실제이적료(만€)"].astype(float).sum() if not team_in_df.empty and "실제이적료(만€)" in team_in_df.columns else 0.0
                total_out_income = team_out_df["실제이적료(만€)"].astype(float).sum() if not team_out_df.empty and "실제이적료(만€)" in team_out_df.columns else 0.0
                net_spend = total_in_spent - total_out_income

                def get_adjusted_deal_score(row, is_buy_side):
                    recorded_score = float(row.get("이적평점", 7.50))
                    orig_trade_type = str(row.get("거래구분", "IN")).strip()
                    if is_buy_side and "OUT" in orig_trade_type:
                        return round(max(1.0, min(10.0, 15.00 - recorded_score)), 2)
                    elif not is_buy_side and "IN" in orig_trade_type:
                        return round(max(1.0, min(10.0, 15.00 - recorded_score)), 2)
                    return recorded_score

                if not team_in_df.empty and "이적평점" in team_in_df.columns:
                    team_in_df["이적평점"] = team_in_df.apply(lambda r: get_adjusted_deal_score(r, is_buy_side=True), axis=1)
                if not team_out_df.empty and "이적평점" in team_out_df.columns:
                    team_out_df["이적평점"] = team_out_df.apply(lambda r: get_adjusted_deal_score(r, is_buy_side=False), axis=1)

                all_team_trades = pd.concat([team_in_df, team_out_df])
                if not all_team_trades.empty and "이적평점" in all_team_trades.columns:
                    fees = all_team_trades["실제이적료(만€)"].astype(float)
                    scores = all_team_trades["이적평점"].astype(float)
                    if fees.sum() > 0:
                        weights = fees.apply(lambda x: max(x, 500.0))
                        weighted_avg_score = (scores * weights).sum() / weights.sum()
                    else:
                        weighted_avg_score = scores.mean()
                else:
                    weighted_avg_score = 7.50

                if weighted_avg_score >= 8.5: club_grade = "💎 S등급 (이적시장 대성공)"
                elif weighted_avg_score >= 7.5: club_grade = "🌟 A등급 (매우 훌륭한 이적시장)"
                elif weighted_avg_score >= 6.8: club_grade = "⚖️ B등급 (준수한 실리 운영)"
                elif weighted_avg_score >= 6.0: club_grade = "⚠️ C등급 (다소 아쉬운 이적시장)"
                else: club_grade = "🚨 D등급 (패닉 / 재정 낭비)"

                st.markdown(f"### 🛡️ **'{sel_team_name}'** 이적시장 종합 성적표 ({sel_season_club})")
                
                t_m1, t_m2, t_m3, t_m4 = st.columns(4)
                t_m1.metric("총 영입 지출액 (IN)", f"€{total_in_spent:,.0f}만", f"{len(team_in_df)}명 영입")
                t_m2.metric("총 방출 수익 (OUT)", f"€{total_out_income:,.0f}만", f"{len(team_out_df)}명 방출")
                t_m3.metric("순지출 (Net Spend)", f"€{net_spend:+,.0f}만", delta=f"{format_currency_desc(abs(net_spend)).split(' | ')[0]} {'지출' if net_spend >= 0 else '수익'}", delta_color="inverse")
                t_m4.metric("이적시장 가중 평점", f"★ {weighted_avg_score:.2f} / 10.00", club_grade.split(" ")[0])
                st.caption(f"🏆 최종 구단 이적시장 종합 판정: **{club_grade}**")

                st.markdown("<br>", unsafe_allow_html=True)
                
                sub_tab1, sub_tab2 = st.tabs([f"🔵 영입 명단 ({len(team_in_df)}명)", f"🔴 방출 명단 ({len(team_out_df)}명)"])
                
                with sub_tab1:
                    if team_in_df.empty:
                        st.info("영입(IN) 데이터가 없습니다.")
                    else:
                        st.dataframe(team_in_df, use_container_width=True)
                
                with sub_tab2:
                    if team_out_df.empty:
                        st.info("방출(OUT) 데이터가 없습니다.")
                    else:
                        st.dataframe(team_out_df, use_container_width=True)

        elif "리그별" in rank_mode:
            st.markdown("#### 🌍 **리그별 & 10대 리그 전체 통합 파워 랭킹 (Power Rankings)**")
            
            c_rk1, c_rk2 = st.columns(2)
            all_seasons_rk = list(history_df["이적시즌"].dropna().unique()) if "이적시즌" in history_df.columns else []
            with c_rk1:
                sel_season_rk = st.selectbox("조회할 이적 시즌", ["전체 시즌"] + all_seasons_rk, index=0, key="rk_season_sel")

            league_filtered_df = history_df if sel_season_rk == "전체 시즌" else history_df[history_df["이적시즌"] == sel_season_rk]

            if "이적팀리그" in league_filtered_df.columns:
                auto_detected_leagues = [str(l).strip() for l in league_filtered_df["이적팀리그"].dropna().unique() if str(l).strip() not in ["", "nan"]]
            else:
                auto_detected_leagues = []

            if not auto_detected_leagues:
                st.warning("⚠️ 아직 시트에 '이적팀리그'가 기록된 데이터가 없습니다. 1번 탭에서 이적팀 리그를 선택하고 새로 저장해 보세요.")
            else:
                league_options = ["🌐 [전체 10개 리그 통합 순위표 (All Leagues)]"] + sorted(auto_detected_leagues)
                with c_rk2:
                    sel_league_name = st.selectbox("조회할 리그 범위 선택 (자동 생성 필터)", league_options, key="rk_league_sel")

                is_all_leagues = "전체 10개 리그" in sel_league_name
                l_target_df = league_filtered_df if is_all_leagues else league_filtered_df[league_filtered_df["이적팀리그"] == sel_league_name]

                if not l_target_df.empty and "이적팀명" in l_target_df.columns:
                    unique_teams = sorted(list(l_target_df["이적팀명"].astype(str).str.strip().unique()))
                    team_stat_rows = []

                    for t_name in unique_teams:
                        in_trades = l_target_df[l_target_df["이적팀명"].astype(str).str.strip() == t_name].copy()
                        out_trades = league_filtered_df[league_filtered_df["원소속팀명"].astype(str).str.strip() == t_name].copy() if "원소속팀명" in league_filtered_df.columns else pd.DataFrame()

                        in_spent = in_trades["실제이적료(만€)"].astype(float).sum() if not in_trades.empty and "실제이적료(만€)" in in_trades.columns else 0.0
                        out_income = out_trades["실제이적료(만€)"].astype(float).sum() if not out_trades.empty and "실제이적료(만€)" in out_trades.columns else 0.0
                        net_val = in_spent - out_income

                        team_stat_rows.append({
                            "이적팀명": t_name,
                            "영입(IN)": len(in_trades),
                            "방출(OUT)": len(out_trades),
                            "총영입액(만€)": int(in_spent),
                            "총방출액(만€)": int(out_income),
                            "순지출(만€)": int(net_val)
                        })

                    ranked_df = pd.DataFrame(team_stat_rows).sort_values(by="총영입액(만€)", ascending=False).reset_index(drop=True)
                    ranked_df.index = ranked_df.index + 1
                    ranked_df.index.name = "순위 (Rank)"

                    title_prefix = "유럽 전체 10개 리그 통합" if is_all_leagues else sel_league_name
                    st.markdown(f"### 🏆 **{title_prefix}** 구단 이적시장 파워 랭킹 ({sel_season_rk})")
                    st.dataframe(ranked_df, use_container_width=True)

        else:
            st.markdown("#### 🛠️ **구글 시트 저장 데이터 조회 및 삭제 관리 (Data Management)**")
            st.caption("테스트로 잘못 저장했거나 중복 저장된 선수 데이터를 선택하여 구글 시트에서 즉시 안전하게 삭제합니다.")
            
            del_c1, del_c2 = st.columns(2)
            del_seasons = list(history_df["이적시즌"].dropna().unique()) if "이적시즌" in history_df.columns else []
            with del_c1:
                sel_del_season = st.selectbox("삭제 대상 이적 시즌 선택", del_seasons, key="del_season_sel")

            del_season_df = history_df[history_df["이적시즌"] == sel_del_season] if "이적시즌" in history_df.columns else pd.DataFrame()
            del_players = list(del_season_df["선수명"].dropna().unique()) if "선수명" in del_season_df.columns else []

            with del_c2:
                sel_del_player = st.selectbox("삭제할 선수 선택", del_players, key="del_player_sel") if del_players else None

            if sel_del_player:
                target_del_row = del_season_df[del_season_df["선수명"] == sel_del_player].iloc[-1]
                st.warning(f"⚠️ 삭제 대상: **'{sel_del_player}'** (시즌: `{sel_del_season}`)")
                
                if st.button(f"🗑️ '{sel_del_player}' 데이터 구글 시트에서 영구 삭제하기", type="primary", use_container_width=True, key="del_exec_btn"):
                    with st.spinner("구글 시트에서 데이터를 삭제 중입니다..."):
                        del_payload = {
                            "action": "delete_row",
                            "season": sel_del_season,
                            "name": sel_del_player
                        }
                        try:
                            res = requests.post(
                                GOOGLE_SHEET_WEBAPP_URL, 
                                data=json.dumps(del_payload), 
                                headers={"Content-Type": "text/plain;charset=utf-8"}, 
                                timeout=30, 
                                allow_redirects=True
                            )
                            res_json = res.json()
                            if res_json.get("status") == "success":
                                st.success(f"✅ '{sel_del_player}' 선수의 데이터가 성공적으로 삭제되었습니다!")
                                st.cache_data.clear()
                                st.rerun()
                            else:
                                st.error("⚠️ 삭제 실패: 일치하는 데이터를 찾지 못했습니다.")
                        except Exception as e:
                            st.error(f"⚠️ 통신 오류: {e}")

            st.markdown("---")
            st.markdown("##### 📋 **전체 메인 시트 저장 데이터 목록**")
            st.dataframe(history_df, use_container_width=True)
