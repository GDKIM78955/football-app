import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime

# 1. 기본 설정
st.set_page_config(
    page_title="축구 이적시장 자동 수집 & 적정가 평가 시스템",
    page_icon="⚽",
    layout="wide"
)

GOOGLE_SHEET_WEBAPP_URL = "https://script.google.com/macros/s/AKfycbxV76sZFJaVPa7tmWSPBGlLaiZHijL77b7MZ_mpr6U-ia6hNO0UEiN-6A_1qz2u7XBNKA/exec"
SCRAPER_API_KEY = "b2dd656270f2635db8d6bdc6b564e53c"

# 주요 10대 리그 트랜스퍼마르크트 공식 URL 목록 (챔피언십 & 터키리그 포함)
LEAGUE_URLS = {
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿 잉글랜드 프리미어리그 (EPL 1부)": "https://www.transfermarkt.com/premier-league/transfers/wettbewerb/GB1",
    "🇪🇸 스페인 라리가 (La Liga 1부)": "https://www.transfermarkt.com/laliga/transfers/wettbewerb/ES1",
    "🇩🇪 독일 분데스리가 (Bundesliga 1부)": "https://www.transfermarkt.com/bundesliga/transfers/wettbewerb/L1",
    "🇮🇹 이탈리아 세리에 A (Serie A 1부)": "https://www.transfermarkt.com/serie-a/transfers/wettbewerb/IT1",
    "🇫🇷 프랑스 리그 1 (Ligue 1 1부)": "https://www.transfermarkt.com/ligue-1/transfers/wettbewerb/FR1",
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿 잉글랜드 챔피언십 (EFL 2부)": "https://www.transfermarkt.com/championship/transfers/wettbewerb/GB2",
    "🇹🇷 튀르키예 쉬페르리그 (Süper Lig 1부)": "https://www.transfermarkt.com/super-lig/transfers/wettbewerb/TR1",
    "🇳🇱 네덜란드 에레디비시 (Eredivisie 1부)": "https://www.transfermarkt.com/eredivisie/transfers/wettbewerb/NL1",
    "🇵🇹 포르투갈 프리메이라리가 (1부)": "https://www.transfermarkt.com/liga-nos/transfers/wettbewerb/PO1",
    "🇧🇪 벨기에 주필러 프로 리그 (1부)": "https://www.transfermarkt.com/jupiler-pro-league/transfers/wettbewerb/BE1"
}

# 가중치 딕셔너리
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

def parse_money(m_str):
    if not m_str or "free" in m_str.lower() or "loan" in m_str.lower() or "-" in m_str or "?" in m_str:
        return 0.0
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

# ScraperAPI를 통한 트랜스퍼마르크트 크롤링 함수 (국적 정보 포함)
def scrape_transfers_with_api(target_url):
    api_url = "http://api.scraperapi.com"
    params = {
        "api_key": SCRAPER_API_KEY,
        "url": target_url
    }
    
    resp = requests.get(api_url, params=params, timeout=60)
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
        
        # 첫 번째 표: In (영입 선수)
        in_table = tables[0]
        rows = in_table.select("tbody > tr")
        
        for r in rows:
            tds = r.find_all("td")
            if len(tds) < 5:
                continue
            
            # 1. 선수명 추출
            p_tag = r.select_one(".di.show-for-small a") or r.select_one(".di a") or tds[0].select_one("a")
            player_name = p_tag.get_text(strip=True) if p_tag else tds[0].get_text(strip=True)
            if not player_name or "No new arrivals" in player_name or "Arrivals" in player_name:
                continue
                
            # 2. 나이 추출
            age_text = tds[1].get_text(strip=True) if len(tds) > 1 else "24"
            try:
                age = int(age_text)
            except:
                age = 24

            # 3. 국적(Nationality) 추출
            nat_img = tds[2].select_one("img.flaggenrahmen") or r.select_one("img.flaggenrahmen")
            nat_text = nat_img.get("title", "").strip() if nat_img else "미상"
                
            # 4. 전 소속팀 추출
            left_club_tag = tds[4].select_one("a") if len(tds) > 4 else None
            left_club = left_club_tag.get_text(strip=True) if left_club_tag else (tds[4].get_text(strip=True) if len(tds) > 4 else "Unknown")
            
            # 5. 시장가치 및 실제 이적료
            mv_text = tds[3].get_text(strip=True) if len(tds) > 3 else "0"
            fee_text = tds[5].get_text(strip=True) if len(tds) > 5 else "0"
            
            tm_val = parse_money(mv_text)
            actual_fee = parse_money(fee_text)
            
            transfers.append({
                "영입팀": buying_club,
                "선수명": player_name,
                "국적": nat_text,
                "나이": age,
                "전소속": left_club,
                "TM시장가치(만유로)": tm_val,
                "실제이적료(만유로)": actual_fee
            })
            
    return transfers

# 2. 메인 UI
st.title("⚽ 축구 이적시장 자동 수집 & 가치 평가 시스템")

tab1, tab2 = st.tabs(["🌐 리그별 원클릭 자동 수집 & 시트 저장", "✍️ 단일 선수 수동 분석"])

with tab1:
    st.subheader("🌐 트랜스퍼마르크트 리그별 전 구단 영입 명단 자동 크롤링 (국적 포함)")
    
    col_l1, col_l2 = st.columns([2, 1])
    with col_l1:
        selected_league_label = st.selectbox("분석할 리그 선택 (유럽 주요 10대 리그)", list(LEAGUE_URLS.keys()))
        selected_url = LEAGUE_URLS[selected_league_label]
    with col_l2:
        batch_tier = st.selectbox("영입 구단 기본 티어", list(CLUB_TIERS.keys()), index=2)
        
    st.caption(f"타겟 URL: `{selected_url}`")
    
    if st.button("🚀 선택한 리그 이적 데이터 일괄 수집 시작", type="primary", use_container_width=True):
        with st.spinner(f"ScraperAPI를 통해 '{selected_league_label}'의 모든 구단 영입 명단을 긁어오는 중입니다... (약 10~20초 소요)"):
            data = scrape_transfers_with_api(selected_url)
            if not data:
                st.error("데이터를 수집하지 못했습니다. API 크레딧 또는 네트워크 상태를 확인해 주세요.")
            else:
                df = pd.DataFrame(data)
                
                # 적정가 자동 계산
                df["나이가중치"] = df["나이"].apply(get_age_weight)
                df["구단가중치"] = CLUB_TIERS[batch_tier]
                df["기본리그가중치"] = 0.95
                
                df["산출적정가(만유로)"] = (df["TM시장가치(만유로)"] * df["기본리그가중치"] * df["나이가중치"] * df["구단가중치"]).round(1)
                df["차액(만유로)"] = (df["실제이적료(만유로)"] - df["산출적정가(만유로)"]).round(1)
                
                def eval_status(row):
                    if row["산출적정가(만유로)"] == 0: return "자유/임대"
                    diff = row["차액(만유로)"]
                    if abs(diff) <= row["산출적정가(만유로)"] * 0.05: return "⚖️ 적정가"
                    elif diff > 0: return "⚠️ 고평가"
                    else: return "💎 저평가"
                    
                df["평가"] = df.apply(eval_status, axis=1)
                st.session_state["api_crawled_df"] = df
                st.session_state["cur_league_name"] = selected_league_label.split(" ")[1]
                st.success(f"🎉 총 {len(df)}건의 영입 데이터를 성공적으로 수집 및 분석 완료했습니다!")

    if "api_crawled_df" in st.session_state:
        df_show = st.session_state["api_crawled_df"]
        st.dataframe(df_show[["영입팀", "선수명", "국적", "나이", "전소속", "TM시장가치(만유로)", "실제이적료(만유로)", "산출적정가(만유로)", "차액(만유로)", "평가"]], use_container_width=True)
        
        st.divider()
        if st.button("💾 위 목록 중 '이적료가 발생한 선수들' 구글 시트에 일괄 저장하기", use_container_width=True):
            with st.spinner("구글 시트로 일괄 전송 중입니다..."):
                saved_count = 0
                for _, r in df_show.iterrows():
                    if r["실제이적료(만유로)"] > 0:
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
                            "notes": f"국적: {r['국적']} / 영입팀: {r['영입팀']}"
                        }
                        try:
                            requests.post(GOOGLE_SHEET_WEBAPP_URL, data=json.dumps(payload), headers={"Content-Type": "text/plain;charset=utf-8"}, timeout=8)
                            saved_count += 1
                        except:
                            pass
                st.success(f"✅ 총 {saved_count}명의 유료 이적 선수가 구글 시트에 안전하게 등록되었습니다!")

with tab2:
    st.subheader("✍️ 단일 선수 수동 입력 & 분석")
    c1, c2 = st.columns(2)
    with c1:
        s_name = st.text_input("선수명", value="손흥민")
        s_nat = st.text_input("선수 국적", value="대한민국")
        s_age = st.number_input("나이", 15, 45, 23)
        s_league = st.selectbox("원소속 리그", list(LEAGUE_WEIGHTS.keys()))
        s_tier = st.selectbox("영입 구단 티어", list(CLUB_TIERS.keys()))
        s_tm = st.number_input("TM 시장가치 (만 유로)", value=3000, step=100)
        s_fee = st.number_input("실제 이적료 (만 유로)", value=4000, step=100)
        s_note = st.text_area("메모/스탯 코멘트")
    with c2:
        s_fair = s_tm * LEAGUE_WEIGHTS[s_league] * get_age_weight(s_age) * CLUB_TIERS[s_tier]
        s_diff = s_fee - s_fair
        st.metric("산출 적정가", f"€{s_fair:,.1f}만")
        st.metric("실제 이적료", f"€{s_fee:,.1f}만", delta=f"{s_diff:+,.1f}만 (€)", delta_color="inverse")
        if st.button("💾 단일 건 저장"):
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
                "notes": f"국적: {s_nat} | {s_note}"
            }
            requests.post(GOOGLE_SHEET_WEBAPP_URL, data=json.dumps(p), headers={"Content-Type": "text/plain;charset=utf-8"}, timeout=8)
            st.success("구글 시트에 저장 완료!")
