import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime

# 1. 페이지 설정
st.set_page_config(
    page_title="축구 이적료 분석 & TM 자동 수집기",
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
    "Tier 1: 엘리트 메가클럽": 1.15,
    "Tier 2: 빅클럽": 1.08,
    "Tier 3: 중상위권 클럽": 1.00,
    "Tier 4: 중하위권 클럽": 0.92,
    "Tier 5: 소형/셀링 클럽": 0.80
}

def get_age_weight(age):
    if age <= 19: return 1.00
    elif age <= 23: return 1.12
    elif age <= 27: return 1.00
    elif age <= 29: return 0.90
    elif age <= 31: return 0.75
    else: return 0.55

def parse_fee_to_million_euros(fee_str):
    if not fee_str or "free" in fee_str.lower() or "loan" in fee_str.lower() or "-" in fee_str or "?" in fee_str:
        return 0.0
    s = fee_str.replace("€", "").replace("m", "M").replace("k", "K").strip()
    try:
        if "M" in s:
            val = float(re.findall(r"[\d\.]+", s)[0])
            return val * 100 # 만 유로 단위 (예: 30.00M = 3000만 유로)
        elif "K" in s:
            val = float(re.findall(r"[\d\.]+", s)[0])
            return val * 0.1 # 만 유로 단위 (예: 500k = 50만 유로)
        else:
            return float(re.findall(r"[\d\.]+", s)[0])
    except:
        return 0.0

# 트랜스퍼마르크트 스크래핑 함수
def scrape_tm_league_transfers(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    resp = requests.get(url, headers=headers, timeout=15)
    if resp.status_code != 200:
        return []
    
    soup = BeautifulSoup(resp.text, "html.parser")
    boxes = soup.select(".box")
    transfers = []
    
    for b in boxes:
        club_header = b.select_one(".content-box-headline a")
        if not club_header:
            continue
        buying_club = club_header.get_text(strip=True)
        
        tables = b.select(".responsive-table")
        if not tables:
            continue
        
        # 첫 번째 테이블은 보통 'In (영입)' 목록
        in_table = tables[0]
        rows = in_table.select("tbody > tr")
        
        for r in rows:
            tds = r.find_all("td")
            if len(tds) < 5:
                continue
            
            # 선수명
            p_tag = r.select_one(".hide-for-small .di.show-for-small a") or r.select_one(".di a") or tds[0].select_one("a")
            player_name = p_tag.get_text(strip=True) if p_tag else tds[0].get_text(strip=True)
            if not player_name or "No new arrivals" in player_name:
                continue
                
            # 나이
            age_text = tds[1].get_text(strip=True) if len(tds) > 1 else "23"
            try:
                age = int(age_text)
            except:
                age = 23
                
            # 전 소속팀 / 리그
            left_club = tds[4].get_text(strip=True) if len(tds) > 4 else "Unknown"
            
            # 시장가치 및 실제 이적료
            mv_text = tds[3].get_text(strip=True) if len(tds) > 3 else "0"
            fee_text = tds[5].get_text(strip=True) if len(tds) > 5 else "0"
            
            tm_val = parse_fee_to_million_euros(mv_text)
            actual_fee = parse_fee_to_million_euros(fee_text)
            
            transfers.append({
                "영입팀": buying_club,
                "선수명": player_name,
                "나이": age,
                "전소속": left_club,
                "TM시장가치(만유로)": tm_val,
                "실제이적료(만유로)": actual_fee,
                "원문이적료": fee_text,
                "원문시장가치": mv_text
            })
            
    return transfers

# 3. Streamlit 화면 구성
st.title("⚽ 축구 이적시장 자동 수집 & 가치 평가 시스템")

tab1, tab2 = st.tabs(["📥 TM 리그별 이적 일괄 자동 수집", "✍️ 단일 선수 수동 분석"])

# ================= TAB 1: 자동 수집 모드 =================
with tab1:
    st.subheader("🌐 트랜스퍼마르크트 리그별 최신 이적 데이터 가져오기")
    
    c1, c2 = st.columns([3, 1])
    with c1:
        tm_url = st.text_input(
            "트랜스퍼마르크트 이적 페이지 URL 입력", 
            value="https://www.transfermarkt.com/premier-league/transfers/wettbewerb/GB1"
        )
    with c2:
        default_tier = st.selectbox("영입 구단 기본 티어", list(CLUB_TIERS.keys()), index=2)
    
    if st.button("🚀 이적 명단 불러오기 & 적정가 자동 계산", type="primary"):
        with st.spinner("트랜스퍼마르크트에서 최신 이적 데이터를 긁어오는 중입니다..."):
            data = scrape_tm_league_transfers(tm_url)
            if not data:
                st.warning("데이터를 가져오지 못했습니다. URL이 올바른지 확인해 주세요.")
            else:
                df = pd.DataFrame(data)
                
                # 계산 필드 추가
                df["나이가중치"] = df["나이"].apply(get_age_weight)
                df["구단가중치"] = CLUB_TIERS[default_tier]
                df["기본리그가중치"] = 0.95 # 기본값
                
                # 적정가 = TM몸값 * 0.95 * 나이가중치 * 구단가중치
                df["산출적정가(만유로)"] = (df["TM시장가치(만유로)"] * df["기본리그가중치"] * df["나이가중치"] * df["구단가중치"]).round(1)
                df["차액(만유로)"] = (df["실제이적료(만유로)"] - df["산출적정가(만유로)"]).round(1)
                
                def get_status(row):
                    if row["산출적정가(만유로)"] == 0: return "평가불가/자유이적"
                    diff = row["차액(만유로)"]
                    if abs(diff) <= row["산출적정가(만유로)"] * 0.05: return "⚖️ 적정가"
                    elif diff > 0: return "⚠️ 고평가"
                    else: return "💎 저평가"
                    
                df["평가"] = df.apply(get_status, axis=1)
                st.session_state["crawled_df"] = df
                st.success(f"총 {len(df)}건의 영입 데이터를 성공적으로 불러왔습니다!")

    if "crawled_df" in st.session_state:
        df_display = st.session_state["crawled_df"]
        st.dataframe(df_display[["영입팀", "선수명", "나이", "전소속", "TM시장가치(만유로)", "실제이적료(만유로)", "산출적정가(만유로)", "차액(만유로)", "평가"]], use_container_width=True)
        
        st.divider()
        if st.button("💾 위 목록 중 '이적료가 발생한 선수들' 구글 시트에 일괄 저장하기", use_container_width=True):
            with st.spinner("구글 시트에 전송 중..."):
                saved_count = 0
                for _, r in df_display.iterrows():
                    if r["실제이적료(만유로)"] > 0: # 이적료가 있는 선수만 저장
                        payload = {
                            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                            "season": "24/25",
                            "name": r["선수명"],
                            "age": int(r["나이"]),
                            "league": r["전소속"],
                            "tier": default_tier.split(":")[0],
                            "tm_val": float(r["TM시장가치(만유로)"]),
                            "fee": float(r["실제이적료(만유로)"]),
                            "fair_val": float(r["산출적정가(만유로)"]),
                            "diff": float(r["차액(만유로)"]),
                            "status": r["평가"],
                            "notes": f"영입구단: {r['영입팀']}"
                        }
                        try:
                            requests.post(GOOGLE_SHEET_WEBAPP_URL, data=json.dumps(payload), headers={"Content-Type": "text/plain;charset=utf-8"}, timeout=8)
                            saved_count += 1
                        except:
                            pass
                st.success(f"✅ 총 {saved_count}명의 유료 이적 선수가 구글 시트에 성공적으로 등록되었습니다!")

# ================= TAB 2: 수동 개별 분석 모드 =================
with tab2:
    st.subheader("✍️ 개별 선수 정밀 분석 & 시트 저장")
    col1, col2 = st.columns(2)
    with col1:
        s_name = st.text_input("선수명", value="손흥민")
        s_age = st.number_input("나이", 15, 45, 23)
        s_league = st.selectbox("원소속 리그", list(LEAGUE_WEIGHTS.keys()))
        s_tier = st.selectbox("영입 구단 규모", list(CLUB_TIERS.keys()))
        s_tm = st.number_input("TM 시장가치 (만 유로)", value=3000, step=100)
        s_fee = st.number_input("실제 이적료 (만 유로)", value=4000, step=100)
        s_note = st.text_area("메모/기대스탯")
    
    with col2:
        s_fair = s_tm * LEAGUE_WEIGHTS[s_league] * get_age_weight(s_age) * CLUB_TIERS[s_tier]
        s_diff = s_fee - s_fair
        st.metric("산출 적정가", f"€{s_fair:,.1f}만")
        st.metric("실제 이적료", f"€{s_fee:,.1f}만", delta=f"{s_diff:+,.1f}만 (€)", delta_color="inverse")
        
        if st.button("💾 단일 건 구글 시트 저장"):
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
                "notes": s_note
            }
            requests.post(GOOGLE_SHEET_WEBAPP_URL, data=json.dumps(p), headers={"Content-Type": "text/plain;charset=utf-8"}, timeout=8)
            st.success("저장 완료!")
