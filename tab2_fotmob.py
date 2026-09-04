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
    "📱 FotMob 스타일 시즌 성적 및 이적 예측룸 (13대 풀 스탯)",
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
            
        option_exercised = st.checkbox("📌 임대 후 옵션 발동 (완전 전환 완료된 건)", value=False, key=f"opt_exec_{k_id}")
        if option_exercised:
            transfer_type = "일반 완전 이적 (Permanent, 기준)"

        c_n1, c_n2, c_n3 = st.columns([2, 1, 1])
        with c_n1: player_name = st.text_input("선수 이름", placeholder="예: Ezri Konsa", key=f"name_{k_id}")
        with c_n2: player_nat = st.text_input("국적", placeholder="예: 잉글랜드", key=f"nat_{k_id}")
        with c_n3: player_age = st.number_input("만 나이", min_value=15, max_value=45, value=28, key=f"age_{k_id}")

        c_t1, c_t2, c_t3 = st.columns(3)
        with c_t1: in_from_team = st.text_input("원소속팀명 (보내는 팀)", placeholder="예: 아스톤 빌라", key=f"from_team_{k_id}")
        with c_t2: in_to_team = st.text_input("이적팀명 (영입 구단)", placeholder="예: 아스날", key=f"to_team_{k_id}")
        with c_t3: in_to_league_choice = st.selectbox("이적팀 리그", list(LEAGUE_WEIGHTS.keys()), index=0, key=f"to_league_choice_{k_id}")
        
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
        elif cur_rating >= 7.15 or cur_p90_exp >= 0.50:
            opta_w = 1.01
        elif cur_rating >= 6.80 or cur_p90_exp >= 0.25:
            opta_w = 1.00
        else:
            opta_w = 0.98

        tm_market_value = st.number_input("TM시장가치(만€)", min_value=0, value=4500, step=50, key=f"tm_{k_id}")
        
        is_loan_type = "임대" in transfer_type and "의무" not in transfer_type and not option_exercised
        is_undisclosed = "비공개" in transfer_type
        is_fa = "FA" in transfer_type
        
        fee_label = "실제 수령/지출 임대료 (Loan Fee, 만 유로, €)" if is_loan_type else ("실제 방출(판매) 이적료 (만 유로, €)" if is_out_trade else "실제이적료(만€)")
        
        actual_transfer_fee = st.number_input(
            fee_label, 
            min_value=0, 
            value=0, 
            step=50, 
            key=f"fee_{k_id}",
            disabled=is_undisclosed
        )

        weekly_wage_in = st.number_input("주급(만€)", min_value=0.0, value=0.0, step=0.5, key=f"wage_{k_id}")
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
    
    if is_fa:
        overpay_pct = 0.0
    elif is_loan_type:
        overpay_pct = 0.0
    else:
        diff = calc_actual_fee - fair_value
        overpay_pct = (diff / fair_value) * 100 if fair_value > 0 else 0.0

    if is_undisclosed:
        status_label = "⚖️ 비공개 (적정가 추정)"
    elif abs(diff) <= (fair_value * 0.05): 
        status_label = "⚖️ 적정가 (Fair Deal)"
    elif diff > 0: 
        status_label = f"⚠️ 고평가/오버페이 (+{overpay_pct:.1f}%)"
    else: 
        status_label = f"💎 저평가/혜자 ({overpay_pct:.1f}%)"

    if tm_market_value > 0 and (calc_actual_fee > 0 or is_loan_type or is_fa or is_undisclosed):
        final_deal_score = 7.50
        deal_grade = "⚖️ B등급 (Solid / Fair Deal)"
    else:
        final_deal_score = 0.00
        deal_grade = "분석 대기 중"

    with col2:
        st.subheader("📊 분석 결과 및 12대 세부 지표")
        display_name = player_name if player_name else "선수명 미입력"
        pos_short = main_position.split(" (")[0]
        st.markdown(f"### 🔵 **{display_name}** - `{pos_short}`")

# ================= TAB 2: 원본 고유 FotMob 스타일 13대 스탯 입력 탭 (내장형) =================
with tab2:
    st.subheader("📱 FotMob 스타일 시즌 성적 및 이적 예측룸 (13대 풀 스탯)")

    col_s1, col_s2 = st.columns([2, 1])
    with col_s1:
        st.markdown("##### 🔍 비교 및 분석 대상 선수 선택")
        if history_df.empty or "선수명" not in history_df.columns:
            st.info("💡 등록된 선수 히스토리가 없습니다. 아래에서 직접 스탯을 입력하거나 1번 탭에서 평가를 진행하세요.")
            p_list = []
        else:
            p_list = list(history_df["선수명"].dropna().unique())
        
        sel_player = st.selectbox("DB 선수 불러오기 (선택 시 자동 매핑)", ["직접 입력 / 커스텀"] + p_list, key="tab2_player_select")

    # 기본값 설정
    def_mins = 2206; def_goals = 16; def_xg = 17.44; def_assists = 4; def_xa = 3.33
    def_rating = 7.32; def_matches = 28; def_starts = 25; def_shots = 88; def_sot = 43
    def_chances = 25; def_dribbles = 14; def_touches = 153; def_tackles = 24

    if sel_player != "직접 입력 / 커스텀" and not history_df.empty:
        matched_rows = history_df[history_df["선수명"] == sel_player]
        if not matched_rows.empty:
            r = matched_rows.iloc[-1]
            def_mins = int(r.get("이전_출전시간", 2206)) if pd.notnull(r.get("이전_출전시간")) else 2206
            def_goals = int(r.get("이전_골", 16)) if pd.notnull(r.get("이전_골")) else 16
            def_xg = float(r.get("이전_xG", 17.44)) if pd.notnull(r.get("이전_xG")) else 17.44
            def_assists = int(r.get("이전_도움", 4)) if pd.notnull(r.get("이전_도움")) else 4
            def_xa = float(r.get("이전_xA", 3.33)) if pd.notnull(r.get("이전_xA")) else 3.33
            def_rating = float(r.get("이전_FotMob평점", 7.32)) if pd.notnull(r.get("이전_FotMob평점")) else 7.32
            def_matches = int(r.get("이전_출전경기", 28)) if pd.notnull(r.get("이전_출전경기")) else 28
            def_starts = int(r.get("이전_선발", 25)) if pd.notnull(r.get("이전_선발")) else 25
            def_shots = int(r.get("이전_총슈팅", 88)) if pd.notnull(r.get("이전_총슈팅")) else 88
            def_sot = int(r.get("이전_유효슈팅", 43)) if pd.notnull(r.get("이전_유효슈팅")) else 43
            def_chances = int(r.get("이전_찬스메이킹", 25)) if pd.notnull(r.get("이전_찬스메이킹")) else 25
            def_dribbles = int(r.get("이전_성공드리블", 14)) if pd.notnull(r.get("이전_성공드리블")) else 14
            def_touches = int(r.get("이전_박스터치", 153)) if pd.notnull(r.get("이전_박스터치")) else 153
            def_tackles = int(r.get("이전_태클성공", 24)) if pd.notnull(r.get("이전_태클성공")) else 24

    st.markdown("---")
    st.markdown("#### ⚽ 직전 시즌 13대 핵심 스탯 입력룸")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("##### 📌 기본 출전 및 평점 지표")
        f_matches = st.number_input("출전 경기 (Matches)", min_value=0, max_value=60, value=def_matches, key="t2_matches")
        f_starts = st.number_input("선발 출전 (Starts)", min_value=0, max_value=60, value=def_starts, key="t2_starts")
        f_mins = st.number_input("출전 시간 (Minutes)", min_value=0, max_value=5000, value=def_mins, key="t2_mins")
        f_rating = st.number_input("FotMob 평균 평점", min_value=1.0, max_value=10.0, value=def_rating, step=0.01, key="t2_rating")

        st.markdown("##### 1️⃣ 슈팅 및 득점 (Shooting & Goals)")
        f_goals = st.number_input("득점 (Goals)", min_value=0, value=def_goals, key="t2_goals")
        f_xg = st.number_input("기대 득점 (xG)", min_value=0.0, value=def_xg, step=0.1, key="t2_xg")
        f_shots = st.number_input("총 슈팅 (Shots)", min_value=0, value=def_shots, key="t2_shots")
        f_sot = st.number_input("유효 슈팅 (On Target)", min_value=0, value=def_sot, key="t2_sot")
        f_pk_goals = st.number_input("PK 득점 (Penalty)", min_value=0, value=0, key="t2_pk")

    with col2:
        st.markdown("##### 2️⃣ 패스 및 기회 창출 (Passing & Creativity)")
        f_assists = st.number_input("도움 (Assists)", min_value=0, value=def_assists, key="t2_assists")
        f_xa = st.number_input("기대 도움 (xA)", min_value=0.0, value=def_xa, step=0.1, key="t2_xa")
        f_chances = st.number_input("기회 창출 (Chances)", min_value=0, value=def_chances, key="t2_chances")
        f_big_chances = st.number_input("빅 찬스 메이킹", min_value=0, value=0, key="t2_big_chances")
        f_pass_acc = st.number_input("패스 성공률 (%)", min_value=0.0, max_value=100.0, value=85.0, step=0.1, key="t2_pass_acc")

        st.markdown("##### 3️⃣ 경합 및 수비 기여 (Duels & Defending)")
        f_dribbles = st.number_input("성공한 드리블", min_value=0, value=def_dribbles, key="t2_dribbles")
        f_touches_box = st.number_input("박스 안 터치", min_value=0, value=def_touches, key="t2_touches")
        f_ground_duels = st.number_input("지상 경합 승률 (%)", min_value=0.0, max_value=100.0, value=55.0, step=0.1, key="t2_g_duels")
        f_aerial_duels = st.number_input("공중볼 승률 (%)", min_value=0.0, max_value=100.0, value=50.0, step=0.1, key="t2_a_duels")
        f_tackles = st.number_input("태클 성공", min_value=0, value=def_tackles, key="t2_tackles")

    st.markdown("---")
    with st.expander("🥅 골키퍼 전용 상세 지표 (GK Stats)", expanded=False):
        gk1, gk2, gk3, gk4, gk5, gk6 = st.columns(6)
        with gk1: st.number_input("선방 횟수", min_value=0, value=78, key="t2_gk_saves")
        with gk2: st.number_input("실점", min_value=0, value=28, key="t2_gk_conceded")
        with gk3: st.number_input("득점 차단 (Prevented)", value=2.45, step=0.1, key="t2_gk_prevented")
        with gk4: st.number_input("클린시트", min_value=0, value=10, key="t2_gk_cs")
        with gk5: st.number_input("실점 실수", min_value=0, value=0, key="t2_gk_errors")
        with gk6: st.number_input("공중볼 캐칭", min_value=0, value=18, key="t2_gk_claims")

# ================= TAB 3: 과거 유사 이적 사례 비교 =================
with tab3:
    st.subheader("🔍 과거 유사 이적 사례 검색 및 벤치마크 비교 (Comps TOP 5 & 10)")

# ================= TAB 4: 이적 첫 시즌 실제 성적 입력 & 모델 검증 =================
with tab4:
    st.subheader("🎯 이적 첫 시즌 실제 성적 입력 & 모델 예측 정확도 사후 검증")

# ================= TAB 5: 신규 이적생 vs 과거 유사 선수 다각도 벤치마크 =================
with tab5:
    st.subheader("👥 신규 이적생 vs 과거 유사 이적 선수 다각도 벤치마크 (Multi-Comps)")

# ================= TAB 6: 이적시장 구단/리그별 종합 결산 & 데이터룸 =================
with tab6:
    st.subheader("🏆 이적시장 구단별 종합 성적표 & 리그 파워 랭킹 & 데이터룸")
