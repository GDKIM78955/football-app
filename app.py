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

# 주요 10대 리그 트랜스퍼마르크트 공식 URL
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
            return num * 100 # 만 유로 단위 (예: €30.00m -> 3000만 유로)
        elif "K" in s:
            num = float(re.findall(r"[\d\.]+", s)[0])
            return num * 0.1 # 만 유로 단위 (예: €500k -> 50만 유로)
        else:
            nums = re.findall(r"[\d\.]+", s)
            return float(nums[0]) if nums else 0.0
    except:
        return 0.0

# Transfermarkt HTML 정밀 파싱 함수
def scrape_transfers_with_api(target_url):
    api_url = "http://api.scraperapi.com"
    params = {
        "api_key": SCRAPER_API_KEY,
        "url": target_url,
        "keep_headers": "true"
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }
    
    try:
        resp = requests.get(api_url, params=params, headers=headers, timeout=60)
    except Exception as e:
        return [], f"API 통신 실패: {e}"
        
    if resp.status_code != 200:
        return [], f"HTTP 응답 오류: {resp.status_code}"
    
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
        
        # In (영입 선수) 테이블 파싱
        in_table = tables[0]
        rows = in_table.select("tbody > tr")
        
        for r in rows:
            tds = r.find_all("td")
            if len(tds) < 6:
                continue
            
            # 1. 선수명 (td[0])
            p_tag = r.select_one(".di.show-for-small a") or r.select_one(".di a") or tds[0].select_one("a")
            player_name = p_tag.get_text(strip=True) if p_tag else tds[0].get_text(strip=True)
            if not player_name or "No new arrivals" in player_name or "Arrivals" in player_name:
                continue
                
            # 2. 나이 (td[1])
            age_text = tds[1].get_text(strip=True) if len(tds) > 1 else "24"
            try:
                age = int(age_text)
            except:
                age = 24

            # 3. 국적 (td[2])
            nat_img = tds[2].select_one("img.flaggenrahmen") or r.select_one("img.flaggenrahmen")
            nat_text = nat_img.get("title", "").strip() if nat_img else "미상"
                
            # 4. 포지션 (td[3])
            pos_text = tds[3].get_text(strip=True) if len(tds) > 3 else "-"

            # 5. 전 소속팀 (td[4])
            left_club_tag = tds[4].select_one("a") if len(tds) > 4 else None
            left_club = left_club_tag.get_text(strip=True) if left_club_tag else (tds[4].get_text(strip=True) if len(tds) > 4 else "Unknown")
            
            # 6. 시장가치 (td[5]) & 실제 이적료 (td[6] 또는 마지막 td)
            mv_text = tds[5].get_text(strip=True) if len(tds) > 5 else "0"
            fee_text = tds[6].get_text(strip=True) if len(tds) > 6 else (tds[-1].get_text(strip=True) if len(tds) > 5 else "0")
            
            tm_val = parse_money(mv_text)
            actual_fee = parse_money(fee_text)
            
            transfers.append({
                "영입팀": buying_club,
                "선수명": player_name,
                "국적": nat_text,
                "포지션": pos_text,
                "나이": age,
                "전소속": left_club,
                "TM시장가치(만유로)": tm_val,
                "실제이적료(만유로)": actual_fee,
                "원문이적료": fee_text,
                "원문시장가치": mv_text
            })
            
    return transfers, "성공"

# 2. 메인 UI
st.title("⚽ 축구 이적시장 자동 수집 & 가치 평가 시스템")

tab1, tab2 = st.tabs(["🌐 리그별 원클릭 자동 수집", "📋 텍스트 직접 복사-붙여넣기 파서"])

with tab1:
    st.subheader("🌐 트랜스퍼마르크트 리그별 전 구단 영입 명단 자동 크롤링")
    
    col_l1, col_l2 = st.columns([2, 1])
    with col_l1:
        selected_league_label = st.selectbox("분석할 리그 선택", list(LEAGUE_URLS.keys()))
        selected_url = LEAGUE_URLS[selected_league_label]
    with col_l2:
        batch_tier = st.selectbox("영입 구단 기본 티어", list(CLUB_TIERS.keys()), index=2)
    
    if st.button("🚀 선택한 리그 이적 데이터 일괄 수집 시작", type="primary", use_container_width=True):
        with st.spinner(f"ScraperAPI로 정밀 데이터를 수집 및 분석 중입니다..."):
            data, msg = scrape_transfers_with_api(selected_url)
            if not data:
                st.error(f"데이터를 가져오지 못했습니다. (원인: {msg})")
            else:
                df = pd.DataFrame(data)
                df["나이가중치"] = df["나이"].apply(get_age_weight)
                df["구단가중치"] = CLUB_TIERS[batch_tier]
                df["기본리그가중치"] = 0.95
                
                # 적정가 = TM몸값 * 기본리그가중치 * 나이가중치 * 구단가중치
                df["산출적정가(만유로)"] = (df["TM시장가치(만유로)"] * df["기본리그가중치"] * df["나이가중치"] * df["구단가중치"]).round(1)
                df["차액(만유로)"] = (df["실제이적료(만유로)"] - df["산출적정가(만유로)"]).round(1)
                
                def eval_status(row):
                    if row["실제이적료(만유로)"] == 0: return "자유/임대"
                    if row["산출적정가(만유로)"] == 0: return "평가불가"
                    diff = row["차액(만유로)"]
                    if abs(diff) <= row["산출적정가(만유로)"] * 0.05: return "⚖️ 적정가"
                    elif diff > 0: return "⚠️ 고평가"
                    else: return "💎 저평가"
                    
                df["평가"] = df.apply(eval_status, axis=1)
                st.session_state["api_crawled_df"] = df
                st.success(f"🎉 총 {len(df)}명의 선수 데이터를 정확하게 수집 및 분석 완료했습니다!")

    if "api_crawled_df" in st.session_state:
        df_show = st.session_state["api_crawled_df"]
        st.dataframe(
            df_show[["영입팀", "선수명", "국적", "포지션", "나이", "전소속", "TM시장가치(만유로)", "실제이적료(만유로)", "산출적정가(만유로)", "차액(만유로)", "평가"]], 
            use_container_width=True
        )
        
        st.divider()
        if st.button("💾 위 목록 중 '이적료가 발생한 선수들' 구글 시트에 일괄 저장하기", use_container_width=True):
            with st.spinner("구글 시트로 전송 중..."):
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
                            "notes": f"국적: {r['국적']} | 포지션: {r['포지션']} | 영입팀: {r['영입팀']}"
                        }
                        try:
                            requests.post(GOOGLE_SHEET_WEBAPP_URL, data=json.dumps(payload), headers={"Content-Type": "text/plain;charset=utf-8"}, timeout=8)
                            saved_count += 1
                        except:
                            pass
                st.success(f"✅ 총 {saved_count}명의 유료 이적 선수가 구글 시트에 안전하게 등록되었습니다!")

with tab2:
    st.subheader("📋 트랜스퍼마르크트 표 복붙 파서")
    st.markdown("웹페이지 표를 직접 드래그 복사(`Ctrl+C`)하여 붙여넣기(`Ctrl+V`) 하실 때 사용합니다.")
    
    raw_text_input = st.text_area("복사한 텍스트 붙여넣기", height=160, placeholder="선수명, 포지션, 이적료 등이 포함된 표를 복사해서 붙여넣으세요.")
    if st.button("🚀 붙여넣은 텍스트 파싱 & 분석"):
        if not raw_text_input.strip():
            st.warning("텍스트를 붙여넣어 주세요.")
        else:
            lines = raw_text_input.split("\n")
            p_list = []
            for l in lines:
                parts = re.split(r"\t+|\s{2,}", l.strip())
                if len(parts) >= 5:
                    name = parts[0]
                    mv = 0.0
                    fee = 0.0
                    age = 24
                    left_c = parts[4] if len(parts) > 4 else "전소속"
                    for p in parts:
                        if p.isdigit() and 15 <= int(p) <= 45: age = int(p)
                        elif "€" in p or "m" in p or "k" in p:
                            if mv == 0.0: mv = parse_money(p)
                            else: fee = parse_money(p)
                    if mv > 0 or fee > 0:
                        p_list.append({"선수명": name, "나이": age, "전소속": left_c, "TM시장가치(만유로)": mv, "실제이적료(만유로)": fee})
            if p_list:
                df_p = pd.DataFrame(p_list)
                df_p["적정가"] = (df_p["TM시장가치(만유로)"] * 0.95 * df_p["나이"].apply(get_age_weight)).round(1)
                st.dataframe(df_p, use_container_width=True)
            else:
                st.error("데이터 형식을 인식하지 못했습니다.")
