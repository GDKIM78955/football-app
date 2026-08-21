import streamlit as st
import pandas as pd
import requests
import json
import re
from datetime import datetime

# 1. 페이지 설정
st.set_page_config(
    page_title="축구 이적료 적정가 분석 & DB 관리",
    page_icon="⚽",
    layout="wide"
)

GOOGLE_SHEET_WEBAPP_URL = "https://script.google.com/macros/s/AKfycbxV76sZFJaVPa7tmWSPBGlLaiZHijL77b7MZ_mpr6U-ia6hNO0UEiN-6A_1qz2u7XBNKA/exec"

# 2. 가중치 딕셔너리
LEAGUE_WEIGHTS = {
    "잉글랜드 프리미어리그 (EPL 1부)": 1.00,
    "이탈리아 세리에 A (Serie A 1부)": 0.97,
    "스페인 라리가 (La Liga 1부)": 0.97,
    "독일 분데스리가 (Bundesliga 1부)": 0.97,
    "프랑스 리그 1 (Ligue 1 1부)": 0.97,
    "브라질 세리에 A (Brasileirão 1부)": 0.96,
    "잉글랜드 챔피언십 (EFL 2부)": 0.95,
    "벨기에 주필러 프로 리그 (1부)": 0.94,
    "아르헨티나 프리메라 디비시온 (1부)": 0.94,
    "포르투갈 프리메이라리가 (1부)": 0.94,
    "네덜란드 에레디비시 (Eredivisie 1부)": 0.92,
    "미국 메이저리그사커 (MLS 1부)": 0.92,
    "멕시코 리가 MX (1부)": 0.92,
    "독일 2. 분데스리가 (2부)": 0.92,
    "스페인 라리가 2 (세군다 2부)": 0.91,
    "이탈리아 세리에 B (2부)": 0.90,
    "일본 J1리그 (1부)": 0.90,
    "사우디 프로리그 (SPL 1부)": 0.89,
    "대한민국 K리그1 (1부)": 0.89,
    "튀르키예 쉬페르리그 (1부)": 0.89,
    "스위스 슈퍼리그 (1부)": 0.89,
    "오스트리아 분데스리가 (1부)": 0.89,
    "덴마크 수페르리가 (1부)": 0.88,
    "프랑스 리그 2 (2부)": 0.88,
    "일본 J2리그 (2부)": 0.84,
    "대한민국 K리그2 (2부)": 0.83,
    "기타 리그": 0.77
}

CLUB_TIERS = {
    "Tier 1: 엘리트 메가클럽 (레알, 맨시티, 바이에른 등)": 1.15,
    "Tier 2: 빅클럽 (아스날, 리버풀, 첼시, 바르샤 등)": 1.08,
    "Tier 3: 중상위권 클럽 (토트넘, AT마드리드, 도르트문트 등)": 1.00,
    "Tier 4: 중하위권 클럽 (EPL 중하위, 빅리그 중위권 팀)": 0.92,
    "Tier 5: 소형/셀링 클럽 (중소리그 팀, 2부리그, K/J리그)": 0.80
}

def get_age_weight(age):
    if age <= 19: return 1.00
    elif age <= 23: return 1.12
    elif age <= 27: return 1.00
    elif age <= 29: return 0.90
    elif age <= 31: return 0.75
    else: return 0.55

def parse_money(m_str):
    if not m_str: return 0.0
    s = m_str.replace("€", "").replace("m", "M").replace("k", "K").strip()
    try:
        if "M" in s:
            num = float(re.findall(r"[\d\.]+", s)[0])
            return num * 100 # 만 유로 단위 (€30.00m -> 3000만 유로)
        elif "K" in s:
            num = float(re.findall(r"[\d\.]+", s)[0])
            return num * 0.1 # 만 유로 단위 (€500k -> 50만 유로)
        else:
            nums = re.findall(r"[\d\.]+", s)
            return float(nums[0]) if nums else 0.0
    except:
        return 0.0

# 텍스트 복붙 스마트 파서 함수
def parse_tm_copied_text(raw_text):
    lines = [line.strip() for line in raw_text.split("\n") if line.strip()]
    parsed_data = []
    
    current_club = "소속 구단"
    for line in lines:
        if any(h in line for h in ["Arsenal", "Aston Villa", "Chelsea", "Liverpool", "Manchester City", "Manchester United", "Tottenham", "Newcastle", "Real Madrid", "Barcelona", "Bayern"]):
            if "FC" in line or len(line.split()) <= 3:
                current_club = line.replace("FC", "").strip()

        # 탭이나 공백으로 구분된 행 분석
        parts = re.split(r"\t+|\s{2,}", line)
        if len(parts) >= 4:
            name = parts[0]
            if "In" in name or "Player" in name or "Arrivals" in name:
                continue
            
            age = 24
            mv = 0.0
            fee = 0.0
            left_club = "전소속팀"
            
            for p in parts:
                if p.isdigit() and 15 <= int(p) <= 45:
                    age = int(p)
                elif "€" in p or "m" in p or "k" in p:
                    if mv == 0.0:
                        mv = parse_money(p)
                    else:
                        fee = parse_money(p)
                elif len(p) > 2 and not any(c.isdigit() for c in p) and p != name:
                    left_club = p
            
            if name and (mv > 0 or fee > 0 or age != 24):
                parsed_data.append({
                    "영입팀": current_club,
                    "선수명": name,
                    "나이": age,
                    "전소속": left_club,
                    "TM시장가치(만유로)": mv,
                    "실제이적료(만유로)": fee
                })
    return parsed_data

# 3. Streamlit 화면 UI
st.title("⚽ 축구 이적시장 자동 수집 & 가치 평가 시스템")

tab1, tab2 = st.tabs(["📋 트랜스퍼마르크트 복사-붙여넣기 일괄 분석", "✍️ 단일 선수 수동 분석"])

with tab1:
    st.subheader("📋 트랜스퍼마르크트 이적 표 복사-붙여넣기")
    st.markdown("""
    트랜스퍼마르크트의 [이적 페이지](https://www.transfermarkt.com/premier-league/transfers/wettbewerb/GB1)에서 
    선수 표 영역을 마우스로 쭉 긁어서 복사(`Ctrl+C`)한 뒤 아래 칸에 붙여넣기(`Ctrl+V`) 하세요.
    """)
    
    sample_text = """Riccardo Calafiori\t22\tLeft-Back\t€45.00m\tBologna\t€43.70m
Mikel Merino\t28\tCentral Midfield\t€50.00m\tReal Sociedad\t€32.00m
David Raya\t28\tGoalkeeper\t€35.00m\tBrentford\t€31.90m
Amadou Onana\t22\tDefensive Midfield\t€50.00m\tEverton\t€59.35m
Ian Maatsen\t22\tLeft-Back\t€40.00m\tChelsea\t€44.50m"""
    
    col_input1, col_input2 = st.columns([3, 1])
    with col_input1:
        raw_text_input = st.text_area("트랜스퍼마르크트에서 복사한 텍스트 붙여넣기", value=sample_text, height=180)
    with col_input2:
        batch_tier = st.selectbox("영입 구단 기본 티어", list(CLUB_TIERS.keys()), index=2)
        batch_league = st.selectbox("기본 리그 가중치", list(LEAGUE_WEIGHTS.keys()), index=0)
        
    if st.button("🚀 붙여넣은 선수들 일괄 분석하기", type="primary", use_container_width=True):
        parsed = parse_tm_copied_text(raw_text_input)
        if not parsed:
            st.error("데이터를 파싱하지 못했습니다. 텍스트 형식을 확인해 주세요.")
        else:
            df = pd.DataFrame(parsed)
            df["나이가중치"] = df["나이"].apply(get_age_weight)
            df["구단가중치"] = CLUB_TIERS[batch_tier]
            df["리그가중치"] = LEAGUE_WEIGHTS[batch_league]
            
            # 적정가 = TM몸값 * 리그가중치 * 나이가중치 * 구단가중치
            df["산출적정가(만유로)"] = (df["TM시장가치(만유로)"] * df["리그가중치"] * df["나이가중치"] * df["구단가중치"]).round(1)
            df["차액(만유로)"] = (df["실제이적료(만유로)"] - df["산출적정가(만유로)"]).round(1)
            
            def eval_status(row):
                if row["산출적정가(만유로)"] == 0: return "평가불가"
                diff = row["차액(만유로)"]
                if abs(diff) <= row["산출적정가(만유로)"] * 0.05: return "⚖️ 적정가"
                elif diff > 0: return "⚠️ 고평가"
                else: return "💎 저평가"
                
            df["평가"] = df.apply(eval_status, axis=1)
            st.session_state["parsed_df"] = df
            st.success(f"총 {len(df)}명의 선수 데이터를 성공적으로 변환 및 계산했습니다!")

    if "parsed_df" in st.session_state:
        df_show = st.session_state["parsed_df"]
        st.dataframe(df_show[["선수명", "나이", "전소속", "TM시장가치(만유로)", "실제이적료(만유로)", "산출적정가(만유로)", "차액(만유로)", "평가"]], use_container_width=True)
        
        st.divider()
        if st.button("💾 위 목록 구글 시트에 일괄 저장하기", use_container_width=True):
            with st.spinner("구글 시트에 일괄 전송 중..."):
                saved = 0
                for _, r in df_show.iterrows():
                    payload = {
                        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "season": "24/25",
                        "name": r["선수명"],
                        "age": int(r["나이"]),
                        "league": r["전소속"],
                        "tier": batch_tier.split(":")[0],
                        "tm_val": float(r["TM시장가치(만유로)"]),
                        "fee": float(r["실제이적료(만유로)"]),
                        "fair_val": float(r["산출적정가(만유로)"]),
                        "diff": float(r["차액(만유로)"]),
                        "status": r["평가"],
                        "notes": "일괄 등록"
                    }
                    try:
                        requests.post(GOOGLE_SHEET_WEBAPP_URL, data=json.dumps(payload), headers={"Content-Type": "text/plain;charset=utf-8"}, timeout=8)
                        saved += 1
                    except:
                        pass
                st.success(f"✅ 총 {saved}명의 선수가 구글 시트에 안전하게 등록되었습니다!")

with tab2:
    st.subheader("✍️ 개별 선수 수동 입력")
    # 기존 단일 입력 로직 유지
    c1, c2 = st.columns(2)
    with c1:
        s_name = st.text_input("선수명", value="손흥민")
        s_age = st.number_input("나이", 15, 45, 23)
        s_league = st.selectbox("원소속 리그", list(LEAGUE_WEIGHTS.keys()))
        s_tier = st.selectbox("영입 구단 티어", list(CLUB_TIERS.keys()))
        s_tm = st.number_input("TM 시장가치 (만 유로)", value=3000, step=100)
        s_fee = st.number_input("실제 이적료 (만 유로)", value=4000, step=100)
    with c2:
        s_fair = s_tm * LEAGUE_WEIGHTS[s_league] * get_age_weight(s_age) * CLUB_TIERS[s_tier]
        s_diff = s_fee - s_fair
        st.metric("산출 적정가", f"€{s_fair:,.1f}만")
        st.metric("실제 이적료", f"€{s_fee:,.1f}만", delta=f"{s_diff:+,.1f}만 (€)", delta_color="inverse")
        if st.button("💾 단일 선수 구글 시트 저장"):
            p = {
                "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "season": "24/25",
                "name": s_name,
                "age": int(s_age),
                "league": s_league.split(" (")[0],
                "tier": s_tier.split(":")[0],
                "tm_val": float(s_tm),
                "fee": float(s_fee),
                "fair_val": round(s_fair, 1),
                "diff": round(s_diff, 1),
                "status": "고평가" if s_diff > 0 else "저평가",
                "notes": "단일 입력"
            }
            requests.post(GOOGLE_SHEET_WEBAPP_URL, data=json.dumps(p), headers={"Content-Type": "text/plain;charset=utf-8"}, timeout=8)
            st.success("저장되었습니다!")
