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

# 🌟 구글 시트 CSV Export 다이렉트 로드 (캐시 0초로 즉시 반영)
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

    default_form_template = {
        "name": "", "nat": "", "age": 28, "from_team": "", "to_team": "",
        "tm": 4500, "fee": 5960, "wage": 0.0, "notes": "", "season": "26/27 여름 (Summer)",
        "pos": list(POSITION_WEIGHTS.keys())[4],
        "from_league": list(LEAGUE_WEIGHTS.keys())[0],
        "to_league": list(LEAGUE_WEIGHTS.keys())[0],
        "buying_tier": list(CLUB_TIERS.keys())[1],
        "contract": list(CONTRACT_WEIGHTS.keys())[2],
        "transfer_type": list(TRANSFER_TYPE_WEIGHTS.keys())[0],
        "trade_type": "🔵 영입 (IN)",
        "reg_status": list(REGISTRATION_WEIGHTS.keys())[1],
        "big_stage": list(BIG_STAGE_WEIGHTS.keys())[0],
        "injury": list(INJURY_WEIGHTS.keys())[1],
        "urgency": list(URGENCY_WEIGHTS.keys())[0],
        "option_exercised": False
    }

    if "current_form" not in st.session_state:
        st.session_state["current_form"] = default_form_template.copy()
    else:
        for k_def, v_def in default_form_template.items():
            if k_def not in st.session_state["current_form"]:
                st.session_state["current_form"][k_def] = v_def

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

                        # 🌟 [완벽 동기화] 1번 탭 데이터 세팅
                        p_name = get_exact_val(row_raw, "선수명", "")
                        p_nat = get_exact_val(row_raw, "국적", "")
                        p_age = int(get_exact_val(row_raw, "만나이", 28))
                        p_pos_str = get_exact_val(row_raw, "포지션", "")
                        p_from_league = get_exact_val(row_raw, "원소속리그", "")
                        p_tier = get_exact_val(row_raw, "영입구단티어", "")
                        p_ttype = get_exact_val(row_raw, "이적형태", "")
                        p_tm = int(get_exact_val(row_raw, "TM시장가치(만€)", 4500))
                        p_fee = int(get_exact_val(row_raw, "실제이적료(만€)", 0))
                        p_to_league_name = get_exact_val(row_raw, "이적팀리그", "")
                        p_notes = get_exact_val(row_raw, "스카우팅메모", "")
                        p_from_team = get_exact_val(row_raw, "원소속팀명", "")
                        p_to_team = get_exact_val(row_raw, "이적팀명", "")
                        p_trade_type = get_exact_val(row_raw, "거래구분", "IN")
                        p_wage = float(get_exact_val(row_raw, "주급(만€)", 0.0))

                        pos_match = list(POSITION_WEIGHTS.keys())[4]
                        for p_k in POSITION_WEIGHTS.keys():
                            if p_pos_str and p_pos_str in p_k:
                                pos_match = p_k
                                break

                        from_l_match = list(LEAGUE_WEIGHTS.keys())[0]
                        for l_k in LEAGUE_WEIGHTS.keys():
                            if p_from_league and p_from_league in l_k:
                                from_l_match = l_k
                                break

                        to_l_match = list(LEAGUE_WEIGHTS.keys())[0]
                        for l_k in LEAGUE_WEIGHTS.keys():
                            if p_to_league_name and p_to_league_name in l_k:
                                to_l_match = l_k
                                break

                        tier_match = list(CLUB_TIERS.keys())[1]
                        for t_k in CLUB_TIERS.keys():
                            if p_tier and p_tier in t_k:
                                tier_match = t_k
                                break

                        ttype_match = list(TRANSFER_TYPE_WEIGHTS.keys())[0]
                        for tt_k in TRANSFER_TYPE_WEIGHTS.keys():
                            if p_ttype and p_ttype in tt_k:
                                ttype_match = tt_k
                                break

                        clean_notes_val = p_notes.split(" | [영입")[0].split(" | [방출")[0].strip()

                        st.session_state["current_form"] = {
                            "name": p_name,
                            "nat": p_nat,
                            "age": p_age,
                            "from_team": p_from_team,
                            "to_team": p_to_team,
                            "tm": p_tm,
                            "fee": p_fee,
                            "wage": p_wage,
                            "notes": clean_notes_val,
                            "season": sel_e_season,
                            "pos": pos_match,
                            "from_league": from_l_match,
                            "to_league": to_l_match,
                            "buying_tier": tier_match,
                            "contract": list(CONTRACT_WEIGHTS.keys())[2],
                            "transfer_type": ttype_match,
                            "trade_type": "🔴 방출 / 판매 (OUT)" if "OUT" in p_trade_type else "🔵 영입 (IN)",
                            "reg_status": list(REGISTRATION_WEIGHTS.keys())[1],
                            "big_stage": list(BIG_STAGE_WEIGHTS.keys())[0],
                            "injury": list(INJURY_WEIGHTS.keys())[1],
                            "urgency": list(URGENCY_WEIGHTS.keys())[0],
                            "option_exercised": "임대후옵션발동완료" in p_notes
                        }

                        # 🌟 [완벽 동기화] 2번 탭 및 전체 스탯 세션 스테이트에 일대일 강제 복원
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

                        saved_proj_mins = int(get_exact_val(row_raw, "예측_출전시간", 3000))
                        st.session_state["custom_proj_mins"] = saved_proj_mins

                        # 위젯 강제 리프레시 키 번호 상승
                        st.session_state["form_key_id"] += 1
                        st.session_state["stat_key_id"] += 1
                        st.rerun()
    else:
        st.session_state["edit_row_index"] = None

    k_id = st.session_state["form_key_id"]
    s_id = st.session_state["stat_key_id"]
    cf = st.session_state["current_form"]

    st.markdown("---")
    trade_type_choice = st.radio("거래 유형 구분", ["🔵 영입 (IN)", "🔴 방출 / 판매 (OUT)"], index=0 if cf.get("trade_type", "🔵 영입 (IN)") == "🔵 영입 (IN)" else 1, horizontal=True, key=f"trade_type_{k_id}")
    is_out_trade = "방출" in trade_type_choice
    
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader(f"📝 {'[수정 모드] ' if edit_toggle else ''}{'방출(OUT)' if is_out_trade else '영입(IN)'} 선수 & 계약 정보")
        c_s1, c_s2 = st.columns(2)
        with c_s1: 
            season_val = st.selectbox("이적 시즌 / 시장", ["26/27 여름 (Summer)", "26/27 겨울 (Winter)", "기타"], index=["26/27 여름 (Summer)", "26/27 겨울 (Winter)", "기타"].index(cf.get("season", "26/27 여름 (Summer)")) if cf.get("season", "") in ["26/27 여름 (Summer)", "26/27 겨울 (Winter)", "기타"] else 0, key=f"season_{k_id}")
        with c_s2: 
            transfer_type = st.selectbox("이적 형태 & 계약 조항", list(TRANSFER_TYPE_WEIGHTS.keys()), index=list(TRANSFER_TYPE_WEIGHTS.keys()).index(cf.get("transfer_type", list(TRANSFER_TYPE_WEIGHTS.keys())[0])) if cf.get("transfer_type", "") in TRANSFER_TYPE_WEIGHTS else 0, key=f"ttype_{k_id}")
            
        option_exercised = st.checkbox("📌 임대 후 옵션 발동 (완전 전환 완료된 건)", value=cf.get("option_exercised", False), key=f"opt_exec_{k_id}")
        if option_exercised:
            transfer_type = "일반 완전 이적 (Permanent, 기준)"

        c_n1, c_n2, c_n3 = st.columns([2, 1, 1])
        with c_n1: player_name = st.text_input("선수 이름", value=cf.get("name", ""), placeholder="예: Ezri Konsa", key=f"name_{k_id}")
        with c_n2: player_nat = st.text_input("국적", value=cf.get("nat", ""), placeholder="예: 잉글랜드", key=f"nat_{k_id}")
        with c_n3: player_age = st.number_input("만 나이", min_value=15, max_value=45, value=cf.get("age", 28), key=f"age_{k_id}")

        c_t1, c_t2, c_t3 = st.columns(3)
        with c_t1: in_from_team = st.text_input("원소속팀명 (보내는 팀)", value=cf.get("from_team", ""), placeholder="예: 아스톤 빌라", key=f"from_team_{k_id}")
        with c_t2: in_to_team = st.text_input("이적팀명 (영입 구단)", value=cf.get("to_team", ""), placeholder="예: 아스날", key=f"to_team_{k_id}")
        with c_t3: in_to_league_choice = st.selectbox("이적팀 리그", list(LEAGUE_WEIGHTS.keys()), index=list(LEAGUE_WEIGHTS.keys()).index(cf.get("to_league", list(LEAGUE_WEIGHTS.keys())[0])) if cf.get("to_league", "") in LEAGUE_WEIGHTS else 0, key=f"to_league_choice_{k_id}")
        
        pos_col1, pos_col2 = st.columns(2)
        with pos_col1: main_position = st.selectbox("주 포지션", list(POSITION_WEIGHTS.keys()), index=list(POSITION_WEIGHTS.keys()).index(cf.get("pos", list(POSITION_WEIGHTS.keys())[4])) if cf.get("pos", "") in POSITION_WEIGHTS else 4, key=f"pos_{k_id}")
        with pos_col2: versatility = st.selectbox("멀티 포지션 소화 능력", list(VERSATILITY_WEIGHTS.keys()), index=0, key=f"vers_{k_id}")
            
        c_r1, c_r2 = st.columns(2)
        with c_r1: 
            reg_val = cf.get("reg_status", list(REGISTRATION_WEIGHTS.keys())[1])
            reg_idx = list(REGISTRATION_WEIGHTS.keys()).index(reg_val) if reg_val in REGISTRATION_WEIGHTS else 1
            reg_status = st.selectbox("스쿼드 등록 / HG 쿼터", list(REGISTRATION_WEIGHTS.keys()), index=reg_idx, key=f"reg_{k_id}")
        with c_r2: 
            stage_val = cf.get("big_stage", list(BIG_STAGE_WEIGHTS.keys())[0])
            stage_idx = list(BIG_STAGE_WEIGHTS.keys()).index(stage_val) if stage_val in BIG_STAGE_WEIGHTS else 0
            big_stage = st.selectbox("UCL / 빅매치 검증도", list(BIG_STAGE_WEIGHTS.keys()), index=stage_idx, key=f"stage_{k_id}")
        
        c_i1, c_i2 = st.columns(2)
        with c_i1: 
            inj_val = cf.get("injury", list(INJURY_WEIGHTS.keys())[1])
            inj_idx = list(INJURY_WEIGHTS.keys()).index(inj_val) if inj_val in INJURY_WEIGHTS else 1
            injury_status = st.selectbox("부상 내구성 & 메디컬 리스크", list(INJURY_WEIGHTS.keys()), index=inj_idx, key=f"inj_{k_id}")
        with c_i2: 
            urg_val = cf.get("urgency", list(URGENCY_WEIGHTS.keys())[0])
            urg_idx = list(URGENCY_WEIGHTS.keys()).index(urg_val) if urg_val in URGENCY_WEIGHTS else 0
            urgency_status = st.selectbox("영입 구단 절박성 & 취약 포지션", list(URGENCY_WEIGHTS.keys()), index=urg_idx, key=f"urg_{k_id}")

        selling_league = st.selectbox("보내는 리그 (원소속 리그)", list(LEAGUE_WEIGHTS.keys()), index=list(LEAGUE_WEIGHTS.keys()).index(cf.get("from_league", list(LEAGUE_WEIGHTS.keys())[0])) if cf.get("from_league", "") in LEAGUE_WEIGHTS else 0, key=f"league_{k_id}")
        buying_club_tier = st.selectbox("영입구단티어", list(CLUB_TIERS.keys()), index=list(CLUB_TIERS.keys()).index(cf.get("buying_tier", list(CLUB_TIERS.keys())[1])) if cf.get("buying_tier", "") in CLUB_TIERS else 1, key=f"tier_{k_id}")
        remaining_contract = st.selectbox("이적 당시 잔여 계약 기간", list(CONTRACT_WEIGHTS.keys()), index=list(CONTRACT_WEIGHTS.keys()).index(cf.get("contract", list(CONTRACT_WEIGHTS.keys())[2])) if cf.get("contract", "") in CONTRACT_WEIGHTS else 2, key=f"contract_{k_id}")
        
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

        tm_market_value = st.number_input("TM시장가치(만€)", min_value=0, value=cf.get("tm", 4500), step=50, key=f"tm_{k_id}")
        
        is_loan_type = "임대" in transfer_type and "의무" not in transfer_type and not option_exercised
        is_undisclosed = "비공개" in transfer_type
        is_fa = "FA" in transfer_type
        
        fee_label = "실제 수령/지출 임대료 (만 유로, €)" if is_loan_type else ("실제 방출(판매) 이적료 (만 유로, €)" if is_out_trade else "실제이적료(만€)")
        
        actual_transfer_fee = st.number_input(
            fee_label, 
            min_value=0, 
            value=0 if is_undisclosed else cf.get("fee", 0), 
            step=50, 
            key=f"fee_{k_id}",
            disabled=is_undisclosed
        )

        weekly_wage_in = st.number_input("주급(만€)", min_value=0.0, value=float(cf.get("wage", 0.0)), step=0.5, key=f"wage_{k_id}")
        player_notes = st.text_area("스카우팅메모", value=cf.get("notes", ""), placeholder="예: 대인 방어 및 후방 빌드업 우수", key=f"note_{k_id}")

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
        overpay_pct = ((weekly_wage_in - expected_fair_weekly_wage) / expected_fair_weekly_wage) * 100 if weekly_wage_in > 0 else 0.0
        diff = (weekly_wage_in - expected_fair_weekly_wage) * 52 if weekly_wage_in > 0 else 0.0
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

    market_min = base_calc_val * (1.15 if is_winter else 1.05)
    market_max = base_calc_val * (1.20 if is_winter else 1.10)
    market_mid = (market_min + market_max) / 2.0
    ext_diff = calc_actual_fee - market_mid
    ext_overpay_pct = (ext_diff / market_mid) * 100 if market_mid > 0 else 0.0

    if tm_market_value > 0:
        base_deal_score = 7.50
        score_multiplier = 1.0 if is_out_trade else -1.0
        val_score_delta = 0.0 if is_undisclosed else max(-3.5, min(2.5, score_multiplier * (overpay_pct / 20.0)))
        rating_delta = max(-0.8, min(1.0, (cur_rating - 7.00) * 1.5))
        age_delta = max(-1.0, min(0.8, (age_w - 1.00) * 8.0))
        risk_delta = (stage_w - 1.00) * 5.0 + (inj_w - 1.00) * 5.0 + (reg_w - 1.00) * 3.0 + (urg_w - 1.00) * 2.0
        
        final_deal_score = round(max(1.00, min(10.00, base_deal_score + val_score_delta + rating_delta + age_delta + risk_delta)), 2)
        ext_deal_score = final_deal_score
    else:
        final_deal_score = 0.00
        ext_deal_score = 0.00

    def get_grade_info(score):
        if score >= 9.00: return "💎 S등급 (Masterclass Deal)"
        elif score >= 8.00: return "🌟 A등급 (Excellent Deal)"
        elif score >= 7.00: return "⚖️ B등급 (Solid / Fair Deal)"
        elif score >= 6.00: return "⚠️ C등급 (Risky Deal)"
        else: return "🚨 D등급 (Panic / Bad Deal)"

    deal_grade = get_grade_info(final_deal_score)
    ext_deal_grade = deal_grade

    with col2:
        st.subheader("📊 분석 결과 및 세부 지표")
        display_name = player_name if player_name else "선수명 미입력"
        display_nat = f"({player_nat})" if player_nat else ""
        pos_short = main_position.split(" (")[0]
        
        st.markdown(f"### **{display_name}** {display_nat} - `{pos_short}`")
        
        res_c1, res_c2, res_c3, res_c4 = st.columns(4)
        with res_c1: st.metric("산출 적정가", f"€{fair_value:,.1f}만")
        with res_c2: st.metric("실제 거래액", f"€{calc_actual_fee:,.1f}만" if not is_undisclosed else "비공개")
        with res_c3: st.metric("평가율", f"{overpay_pct:+.1f}%")
        with res_c4: st.metric("이적 평점", f"★ {final_deal_score:.2f}")

    st.markdown("---")
    display_pname_t1 = player_name.strip() if player_name.strip() else "선수명 미입력"
    action_type = "update" if edit_toggle else "save_all"
    btn_label_t1 = f"🔄 '{display_pname_t1}' 수정된 데이터 구글 시트에 업데이트" if edit_toggle else f"💾 구글 시트에 바로 저장하기"

    if st.button(btn_label_t1, type="primary", use_container_width=True, key="save_btn_tab1"):
        if not player_name.strip():
            st.warning("⚠️ 선수 이름을 먼저 입력해 주세요.")
        else:
            with st.spinner("구글 시트에 데이터를 전송 중입니다..."):
                detailed_notes = f"[{'방출' if is_out_trade else '영입'}] {player_notes}"
                f_target_mins_t1 = st.session_state.get("custom_proj_mins", 3000)

                payload = {
                    "action": action_type,
                    "row_index": st.session_state.get("edit_row_index"),
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "season": season_val,
                    "name": player_name,
                    "nat": player_nat if player_nat.strip() else "미상",
                    "age": int(player_age),
                    "pos": pos_short,
                    "from_league": selling_league.split(" (")[0],
                    "buying_tier": buying_club_tier.split(":")[0],
                    "transfer_type": transfer_type.split(" (")[0],
                    "tm_val": float(tm_market_value),
                    "fee": float(calc_actual_fee),
                    "fair_val": round(fair_value, 1),
                    "diff": round(diff, 1),
                    "status": status_label,
                    "deal_score": float(final_deal_score),
                    "prev_matches": int(st.session_state["f_matches"]),
                    "prev_starts": int(st.session_state["f_starts"]),
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
                    "proj_goals": 0.0, "proj_xg": 0.0, "proj_assists": 0.0, "proj_xa": 0.0, "proj_shots": 0.0, "proj_rating": 7.0,
                    "notes": detailed_notes,
                    "from_team": in_from_team.strip(),
                    "to_team": in_to_team.strip(),
                    "to_league_name": in_to_league_choice.split(" (")[0],
                    "trade_type": "OUT" if is_out_trade else "IN",
                    "weekly_wage": float(weekly_wage_in),
                    "gk_saves": int(st.session_state.get("f_gk_saves", 0)),
                    "gk_conceded": int(st.session_state.get("f_gk_conceded", 0)),
                    "gk_prevented": float(st.session_state.get("f_gk_prevented", 0.0)),
                    "gk_cs": int(st.session_state.get("f_gk_cs", 0)),
                    "gk_errors": int(st.session_state.get("f_gk_errors", 0)),
                    "gk_claims": int(st.session_state.get("f_gk_claims", 0))
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
                        st.session_state["last_saved_msg"] = f"✅ '{player_name}' 선수의 데이터가 성공적으로 저장되었습니다!"
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error(f"⚠️ 저장 실패: {res_json.get('message', '통신 오류')}")
                except Exception as e:
                    st.error(f"⚠️ 저장 오류: {e}")

# ================= TAB 2: FotMob 시즌 성적 & 이적 예측 =================
with tab2:
    st.subheader("📱 FotMob 스타일 시즌 스탯 입력 & 이적 첫 시즌 성적 프로젝션")
    
    f_c1, f_c2, f_c3 = st.columns(3)
    with f_c1: f_pos = st.selectbox("선수 포지션 분류", ["⚽ 필드 플레이어", "🧤 골키퍼"], index=1 if "GK" in main_position else 0, key=f"f_tab_pos_{k_id}_{s_id}")
    with f_c2: f_from_l = st.selectbox("원소속 리그", list(LEAGUE_WEIGHTS.keys()), index=list(LEAGUE_WEIGHTS.keys()).index(selling_league) if selling_league in LEAGUE_WEIGHTS else 0, key=f"f_tab_from_l_{k_id}_{s_id}")
    with f_c3: f_to_l = st.selectbox("이적할 리그", list(LEAGUE_WEIGHTS.keys()), index=list(LEAGUE_WEIGHTS.keys()).index(in_to_league_choice) if in_to_league_choice in LEAGUE_WEIGHTS else 0, key=f"f_tab_to_l_{k_id}_{s_id}")
    
    f_target_mins = st.number_input("예상 출전 시간(분)", min_value=0, max_value=4500, value=int(st.session_state["custom_proj_mins"]), step=90, key=f"f_tab_target_mins_{k_id}_{s_id}")
    st.session_state["custom_proj_mins"] = f_target_mins

    st.divider()
    st.markdown("### 📥 FotMob 시즌 실제 기록 입력")

    b1, b2, b3, b4 = st.columns(4)
    with b1: in_matches = st.number_input("출전 경기", 0, 60, value=int(st.session_state["f_matches"]), key=f"in_matches_box_{k_id}_{s_id}")
    with b2: in_starts = st.number_input("선발 출전", 0, 60, value=int(st.session_state["f_starts"]), key=f"in_starts_box_{k_id}_{s_id}")
    with b3: in_mins = st.number_input("출전 시간", 0, 4500, value=int(st.session_state["f_mins"]), key=f"in_mins_box_{k_id}_{s_id}")
    with b4: in_rating = st.number_input("FotMob 평점", 0.0, 10.0, value=float(st.session_state["f_rating"]), step=0.01, key=f"in_rating_box_{k_id}_{s_id}")

    st.session_state["f_mins"] = in_mins
    st.session_state["f_rating"] = in_rating
    st.session_state["f_matches"] = in_matches
    st.session_state["f_starts"] = in_starts

    if "골키퍼" not in f_pos:
        s1, s2, s3, s4, s5 = st.columns(5)
        with s1: in_goals = st.number_input("득점", 0, 50, value=int(st.session_state["f_goals"]), key=f"in_goals_box_{k_id}_{s_id}")
        with s2: in_xg = st.number_input("기대득점(xG)", 0.0, 50.0, value=float(st.session_state["f_xg"]), step=0.01, key=f"in_xg_box_{k_id}_{s_id}")
        with s3: in_shots = st.number_input("총 슈팅", 0, 200, value=int(st.session_state["f_shots"]), key=f"in_shots_box_{k_id}_{s_id}")
        with s4: in_sot = st.number_input("유효 슈팅", 0, 100, value=int(st.session_state["f_sot"]), key=f"in_sot_box_{k_id}_{s_id}")
        with s5: in_pk_goals = st.number_input("PK 득점", 0, 20, value=int(st.session_state["f_pk_goals"]), key=f"in_pk_box_{k_id}_{s_id}")

        st.session_state["f_goals"] = in_goals
        st.session_state["f_xg"] = in_xg
        st.session_state["f_shots"] = in_shots
        st.session_state["f_sot"] = in_sot
        st.session_state["f_pk_goals"] = in_pk_goals

        p1, p2, p3, p4, p5 = st.columns(5)
        with p1: in_assists = st.number_input("도움", 0, 50, value=int(st.session_state["f_assists"]), key=f"in_assists_box_{k_id}_{s_id}")
        with p2: in_xa = st.number_input("기대도움(xA)", 0.0, 50.0, value=float(st.session_state["f_xa"]), step=0.01, key=f"in_xa_box_{k_id}_{s_id}")
        with p3: in_chances = st.number_input("기회 창출", 0, 150, value=int(st.session_state["f_chances"]), key=f"in_chances_box_{k_id}_{s_id}")
        with p4: in_big_chances = st.number_input("빅찬스메이킹", 0, 50, value=int(st.session_state["f_big_chances"]), key=f"in_bc_box_{k_id}_{s_id}")
        with p5: in_pass_pct = st.number_input("패스 성공률(%)", 0.0, 100.0, value=float(st.session_state["f_pass_pct"]), step=0.1, key=f"in_pass_box_{k_id}_{s_id}")

        st.session_state["f_assists"] = in_assists
        st.session_state["f_xa"] = in_xa
        st.session_state["f_chances"] = in_chances
        st.session_state["f_big_chances"] = in_big_chances
        st.session_state["f_pass_pct"] = in_pass_pct

        d1, d2, d3, d4, d5 = st.columns(5)
        with d1: in_dribbles = st.number_input("성공 드리블", 0, 100, value=int(st.session_state["f_dribbles"]), key=f"in_dribbles_box_{k_id}_{s_id}")
        with d2: in_touches_box = st.number_input("박스 안 터치", 0, 300, value=int(st.session_state["f_touches_box"]), key=f"in_touches_box_{k_id}_{s_id}")
        with d3: in_duels_pct = st.number_input("지상경합승률(%)", 0.0, 100.0, value=float(st.session_state["f_duels_pct"]), step=0.1, key=f"in_duels_box_{k_id}_{s_id}")
        with d4: in_aerial_pct = st.number_input("공중볼승률(%)", 0.0, 100.0, value=float(st.session_state["f_aerial_pct"]), step=0.1, key=f"in_aerial_box_{k_id}_{s_id}")
        with d5: in_tackles = st.number_input("태클 성공", 0, 150, value=int(st.session_state["f_tackles"]), key=f"in_tackles_box_{k_id}_{s_id}")

        st.session_state["f_dribbles"] = in_dribbles
        st.session_state["f_touches_box"] = in_touches_box
        st.session_state["f_tackles"] = in_tackles
        st.session_state["f_duels_pct"] = in_duels_pct
        st.session_state["f_aerial_pct"] = in_aerial_pct
    else:
        gk1, gk2, gk3 = st.columns(3)
        with gk1: in_gk_saves = st.number_input("선방", 0, 250, value=int(st.session_state["f_gk_saves"]), key=f"in_gk_saves_{k_id}_{s_id}")
        with gk2: in_gk_conceded = st.number_input("실점", 0, 120, value=int(st.session_state["f_gk_conceded"]), key=f"in_gk_con__{k_id}_{s_id}")
        with gk3: in_gk_prevented = st.number_input("득점차단", -20.0, 30.0, value=float(st.session_state["f_gk_prevented"]), key=f"in_gk_prev_{k_id}_{s_id}")
        st.session_state["f_gk_saves"] = in_gk_saves
        st.session_state["f_gk_conceded"] = in_gk_conceded
        st.session_state["f_gk_prevented"] = in_gk_prevented

# ================= TAB 3: 과거 유사 이적 사례 비교 =================
with tab3:
    st.subheader("🔍 과거 유사 이적 사례 검색 및 벤치마크 비교")
    if history_df.empty or "선수명" not in history_df.columns:
        st.info("💡 구글 시트에 누적된 과거 데이터가 없습니다. 선수를 저장해 보세요.")
    else:
        st.dataframe(history_df, use_container_width=True)

# ================= TAB 4: 검증 데이터 =================
with tab4:
    st.subheader("🎯 이적 첫 시즌 실제 성적 입력 & 모델 검증")
    val_df = fetch_validation_data()
    if val_df.empty:
        st.info("💡 검증 데이터가 없습니다.")
    else:
        st.dataframe(val_df, use_container_width=True)

# ================= TAB 5: 벤치마크 =================
with tab5:
    st.subheader("👥 신규 이적생 vs 과거 유사 선수 다각도 벤치마크")
    if history_df.empty:
        st.info("💡 과거 데이터가 2명 이상 쌓이면 활성화됩니다.")

# ================= TAB 6: 종합 결산 & 데이터룸 =================
with tab6:
    st.subheader("🏆 이적시장 구단별 종합 성적표 & 데이터룸")
    if history_df.empty:
        st.info("💡 저장된 데이터가 없습니다.")
    else:
        st.dataframe(history_df, use_container_width=True)
