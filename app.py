import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import numpy as np
import requests
import json
import math
import re
import base64
from io import BytesIO
from PIL import Image
import plotly.graph_objects as go
from datetime import datetime

# 1. 페이지 기본 설정
st.set_page_config(
    page_title="축구 이적시장 12대 가중치 분석 & FotMob 프로젝션 Pro",
    page_icon="⚽",
    layout="wide"
)

# 최신 구글 시트 웹앱 URL
GOOGLE_SHEET_WEBAPP_URL = "https://script.google.com/macros/s/AKfycbwmxL1KAuMav1KpXsRQpsa-p18i_-nkWVG-4MkTR7c6jI7FRqNvUaTLSuC7lGFivYvD/exec"
SPREADSHEET_ID = "16CeAQp1-xqc-mhtvlP0vLlQu5k1pg8DW5A-m29WCFdw"
SHEET_CSV_URL = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/gviz/tq?tqx=out:csv"

VAL_SHEET_GID = "15389686"
VAL_SHEET_CSV_URL = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv&gid={VAL_SHEET_GID}"

if "form_key_id" not in st.session_state:
    st.session_state["form_key_id"] = 0
if "last_saved_msg" not in st.session_state:
    st.session_state["last_saved_msg"] = None

# =========================================================================
# [구글 드라이브 폴더 자동 스캔 & 체크무늬/흰배경 완벽 제거 엔진]
# - 아래 큰따옴표(" ") 안에 구글 드라이브 '축구구단_로고' 폴더 공유 링크를 넣어주세요!
# =========================================================================
DRIVE_LOGO_FOLDER_URL = "https://drive.google.com/drive/folders/1jhKbgnrWEK3t0rQuP9OYTryYrI56Ujye?usp=drive_link"

DEFAULT_CLUB_LOGOS = {
    "아스날": "https://crests.football-data.org/57.png",
    "아스널": "https://crests.football-data.org/57.png",
    "맨시티": "https://crests.football-data.org/65.png",
    "맨체스터 시티": "https://crests.football-data.org/65.png",
    "리버풀": "https://crests.football-data.org/64.png",
    "첼시": "https://crests.football-data.org/61.png",
    "토트넘": "https://crests.football-data.org/73.png",
    "맨유": "https://crests.football-data.org/66.png",
    "맨체스터 유나이티드": "https://crests.football-data.org/66.png",
    "뉴캐슬": "https://crests.football-data.org/67.png",
    "아스톤 빌라": "https://crests.football-data.org/58.png",
    "애스턴 빌라": "https://crests.football-data.org/58.png",
    "브라이튼": "https://crests.football-data.org/397.png",
    "웨스트햄": "https://crests.football-data.org/563.png",
    "본머스": "https://crests.football-data.org/1044.png",
    "풀럼": "https://crests.football-data.org/63.png",
    "울버햄튼": "https://crests.football-data.org/76.png",
    "크리스탈 팰리스": "https://crests.football-data.org/354.png",
    "브렌트포드": "https://crests.football-data.org/402.png",
    "에버턴": "https://crests.football-data.org/62.png",
    "노팅엄": "https://crests.football-data.org/351.png",
    "노팅엄 포레스트": "https://crests.football-data.org/351.png",
    "레알 마드리드": "https://crests.football-data.org/86.png",
    "바르셀로나": "https://crests.football-data.org/81.png",
    "AT 마드리드": "https://crests.football-data.org/78.png",
    "아틀레티코 마드리드": "https://crests.football-data.org/78.png",
    "바이에른 뮌헨": "https://crests.football-data.org/5.png",
    "뮌헨": "https://crests.football-data.org/5.png",
    "레버쿠젠": "https://crests.football-data.org/3.png",
    "도르트문트": "https://crests.football-data.org/4.png",
    "라이프치히": "https://crests.football-data.org/721.png",
    "인터밀란": "https://crests.football-data.org/108.png",
    "인테르": "https://crests.football-data.org/108.png",
    "유벤투스": "https://crests.football-data.org/109.png",
    "AC밀란": "https://crests.football-data.org/98.png",
    "나폴리": "https://crests.football-data.org/113.png",
    "AS로마": "https://crests.football-data.org/100.png",
    "아탈란타": "https://crests.football-data.org/102.png",
    "PSG": "https://crests.football-data.org/524.png",
    "파리 생제르맹": "https://crests.football-data.org/524.png",
    "스포르팅": "https://crests.football-data.org/498.png",
    "벤피카": "https://crests.football-data.org/1903.png",
    "포르투": "https://crests.football-data.org/503.png",
    "아약스": "https://crests.football-data.org/678.png",
    "PSV": "https://crests.football-data.org/674.png",
    "페예노르트": "https://crests.football-data.org/675.png"
}

CLUB_SYNONYMS = {
    "아스널": ["아스날", "Arsenal"],
    "아스날": ["아스널", "Arsenal"],
    "맨시티": ["맨체스터 시티", "맨체스터시티"],
    "맨유": ["맨체스터 유나이티드", "맨체스터유나이티드"],
    "아스톤 빌라": ["애스턴 빌라", "아스톤빌라", "애스턴빌라"],
    "애스턴 빌라": ["아스톤 빌라", "아스톤빌라", "애스턴빌라"],
    "바이에른 뮌헨": ["뮌헨", "바이에른뮌헨"],
    "인터밀란": ["인테르", "인터 밀란"],
    "인테르": ["인터밀란", "인터 밀란"],
    "PSG": ["파리 생제르맹", "파리생제르맹"],
    "AT 마드리드": ["아틀레티코 마드리드", "AT마드리드"]
}

@st.cache_data(ttl=300, show_spinner=False)
def fetch_drive_folder_logos(folder_url):
    """구글 시트 Apps Script를 통해 드라이브 로고 폴더 안의 모든 파일명과 링크를 자동 스캔"""
    if not folder_url or "drive.google.com" not in str(folder_url):
        return {}
    try:
        res = requests.post(
            GOOGLE_SHEET_WEBAPP_URL,
            data=json.dumps({"action": "list_drive_logos", "folder_url": folder_url.strip()}),
            headers={"Content-Type": "text/plain;charset=utf-8"},
            timeout=10,
            allow_redirects=True
        )
        if res.status_code in [200, 302]:
            rj = res.json()
            if rj.get("status") == "success":
                return rj.get("logos", {})
    except Exception:
        pass
    return {}

if "custom_club_logos" not in st.session_state:
    st.session_state["custom_club_logos"] = DEFAULT_CLUB_LOGOS.copy()

scanned_drive_logos = fetch_drive_folder_logos(DRIVE_LOGO_FOLDER_URL)
for c_name, d_url in scanned_drive_logos.items():
    st.session_state["custom_club_logos"][c_name] = d_url
    for syn in CLUB_SYNONYMS.get(c_name, []):
        st.session_state["custom_club_logos"][syn] = d_url

def extract_drive_id(url_str):
    if not url_str or not isinstance(url_str, str):
        return ""
    u = url_str.strip()
    if "drive.google.com" not in u:
        return ""
    m = re.search(r"/file/d/([a-zA-Z0-9_-]+)", u)
    if not m:
        m = re.search(r"[?&]id=([a-zA-Z0-9_-]+)", u)
    return m.group(1) if m else ""

@st.cache_data(ttl=3600, show_spinner=False)
def url_to_base64_img(img_url):
    """외곽의 흰색 배경 및 가짜 투명 체크무늬(회색+흰색 격자) 완벽 제거 엔진"""
    if not img_url or not str(img_url).strip():
        return ""
    u = str(img_url).strip()
    if u.startswith("data:image"):
        return u

    drive_id = extract_drive_id(u)
    if drive_id:
        candidate_urls = [
            f"https://drive.google.com/uc?export=download&id={drive_id}",
            f"https://lh3.googleusercontent.com/d/{drive_id}",
            f"https://drive.google.com/thumbnail?id={drive_id}&sz=w500"
        ]
    else:
        candidate_urls = [u]

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "image/avif,image/webp,image/apng,image/png,image/*,*/*;q=0.8"
    }

    for target_u in candidate_urls:
        try:
            resp = requests.get(target_u, headers=headers, timeout=6, allow_redirects=True)
            if resp.status_code == 200 and len(resp.content) > 100:
                mime = resp.headers.get("Content-Type", "")
                if "text/html" in mime:
                    continue

                img = Image.open(BytesIO(resp.content)).convert("RGBA")
                width, height = img.size
                pixels = img.load()

                corners = [pixels[0, 0], pixels[width - 1, 0], pixels[0, height - 1], pixels[width - 1, height - 1]]
                needs_bg_removal = any(c[3] > 50 for c in corners)

                if needs_bg_removal:
                    visited = set()
                    queue = (
                        [(x, 0) for x in range(width)] +
                        [(x, height - 1) for x in range(width)] +
                        [(0, y) for y in range(height)] +
                        [(width - 1, y) for y in range(height)]
                    )
                    while queue:
                        x, y = queue.pop()
                        if (x, y) in visited or x < 0 or x >= width or y < 0 or y >= height:
                            continue
                        visited.add((x, y))
                        r, g, b, a = pixels[x, y]
                        lum = (r + g + b) / 3.0
                        sat = max(r, g, b) - min(r, g, b)

                        if a == 0 or (lum >= 135 and sat <= 30):
                            pixels[x, y] = (0, 0, 0, 0)
                            queue.extend([(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)])

                bbox = img.getbbox()
                if bbox:
                    img = img.crop(bbox)

                out_buf = BytesIO()
                img.save(out_buf, format="PNG")
                b64 = base64.b64encode(out_buf.getvalue()).decode("utf-8")
                return f"data:image/png;base64,{b64}"
        except Exception:
            continue

    return f"https://wsrv.nl/?url={candidate_urls[0]}&output=png"

def extract_logos_from_notes(notes_str):
    if not isinstance(notes_str, str):
        return "", ""
    m_from = re.search(r"\|\|LOGO_FROM:(.*?)\|\|", notes_str)
    m_to = re.search(r"\|\|LOGO_TO:(.*?)\|\|", notes_str)
    f_url = m_from.group(1).strip() if m_from else ""
    t_url = m_to.group(1).strip() if m_to else ""
    return f_url, t_url

def extract_subpos_from_notes(notes_str):
    if not isinstance(notes_str, str):
        return []
    m_sub = re.search(r"\|\|SUBPOS:(.*?)\|\|", notes_str)
    if m_sub and m_sub.group(1).strip():
        return [x.strip() for x in m_sub.group(1).split(",") if x.strip()]
    return []

def clean_notes_display(notes_str):
    if not isinstance(notes_str, str):
        return ""
    cleaned = re.sub(r"\|\|LOGO_FROM:.*?\|\|", "", notes_str)
    cleaned = re.sub(r"\|\|LOGO_TO:.*?\|\|", "", cleaned)
    cleaned = re.sub(r"\|\|SUBPOS:.*?\|\|", "", cleaned)
    return cleaned.strip(" |")

default_stats = {
    "f_mins": 2206, "f_goals": 16, "f_xg": 17.44, "f_assists": 4, "f_xa": 3.33,
    "f_rating": 7.32, "f_matches": 28, "f_starts": 25, "f_shots": 88, "f_sot": 43,
    "f_chances": 25, "f_dribbles": 14, "f_touches_box": 153, "f_tackles": 24,
    "f_starts_val": 25, "f_big_chances": 2, "f_pk": 0, "f_pass_pct": 88.2, "f_duels_pct": 62.4, "f_aerial_pct": 65.8,
    "f_gk_saves": 78, "f_gk_conceded": 28, "f_gk_prevented": 2.45,
    "f_gk_cs": 10, "f_gk_errors": 0, "f_gk_claims": 18
}
for k, v in default_stats.items():
    if k not in st.session_state:
        st.session_state[k] = v

@st.cache_data(ttl=60)
def fetch_sheet_history():
    try:
        df = pd.read_csv(SHEET_CSV_URL)
        return df
    except Exception:
        return pd.DataFrame()

history_df = fetch_sheet_history()

if not history_df.empty and "스카우팅메모" in history_df.columns:
    for _, r_hist in history_df.iterrows():
        nt_raw = str(r_hist.get("스카우팅메모", ""))
        f_team_h = str(r_hist.get("원소속팀명", "")).strip()
        t_team_h = str(r_hist.get("이적팀명", "")).strip()
        f_logo_h, t_logo_h = extract_logos_from_notes(nt_raw)
        if f_team_h and f_logo_h and "fotmob.com" not in f_logo_h:
            st.session_state["custom_club_logos"][f_team_h] = f_logo_h
        if t_team_h and t_logo_h and "fotmob.com" not in t_logo_h:
            st.session_state["custom_club_logos"][t_team_h] = t_logo_h

def get_raw_club_logo(team_name, manual_url=""):
    if manual_url and str(manual_url).strip() and not str(manual_url).strip().startswith("data:image"):
        return str(manual_url).strip()
    t_clean = str(team_name).strip()
    if not t_clean:
        return ""
    logo_dict = st.session_state["custom_club_logos"]
    if t_clean in logo_dict:
        return logo_dict[t_clean]
    for k_club, v_url in logo_dict.items():
        if k_club in t_clean or t_clean in k_club:
            return v_url
    return ""

def resolve_club_logo(team_name, manual_url=""):
    raw_u = get_raw_club_logo(team_name, manual_url)
    return url_to_base64_img(raw_u) if raw_u else ""

# =========================================================================
# [V8 Pro FM 스카우팅 그래픽 엔진: 미니 포지션 피치 + 90종 정밀 스카우팅 프리셋]
# =========================================================================
SUB_POS_OPTIONS = [
    "ST (스트라이커)", "LW (좌측 윙어)", "RW (우측 윙어)", "CAM (공격형 미드필더)",
    "CM (중앙 미드필더)", "CDM (수비형 미드필더)", "LB/LWB (좌측 풀백·윙백)",
    "RB/RWB (우측 풀백·윙백)", "CB (센터백)", "GK (골키퍼)"
]

def build_fm_mini_pitch_svg(main_pos_str, versatility_str, manual_sub_list, stats_dict):
    """FM 스타일 미니 포지션 숙련도 맵 (🟢 주포지션 천연 / 🟡 서브포지션 능숙 하이브리드)"""
    nodes = {
        "ST":  (80, 22, "ST"),
        "LW":  (28, 44, "LW"),
        "CAM": (80, 50, "CAM"),
        "RW":  (132, 44, "RW"),
        "CM":  (80, 82, "CM"),
        "CDM": (80, 112, "CDM"),
        "LB":  (26, 138, "LB"),
        "CB":  (80, 144, "CB"),
        "RB":  (134, 138, "RB"),
        "GK":  (80, 174, "GK")
    }

    primary_nodes = set()
    secondary_nodes = set()

    if "ST/CF" in main_pos_str:
        primary_nodes.add("ST")
    elif "WG/CAM" in main_pos_str:
        primary_nodes.update(["LW", "RW", "CAM"])
    elif "CM/CDM" in main_pos_str:
        primary_nodes.update(["CM", "CDM"])
    elif "RB/LB/WB" in main_pos_str:
        primary_nodes.update(["LB", "RB"])
    elif "CB" in main_pos_str:
        primary_nodes.add("CB")
    elif "GK" in main_pos_str:
        primary_nodes.add("GK")

    is_multi = "단일" not in versatility_str
    if is_multi:
        if manual_sub_list:
            for item in manual_sub_list:
                code = item.split(" ")[0].split("/")[0].strip()
                if code in nodes and code not in primary_nodes:
                    secondary_nodes.add(code)
        else:
            is_utility_3 = "3개" in versatility_str
            p_pass = stats_dict.get("pass_pct", 85.0)
            p_drib = stats_dict.get("p90_drib", 0.5)
            p_box = stats_dict.get("p90_box", 1.5)
            p_tkl = stats_dict.get("p90_tkl", 1.2)

            if "ST" in primary_nodes:
                secondary_nodes.update(["LW", "RW"] if p_drib >= 0.8 else ["CAM"])
                if is_utility_3: secondary_nodes.update(["LW", "RW", "CAM"])
            elif "CAM" in primary_nodes:
                if p_box >= 4.0: secondary_nodes.add("ST")
                else: secondary_nodes.add("CM")
            elif "CM" in primary_nodes:
                if p_tkl >= 1.8: secondary_nodes.add("CB")
                else: secondary_nodes.add("CAM")
                if is_utility_3: secondary_nodes.update(["RB", "LB"])
            elif "LB" in primary_nodes:
                secondary_nodes.add("CB" if p_tkl >= 1.6 else "LW")
                if is_utility_3: secondary_nodes.add("CDM")
            elif "CB" in primary_nodes:
                if p_pass >= 88.5: secondary_nodes.add("CDM")
                else: secondary_nodes.update(["RB", "LB"])
                if is_utility_3: secondary_nodes.update(["CDM", "RB", "LB"])

    dots_svg = ""
    for code, (nx, ny, lbl) in nodes.items():
        if code in primary_nodes:
            dots_svg += (
                f'<circle cx="{nx}" cy="{ny}" r="11" fill="#10B981" fill-opacity="0.35"/>'
                f'<circle cx="{nx}" cy="{ny}" r="7.5" fill="#10B981" stroke="#FFFFFF" stroke-width="1.8"/>'
                f'<text x="{nx}" y="{ny+18}" text-anchor="middle" fill="#6EE7B7" font-size="8.5" font-weight="900">{lbl}</text>'
            )
        elif code in secondary_nodes:
            dots_svg += (
                f'<circle cx="{nx}" cy="{ny}" r="9.5" fill="#FBBF24" fill-opacity="0.28"/>'
                f'<circle cx="{nx}" cy="{ny}" r="6.5" fill="#FBBF24" stroke="#0F172A" stroke-width="1.5"/>'
                f'<text x="{nx}" y="{ny+17}" text-anchor="middle" fill="#FDE68A" font-size="8" font-weight="800">{lbl}</text>'
            )
        else:
            dots_svg += (
                f'<circle cx="{nx}" cy="{ny}" r="4.5" fill="#1E293B" stroke="#475569" stroke-width="1"/>'
                f'<text x="{nx}" y="{ny+14}" text-anchor="middle" fill="#64748B" font-size="7.5" font-weight="700">{lbl}</text>'
            )

    return f"""
    <svg viewBox="0 0 160 196" width="142" height="174" style="display:block; margin:0 auto;">
        <rect x="4" y="4" width="152" height="188" rx="10" fill="#064E3B" stroke="#34D399" stroke-width="1.5" stroke-opacity="0.55"/>
        <line x1="4" y1="98" x2="156" y2="98" stroke="rgba(255,255,255,0.22)" stroke-width="1.2"/>
        <circle cx="80" cy="98" r="20" fill="none" stroke="rgba(255,255,255,0.22)" stroke-width="1.2"/>
        <rect x="42" y="4" width="76" height="26" fill="none" stroke="rgba(255,255,255,0.22)" stroke-width="1.2"/>
        <rect x="42" y="166" width="76" height="26" fill="none" stroke="rgba(255,255,255,0.22)" stroke-width="1.2"/>
        {dots_svg}
    </svg>
    """

def generate_fm_scouting_features(
    main_pos, age, rating, goals, xg, assists, xa, shots, sot, chances, big_chances,
    dribbles, box_touches, tackles, pass_pct, duels_pct, aerial_pct, pk_goals,
    gk_saves, gk_conceded, gk_prev, gk_cs, gk_errors, gk_claims,
    matches, starts, mins, overpay_pct, stage_str, inj_str, reg_str, vers_str, contract_str, urg_str, league_w
):
    """
    [90종 풀버전 FM 스카우팅 인텔리전스 엔진]
    - 스탯 상호 비율(슈팅 정확도, 빅찬스 순도, PK 비중, 선발 신뢰도, 지상/공중 편차 등)과
      포지션별 전술 아키타입(포처, 컴플리트 포워드, 인사이드 포워드, 딥라잉 플레이메이커, 볼 플레잉 CB 등)을 교차 분석
    """
    p90 = max(1.0, mins / 90.0)
    p90_g = goals / p90
    p90_xg = xg / p90
    p90_xa = xa / p90
    p90_xg_xa = (xg + xa) / p90
    p90_shots = shots / p90
    p90_sot = sot / p90
    p90_chances = chances / p90
    p90_bc = big_chances / p90
    p90_drib = dribbles / p90
    p90_box = box_touches / p90
    p90_tkl = tackles / p90
    sot_ratio = (sot / shots * 100.0) if shots > 0 else 0.0
    bc_ratio = (big_chances / chances * 100.0) if chances > 0 else 0.0
    start_ratio = (starts / matches * 100.0) if matches > 0 else 80.0
    non_pk_goals = max(0, goals - pk_goals)
    pk_share = (pk_goals / goals * 100.0) if goals > 0 else 0.0
    duels_avg = (duels_pct + aerial_pct) / 2.0

    is_st = "ST/CF" in main_pos
    is_wg_cam = "WG/CAM" in main_pos
    is_cm_cdm = "CM/CDM" in main_pos
    is_fb = "RB/LB/WB" in main_pos
    is_cb = "CB" in main_pos
    is_gk = "GK" in main_pos
    is_def_mid = is_cm_cdm or is_fb or is_cb

    # =========================================================================
    # 1) FM 전술 롤 아키타입 & 선호 플레이 (Player Traits / PPM) — 약 35종 분기
    # =========================================================================
    traits = []
    if is_gk:
        if gk_prev >= 2.5: traits.append("🧤 동물적인 반사신경 & 슈퍼세이브형 수문장 (Shot-Stopper)")
        elif gk_prev >= 1.0: traits.append("🧤 안정적인 선방 위치선정 및 골문 방어")
        if gk_claims >= 16: traits.append("🗼 크로스 및 공중볼 직접 처리 선호 (박스 지배자)")
        if gk_cs >= 12: traits.append("🧱 수비 라인 통솔 및 클린시트 메이커")
        if pass_pct >= 82.0: traits.append("📐 후방 빌드업에 적극 관여하는 스위퍼 키퍼 (Sweeper Keeper)")
        if gk_errors == 0 and mins >= 1800: traits.append("🛡️ 잔실수가 없는 침착한 핸들링 및 안정감")
        if not traits: traits.append("🧤 기본기에 충실한 클래식 골키퍼")
    elif is_st:
        if p90_g >= 0.45 and p90_chances >= 1.2 and aerial_pct >= 58.0:
            traits.append("👑 연계·제공권·마무리를 겸비한 만능형 스트라이커 (Complete Forward)")
        elif p90_box >= 5.0 and p90_chances < 1.0 and goals >= 10:
            traits.append("🦊 박스 안 위치선정 및 원터치 피니시 특화 (포처 / Poacher)")
        elif p90_chances >= 1.4 or p90_xa >= 0.18:
            traits.append("🔗 2선으로 내려와 공격을 연결하는 연계형 포워드 (Deep-Lying Forward)")
        elif aerial_pct >= 62.0:
            traits.append("🗼 포스트 플레이 및 공중볼 경합을 즐기는 타겟맨 (Target Forward)")
        elif p90_drib >= 1.1 and p90_box >= 4.0:
            traits.append("⚡ 뒷공간 침투 및 드리블 돌파를 즐기는 전진형 포워드 (Advanced Forward)")
        if goals >= 8 and xg > 0 and (goals / xg) >= 1.15:
            traits.append("🎯 골키퍼와의 1대1에서 침착한 구석 마무리 선호")
        if p90_shots >= 3.2:
            traits.append("🚀 거리와 각도를 가리지 않는 과감한 슈팅 시도")
        if p90_tkl >= 0.8 or duels_pct >= 55.0:
            traits.append("🐕 최전방에서 상대 수비진을 괴롭히는 압박형 포워드")
    elif is_wg_cam:
        if p90_shots >= 2.3 and p90_box >= 4.2:
            traits.append("🏹 측면에서 중앙으로 접고 들어와 직접 득점 노림 (인사이드 포워드)")
        elif p90_xa >= 0.25 or p90_chances >= 2.0:
            traits.append("🎩 창의적인 스루패스로 수비 라인을 허무는 플레이메이커 (AP)")
        elif p90_drib >= 1.8 and p90_shots < 2.0:
            traits.append("⚡ 터치라인을 따라 폭발적인 드리블 돌파 후 컷백/크로스 선호 (클래식 윙어)")
        elif p90_box >= 4.5 and goals >= 8:
            traits.append("👻 하프스페이스 빈 공간을 찾아 침투하는 섀도우 스트라이커 (라움도이터)")
        if p90_drib >= 1.5:
            traits.append("🏃‍♂️ 1대1 대인 돌파를 자주 시도하며 파울을 유도함")
        if bc_ratio >= 22.0 and big_chances >= 5:
            traits.append("🔑 결정적 1대1 빅찬스를 창출하는 킬패스 선호")
        if pass_pct >= 88.0:
            traits.append("📐 좁은 공간에서 볼을 잃지 않는 탈압박 및 볼 키핑")
    elif is_cm_cdm:
        if pass_pct >= 89.5 and p90_chances >= 1.2 and p90_box < 2.0:
            traits.append("🎼 3선 후방에서 장단패스로 경기 템포를 조율하는 사령관 (레지스타 / DLP)")
        elif p90_tkl >= 1.8 and p90_box >= 2.0:
            traits.append("🔋 공수 양면 박스부터 박스까지 종횡무진하는 활동량 (Box-to-Box)")
        elif p90_tkl >= 2.0 and duels_pct >= 60.0 and p90_box < 1.5:
            traits.append("🛡️ 포백 앞을 철저히 보호하고 상대 맥을 끊는 앵커맨 (Ball-Winning Midfielder)")
        elif p90_chances >= 1.5 and p90_drib >= 1.0:
            traits.append("⚡ 중원 하프스페이스를 파고들며 공격을 전개하는 메짤라 (Mezzala)")
        if pass_pct >= 90.0:
            traits.append("📐 위험 부담 없는 안전한 볼 순환 및 점유율 유지 선호")
        if duels_avg >= 62.0:
            traits.append("🧱 중원 몸싸움과 세컨드볼 경합에 적극적으로 뛰어듦")
    elif is_fb:
        if p90_chances >= 1.3 or p90_xa >= 0.15 or p90_drib >= 1.2:
            traits.append("⚡ 과감한 오버래핑으로 측면 공격 숫자를 늘리는 공격형 풀백/윙백")
        elif pass_pct >= 88.0 and p90_tkl >= 1.4:
            traits.append("🧠 중앙으로 좁혀 들어와 3선 빌드업을 돕는 인버티드 풀백 (Inverted FB)")
        elif duels_pct >= 62.0 and p90_tkl >= 1.8:
            traits.append("🔒 상대 윙어와의 1대1 측면 수비 봉쇄에 집중하는 수비형 풀백")
        if p90_box >= 1.8:
            traits.append("🏃‍♂️ 상대 페널티 박스 근처까지 깊숙이 언더래핑 침투 시도")
    elif is_cb:
        if pass_pct >= 89.5 and duels_pct >= 60.0:
            traits.append("📐 정교한 전진 패스로 후방 빌드업의 시발점이 되는 볼 플레잉 디펜더 (BPD)")
        elif aerial_pct >= 66.0 and p90_tkl >= 1.4:
            traits.append("🧱 압도적 제공권과 거친 대인 방어로 상대를 제압하는 파이터형 스토퍼")
        elif duels_pct >= 64.0 and pass_pct >= 87.0:
            traits.append("🛡️ 빠른 커버 플레이와 침착한 라인 컨트롤을 겸비한 커맨더형 센터백")
        if aerial_pct >= 68.0 and goals >= 2:
            traits.append("🗼 공격 세트피스(코너킥) 상황에서 위협적인 헤더 타겟")

    if "만능" in vers_str:
        traits.append("🔄 경기 중 전술 변화에 맞춰 3개 이상 포지션 스위칭 가능")
    elif "듀얼" in vers_str:
        traits.append("🔄 주 포지션과 서브 포지션을 오가는 멀티 롤 소화")
    if pk_goals >= 3:
        traits.append(f"🎯 팀 내 전담 페널티킥(PK) 키커 수행 ({pk_goals}골 성공)")
    if not traits:
        traits.append("⚖️ 감독의 전술적 지시를 충실히 수행하는 팀 플레이어")

    # =========================================================================
    # 2) FM 스카우팅 핵심 강점 (PROS) — 약 30종 분기
    # =========================================================================
    pros = []
    if rating >= 7.40: pros.append(f"직전 시즌 리그 최정상급(월드클래스급) 퍼포먼스 입증 (★{rating:.2f})")
    elif rating >= 7.18: pros.append(f"직전 시즌 상위권 주전으로서 뛰어난 경기 영향력 발휘 (★{rating:.2f})")
    elif rating >= 7.02: pros.append(f"기복 없이 안정적인 시즌 평균 평점 유지 (★{rating:.2f})")

    if is_gk:
        if gk_prev >= 2.5: pros.append(f"패배를 승점으로 바꾸는 엘리트급 선방 능력 (기대실점 대비 {gk_prev:+.2f}골 차단)")
        elif gk_prev >= 1.0: pros.append(f"기대 실점보다 적은 실점을 허용하는 안정적 방어력 ({gk_prev:+.2f}골 차단)")
        if gk_cs >= 12: pros.append(f"검증된 무실점 경기 조율 능력 (시즌 클린시트 {gk_cs}회)")
        if gk_claims >= 15: pros.append(f"골문 앞 공중볼 크로스 직접 차단 능력 우수 (공중볼 처리 {gk_claims}회)")
        if gk_errors == 0 and mins >= 1500: pros.append("시즌 내내 실점으로 직결된 치명적 실책(Error) 0회 기록")
    elif is_def_mid:
        if duels_pct >= 63.0 and aerial_pct >= 63.0:
            pros.append(f"지상({duels_pct:.1f}%)과 공중({aerial_pct:.1f}%) 모두 빈틈없는 완성형 경합 지배력")
        elif duels_pct >= 63.0:
            pros.append(f"1대1 지상 대인 방어 및 발밑 경합에서 매우 강한 면모 ({duels_pct:.1f}%)")
        elif aerial_pct >= 64.0:
            pros.append(f"세트피스 수비 및 롱볼 대응에 탁월한 공중볼 장악력 ({aerial_pct:.1f}%)")
        if pass_pct >= 90.0:
            pros.append(f"상대 압박 속에서도 흔들리지 않는 최상위권 패스 성공률 ({pass_pct:.1f}%)")
        elif pass_pct >= 87.0:
            pros.append(f"후방에서 안정적으로 볼을 배급하는 빌드업 정확도 ({pass_pct:.1f}%)")
        if p90_tkl >= 1.8:
            pros.append(f"왕성한 수비 범위와 뛰어난 볼 탈취 생산성 (90분당 태클 {p90_tkl:.2f}회)")
        if goals + assists >= 5:
            pros.append(f"수비/중원 자원임에도 쏠쏠한 공격 포인트 생산 가담 ({goals}골 {assists}도움)")
    else:
        if p90_xg_xa >= 0.65:
            pros.append(f"유럽 정상급 기대 공격포인트 생산력 (90분당 xG+xA {p90_xg_xa:.2f})")
        elif p90_xg_xa >= 0.45:
            pros.append(f"주전 공격 자원으로서 준수한 기회 생산성 (90분당 xG+xA {p90_xg_xa:.2f})")
        if goals >= 6 and xg > 0 and (goals / xg) >= 1.15:
            pros.append(f"기대득점(xG {xg:.1f})을 뛰어넘는 순도 높은 결정력 (실제 {goals}골)")
        if pk_goals == 0 and goals >= 8:
            pros.append(f"페널티킥(PK) 없이 100% 오픈플레이로만 만들어낸 순수 {goals}골 기록")
        if sot_ratio >= 48.0 and shots >= 25:
            pros.append(f"난사 없이 골문 안으로 꽂아 넣는 뛰어난 슈팅 영점 조준 (유효슈팅률 {sot_ratio:.1f}%)")
        if big_chances >= 8 or (p90_chances >= 1.6):
            pros.append(f"동료에게 결정적 1대1 찬스를 열어주는 기회 창출 능력 (기회창출 {chances}회 · 빅찬스 {big_chances}회)")
        if p90_drib >= 1.5:
            pros.append(f"밀집 수비를 균열내는 개인 전술 및 드리블 돌파력 (성공 {dribbles}회)")

    if start_ratio >= 85.0 and mins >= 2300:
        pros.append(f"직전 소속팀에서 검증된 붙박이 주전 신뢰도 및 풀타임 체력 ({mins:,}분 · 선발률 {start_ratio:.0f}%)")
    elif "철강왕" in inj_str:
        pros.append("최근 2년간 부상 공백이 거의 없는 뛰어난 메디컬 내구성 (철강왕)")
    if overpay_pct <= -8.0:
        pros.append(f"모델 산출 적정가 대비 매우 유리한 조건에 타결된 가성비 딜 ({overpay_pct:.1f}%)")
    elif abs(overpay_pct) <= 5.0:
        pros.append("거품 없는 합리적 시장 적정가 수준에서 성사된 영입")
    if "UCL" in stage_str:
        pros.append("챔피언스리그(UCL) 토너먼트 및 메이저 A매치 큰 무대 검증 완료")
    if "홈그로운" in reg_str or "유스" in reg_str:
        pros.append("구단 스쿼드 등록 및 엔트리 운영에 필수적인 홈그로운(HG) 프리미엄 보유")
    if age <= 22:
        pros.append(f"성장 포텐셜이 열려 있으며 향후 재판매(Resale) 가치 상승이 기대되는 연령대 (만 {age}세)")
    elif 24 <= age <= 27:
        pros.append(f"신체 능력과 경험이 정점에 달하는 전성기(Peak Age) 구간 진입 (만 {age}세)")

    if not pros:
        pros.append("팀 전술 운용 및 스쿼드 뎁스 강화에 즉시 활용 가능한 자원")

    # =========================================================================
    # 3) FM 스카우팅 약점 및 리스크 (CONS) — 약 25종 분기
    # =========================================================================
    cons = []
    if overpay_pct >= 20.0:
        cons.append(f"적정 가치 대비 과도한 오버페이 지출로 인한 재정적 부담 (+{overpay_pct:.1f}%)")
    elif overpay_pct >= 10.0:
        cons.append(f"셀링 클럽의 협상 우위로 인해 적정가 대비 다소 높은 프리미엄 지불 (+{overpay_pct:.1f}%)")

    if "장기 부상" in inj_str:
        cons.append("최근 2년 내 장기 부상 이력이 존재하여 철저한 메디컬 및 출전 시간 관리가 필수적임")
    elif "잔부상" in inj_str:
        cons.append("시즌 중 간헐적인 근육/잔부상 결장 패턴이 있어 로테이션 백업 대비 필요")

    if age >= 31:
        cons.append(f"에이징 커브 하락세 진입 구간으로 계약 만료 시 이적료 회수(리세일)가 사실상 어려움 (만 {age}세)")
    elif age >= 29 and not is_gk and not is_cb:
        cons.append(f"기동력이 요구되는 포지션 특성상 2~3년 내 에이징 커브 도래 가능성 염두 (만 {age}세)")

    if league_w <= 0.70:
        cons.append("원소속 리그와의 템포·피지컬 격차가 커서 빅리그 압박 속도에 적응할 시간이 필요함")
    elif league_w <= 0.80:
        cons.append("상위 빅리그 스텝업에 따른 초기 공수 전환 템포 적응 변수 존재")

    if is_gk:
        if gk_errors >= 2:
            cons.append(f"간헐적으로 실점으로 직결되는 치명적인 미스 노출 이력 (골 실수 {gk_errors}회)")
        if gk_prev < -1.0:
            cons.append(f"기대 실점 대비 실제 실점이 많아 선방 안정감 개선 필요 ({gk_prev:+.2f})")
    elif is_def_mid:
        if duels_pct >= 60.0 and aerial_pct < 52.0:
            cons.append(f"지상 수비는 준수하나 공중볼 경합({aerial_pct:.1f}%)에서 약점을 보여 타겟맨 상대 시 주의 필요")
        elif aerial_pct >= 60.0 and duels_pct < 52.0:
            cons.append(f"제공권은 좋으나 발 빠른 드리블러 상대 지상 1대1 경합({duels_pct:.1f}%)에서 고전 경향")
        elif duels_avg < 51.0:
            cons.append(f"거친 중원·수비 몸싸움 및 대인 경합 승률 보완 필요 (평균 {duels_avg:.1f}%)")
        if pass_pct < 80.0:
            cons.append(f"강한 전방 압박을 받을 때 후방 패스 미스 리스크 존재 (패스 성공률 {pass_pct:.1f}%)")
    else:
        if xg >= 5.0 and (goals / xg) < 0.78:
            cons.append(f"좋은 위치선정으로 찬스(xG {xg:.1f})는 많이 잡으나 마무리 골 결정력({goals}골)에서 아쉬움 노출")
        if shots >= 35 and sot_ratio < 32.0:
            cons.append(f"슈팅 볼륨({shots}회) 대비 유효슈팅 연결 비율({sot_ratio:.1f}%)이 낮아 영점 조준 개선 필요")
        if pk_share >= 35.0 and pk_goals >= 4:
            cons.append(f"전체 득점({goals}골) 중 페널티킥 비중({pk_goals}골, {pk_share:.0f}%)이 높아 오픈플레이 득점력 검증 필요")
        if duels_avg < 45.0:
            cons.append(f"상대 수비수의 강한 피지컬 견제 시 볼 간수 및 경합 열세 ({duels_avg:.1f}%)")

    if mins < 1400:
        cons.append(f"직전 시즌 실전 출전 시간({mins:,}분)이 적어 풀타임 경기 감각 및 체력 검증 필요")
    elif start_ratio < 60.0 and matches >= 15:
        cons.append(f"붙박이 선발보다는 교체/로테이션 비중(선발률 {start_ratio:.0f}%)이 높았던 이력")

    if "비EU" in reg_str:
        cons.append("구단 내 제한된 비EU(Non-EU) 외국인 등록 쿼터를 1장 소모함")
    if "패닉바이" in urg_str:
        cons.append("구단의 급박한 상황에서 추진된 영입으로 오버페이 및 전술 융화 리스크 내포")

    if not cons:
        cons.append("스탯과 계약 조건 모두 뚜렷한 결격 사유가 없는 로우 리스크(Low-Risk) 영입")

    return traits[:4], pros[:4], cons[:3]


def build_svg_donut_ring(score, max_score=10.0, color="#10B981", sub_label="DEAL SCORE", size=112):
    r = 44
    c = 2 * math.pi * r
    pct = max(0.0, min(1.0, score / max_score)) if max_score > 0 else 0.0
    dash = pct * c
    val_disp = f"★{score:.2f}" if max_score == 10.0 else f"{score:.1f}%"
    clean_col_id = color.replace("#", "")
    return f"""
    <svg width="{size}" height="{size}" viewBox="0 0 110 110" style="display:block; margin:0 auto; overflow:visible;">
        <defs>
            <filter id="ringGlow_{clean_col_id}" x="-20%" y="-20%" width="140%" height="140%">
                <feDropShadow dx="0" dy="0" stdDeviation="3.5" flood-color="{color}" flood-opacity="0.65"/>
            </filter>
        </defs>
        <circle cx="55" cy="55" r="{r}" fill="rgba(15,23,42,0.85)" stroke="#1E293B" stroke-width="8"/>
        <circle cx="55" cy="55" r="{r}" fill="none" stroke="{color}" stroke-width="8"
                stroke-linecap="round" stroke-dasharray="{dash:.1f} {c:.1f}"
                transform="rotate(-90 55 55)" filter="url(#ringGlow_{clean_col_id})"/>
        <text x="55" y="49" text-anchor="middle" fill="#FFFFFF" font-size="20" font-weight="900" font-family="Pretendard, sans-serif">{val_disp}</text>
        <text x="55" y="68" text-anchor="middle" fill="{color}" font-size="9.5" font-weight="800" letter-spacing="0.5">{sub_label}</text>
    </svg>
    """

def build_svg_radar(labels, values_a, color_a="#38BDF8", values_b=None, color_b="#F97316", size=335):
    cx, cy = size / 2, size / 2
    max_r = size * 0.285
    n = len(labels)
    bg_circles = f'<circle cx="{cx}" cy="{cy}" r="{max_r}" fill="rgba(15, 23, 42, 0.75)" stroke="#1E293B" stroke-width="1.5"/>'

    grid_svg = ""
    for idx_l, level in enumerate([0.25, 0.50, 0.75, 1.0]):
        r = max_r * level
        pts = []
        for i in range(n):
            ang = -math.pi / 2 + i * (2 * math.pi / n)
            pts.append(f"{cx + r * math.cos(ang):.1f},{cy + r * math.sin(ang):.1f}")
        stroke_col = "#334155" if level < 1.0 else "#475569"
        fill_col = "rgba(30, 41, 59, 0.22)" if idx_l % 2 == 0 else "none"
        dash_attr = "3,3" if level < 1.0 else "none"
        grid_svg += f'<polygon points="{" ".join(pts)}" fill="{fill_col}" stroke="{stroke_col}" stroke-width="1.2" stroke-dasharray="{dash_attr}"/>'

    axes_svg = ""
    for i in range(n):
        ang = -math.pi / 2 + i * (2 * math.pi / n)
        x2 = cx + max_r * math.cos(ang)
        y2 = cy + max_r * math.sin(ang)
        axes_svg += f'<line x1="{cx}" y1="{cy}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="#334155" stroke-width="1.2"/>'

    defs_svg = f"""
    <defs>
        <filter id="radarGlowA" x="-20%" y="-20%" width="140%" height="140%">
            <feDropShadow dx="0" dy="2" stdDeviation="4" flood-color="{color_a}" flood-opacity="0.55"/>
        </filter>
        <linearGradient id="gradPolyA" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="{color_a}" stop-opacity="0.52"/>
            <stop offset="100%" stop-color="{color_a}" stop-opacity="0.18"/>
        </linearGradient>
        <linearGradient id="gradPolyB" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="{color_b}" stop-opacity="0.48"/>
            <stop offset="100%" stop-color="{color_b}" stop-opacity="0.15"/>
        </linearGradient>
    </defs>
    """

    def make_poly(vals, stroke_c, grad_id, use_glow=False):
        pts = []
        dots = ""
        for i, v in enumerate(vals):
            ang = -math.pi / 2 + i * (2 * math.pi / n)
            norm = max(0.15, min(1.0, (v - 40) / 60.0))
            r = max_r * norm
            px = cx + r * math.cos(ang)
            py = cy + r * math.sin(ang)
            pts.append(f"{px:.1f},{py:.1f}")
            dots += (
                f'<circle cx="{px:.1f}" cy="{py:.1f}" r="6.5" fill="{stroke_c}" fill-opacity="0.3"/>'
                f'<circle cx="{px:.1f}" cy="{py:.1f}" r="4" fill="#FFFFFF" stroke="{stroke_c}" stroke-width="2.5"/>'
            )
        flt = 'filter="url(#radarGlowA)"' if use_glow else ''
        poly = f'<polygon points="{" ".join(pts)}" fill="url(#{grad_id})" stroke="{stroke_c}" stroke-width="2.8" {flt}/>'
        return poly + dots

    poly_svg = make_poly(values_a, color_a, "gradPolyA", use_glow=True)
    if values_b is not None:
        poly_svg += make_poly(values_b, color_b, "gradPolyB", use_glow=False)

    labels_svg = ""
    for i, lbl in enumerate(labels):
        ang = -math.pi / 2 + i * (2 * math.pi / n)
        lr = max_r + 39
        lx = cx + lr * math.cos(ang)
        ly = cy + lr * math.sin(ang)
        val_txt = f"{values_a[i]}점" if values_b is None else f"A:{values_a[i]} · B:{values_b[i]}"
        badge_w = 54 if values_b is None else 78
        badge_col = color_a if values_b is None else "#FBBF24"
        labels_svg += (
            f'<text x="{lx:.1f}" y="{ly - 9:.1f}" fill="#F8FAFC" font-size="11.5" font-weight="800" text-anchor="middle" dominant-baseline="central">{lbl}</text>'
            f'<rect x="{lx - badge_w/2:.1f}" y="{ly + 1:.1f}" width="{badge_w}" height="17" rx="8.5" fill="#0F172A" stroke="{badge_col}" stroke-width="1.2"/>'
            f'<text x="{lx:.1f}" y="{ly + 9.5:.1f}" fill="{badge_col}" font-size="10.5" font-weight="900" text-anchor="middle" dominant-baseline="central">{val_txt}</text>'
        )

    return f'<svg viewBox="0 0 {size} {size}" width="100%" height="{size}px" style="overflow:visible; display:block; margin:0 auto;">{defs_svg}{bg_circles}{grid_svg}{axes_svg}{poly_svg}{labels_svg}</svg>'


def build_tactical_pitch_html(team_in_df):
    zones = {"ST": [], "WG": [], "CM": [], "FB": [], "CB": [], "GK": []}
    if not team_in_df.empty:
        for _, r in team_in_df.iterrows():
            p_name = str(r.get("선수명", ""))
            p_pos = str(r.get("포지션", ""))
            p_fee = float(r.get("실제이적료(만€)", 0))
            p_sc = float(r.get("이적평점", 7.5))
            chip = (
                f"<div style='background:rgba(9,13,22,0.92); border:1.5px solid #38BDF8; border-radius:8px; "
                f"padding:4px 9px; margin:3px; display:inline-block; text-align:center; box-shadow:0 4px 10px rgba(0,0,0,0.5);'>"
                f"<div style='font-size:12px; font-weight:900; color:#FFFFFF;'>{p_name}</div>"
                f"<div style='font-size:10px; color:#34D399; font-weight:700;'>€{p_fee:,.0f}만 · ★{p_sc:.2f}</div></div>"
            )
            if any(k in p_pos for k in ["스트라이커", "센터포워드", "ST", "CF"]):
                zones["ST"].append(chip)
            elif any(k in p_pos for k in ["윙어", "공격형", "WG", "CAM"]):
                zones["WG"].append(chip)
            elif any(k in p_pos for k in ["중앙", "수비형", "미드필더", "CM", "CDM"]):
                zones["CM"].append(chip)
            elif any(k in p_pos for k in ["풀백", "윙백", "RB", "LB", "WB"]):
                zones["FB"].append(chip)
            elif any(k in p_pos for k in ["골키퍼", "GK"]):
                zones["GK"].append(chip)
            else:
                zones["CB"].append(chip)

    def z_html(key, label):
        items = "".join(zones[key]) if zones[key] else f"<span style='font-size:11px; color:rgba(255,255,255,0.35);'>{label} 영입 없음</span>"
        return f"<div style='text-align:center; padding:6px;'><div style='font-size:10px; font-weight:800; color:#A7F3D0; letter-spacing:0.5px; margin-bottom:2px;'>[{label}]</div>{items}</div>"

    return f"""
    <div style="background:linear-gradient(180deg, #064E3B 0%, #047857 50%, #064E3B 100%); border:2px solid rgba(255,255,255,0.45); border-radius:14px; padding:14px; position:relative; box-shadow:inset 0 0 30px rgba(0,0,0,0.45);">
        <div style="border:1.5px solid rgba(255,255,255,0.28); border-radius:10px; padding:10px;">
            {z_html("ST", "ST / CF 최전방 스트라이커")}
            <hr style="border:0; border-top:1px dashed rgba(255,255,255,0.22); margin:6px 0;">
            {z_html("WG", "WG / CAM 2선 윙어 · 공격형 미드필더")}
            <hr style="border:0; border-top:1.5px solid rgba(255,255,255,0.35); margin:8px 0;">
            {z_html("CM", "CM / CDM 3선 중원 · 수비형 미드필더")}
            <hr style="border:0; border-top:1px dashed rgba(255,255,255,0.22); margin:6px 0;">
            <div style="display:grid; grid-template-columns:1fr 1fr; gap:8px;">
                {z_html("FB", "RB / LB / WB 측면 풀백·윙백")}
                {z_html("CB", "CB 중앙 센터백")}
            </div>
            <hr style="border:0; border-top:1px dashed rgba(255,255,255,0.22); margin:6px 0;">
            {z_html("GK", "GK 골키퍼")}
        </div>
    </div>
    """


def render_copyable_infographic(card_inner_html, filename="scouting_infographic", height=880):
    full_doc = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="utf-8">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
    <style>
        @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
        * {{
            box-sizing: border-box;
            font-family: 'Pretendard', 'Malgun Gothic', -apple-system, BlinkMacSystemFont, sans-serif;
            word-break: keep-all;
            overflow-wrap: break-word;
            -webkit-font-smoothing: antialiased;
        }}
        body {{ margin: 0; padding: 6px; background: transparent; color: #F8FAFC; }}
        .top-action-bar {{
            display: flex; gap: 10px; margin-bottom: 14px;
            background: linear-gradient(90deg, #090D16 0%, #1E293B 100%);
            padding: 10px 14px; border-radius: 14px;
            border: 1px solid rgba(56, 189, 248, 0.5);
            align-items: center; justify-content: space-between;
            box-shadow: 0 8px 20px rgba(0,0,0,0.45);
        }}
        .btn-copy-img {{
            flex: 1;
            background: linear-gradient(135deg, #0284C7 0%, #2563EB 50%, #4F46E5 100%);
            color: #FFFFFF; border: 1px solid rgba(125, 211, 252, 0.6);
            padding: 13px 20px; border-radius: 10px;
            font-size: 14.5px; font-weight: 800; cursor: pointer;
            transition: all 0.2s ease; text-align: center;
            box-shadow: 0 4px 15px rgba(37, 99, 235, 0.45);
        }}
        .btn-copy-img:hover {{ filter: brightness(1.12); transform: translateY(-1px); }}
        .btn-save-img {{
            background: rgba(30, 41, 59, 0.9); color: #E2E8F0;
            border: 1px solid #475569; padding: 13px 18px;
            border-radius: 10px; font-size: 13.5px; font-weight: 700; cursor: pointer;
        }}
        .btn-save-img:hover {{ background: #334155; color: #FFFFFF; }}
        #capture-board {{
            position: relative; background-color: #060911;
            background-image: 
                radial-gradient(at 0% 0%, rgba(56, 189, 248, 0.14) 0px, transparent 45%),
                radial-gradient(at 100% 0%, rgba(168, 85, 247, 0.12) 0px, transparent 45%),
                radial-gradient(at 50% 100%, rgba(16, 185, 129, 0.10) 0px, transparent 50%),
                radial-gradient(rgba(255, 255, 255, 0.045) 1px, transparent 1px);
            background-size: 100% 100%, 100% 100%, 100% 100%, 20px 20px;
            border: 1.5px solid rgba(148, 163, 184, 0.25);
            border-radius: 22px; padding: 26px;
            box-shadow: 0 22px 48px rgba(0, 0, 0, 0.7); overflow: hidden;
        }}
        .glass-panel {{
            background: rgba(15, 23, 42, 0.78); backdrop-filter: blur(12px);
            border: 1px solid rgba(148, 163, 184, 0.16); border-radius: 16px;
            box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.08);
        }}
        .kpi-card {{
            background: linear-gradient(180deg, rgba(30, 41, 59, 0.55) 0%, rgba(15, 23, 42, 0.85) 100%);
            border: 1px solid rgba(148, 163, 184, 0.2); border-radius: 14px;
            padding: 14px 12px; text-align: center; box-shadow: 0 6px 16px rgba(0,0,0,0.25);
        }}
        .brand-footer {{
            margin-top: 16px; padding-top: 10px;
            border-top: 1px solid rgba(148, 163, 184, 0.14);
            display: flex; justify-content: space-between; align-items: center;
            font-size: 10.5px; color: #64748B; font-weight: 600; letter-spacing: 0.4px;
        }}
    </style>
    </head>
    <body>
        <div class="top-action-bar">
            <button id="copyBtn" class="btn-copy-img" onclick="copyBoardAsImage()">
                📸 블로그 / 카페용 초고화질 인포그래픽 이미지 한 번에 복사하기 (클릭 후 Ctrl+V 붙여넣기)
            </button>
            <button class="btn-save-img" onclick="downloadBoardAsPNG()">
                💾 고해상도 PNG 저장
            </button>
        </div>
        <div id="capture-board">
            {card_inner_html}
            <div class="brand-footer">
                <span>⚽ PRO FOOTBALL SCOUTING & VALUATION ANALYTICS (FM EDITION)</span>
                <span>DATA SOURCE: TRANSFERMARKT · FOTMOB · 12-FACTOR PROPRIETARY MODEL</span>
            </div>
        </div>
        <script>
        async function copyBoardAsImage() {{
            const btn = document.getElementById('copyBtn');
            const origText = btn.innerHTML;
            btn.innerHTML = '⏳ 3배율(Ultra-HD) 고화질 그래픽 이미지를 생성하여 클립보드에 복사 중입니다...';
            btn.style.background = '#059669';
            try {{
                const el = document.getElementById('capture-board');
                const canvas = await html2canvas(el, {{ scale: 3.0, backgroundColor: '#060911', useCORS: true, logging: false }});
                canvas.toBlob(async function(blob) {{
                    try {{
                        const item = new ClipboardItem({{ 'image/png': blob }});
                        await navigator.clipboard.write([item]);
                        btn.innerHTML = '✅ 초고화질 이미지 복사 완료! 지금 블로그/카페 글쓰기 창에 붙여넣기(Ctrl+V) 하세요!';
                        btn.style.background = '#10B981';
                        setTimeout(() => {{ btn.innerHTML = origText; btn.style.background = 'linear-gradient(135deg, #0284C7 0%, #2563EB 50%, #4F46E5 100%)'; }}, 4000);
                    }} catch (err) {{
                        const link = document.createElement('a');
                        link.download = '{filename}.png';
                        link.href = canvas.toDataURL('image/png');
                        link.click();
                        btn.innerHTML = '📥 브라우저 보안 정책으로 인해 초고화질 PNG 파일로 즉시 다운로드되었습니다!';
                        setTimeout(() => {{ btn.innerHTML = origText; btn.style.background = 'linear-gradient(135deg, #0284C7 0%, #2563EB 50%, #4F46E5 100%)'; }}, 4000);
                    }}
                }}, 'image/png');
            }} catch (e) {{
                btn.innerHTML = '⚠️ 복사 오류: 우측 고해상도 PNG 저장 버튼을 눌러주세요.';
            }}
        }}
        async function downloadBoardAsPNG() {{
            const el = document.getElementById('capture-board');
            const canvas = await html2canvas(el, {{ scale: 3.0, backgroundColor: '#060911', useCORS: true, logging: false }});
            const link = document.createElement('a');
            link.download = '{filename}.png';
            link.href = canvas.toDataURL('image/png');
            link.click();
        }}
        </script>
    </body>
    </html>
    """
    components.html(full_doc, height=height, scrolling=True)


# 사이드바: 실시간 환율 설정 + 구단 로고 사전 관리/수정 + 영국/국내 금액 변환기
with st.sidebar:
    st.markdown("### 💱 실시간 환율 기준 설정")
    st.caption("이적시장 시점의 실제 환율에 맞게 조정할 수 있습니다.")
    rate_krw = st.number_input("1 유로(€) 당 원화(₩) 환율", min_value=1000, max_value=2500, value=1500, step=10, key="sb_rate_krw")
    rate_gbp = st.number_input("1 유로(€) 당 파운드(£) 환율", min_value=0.50, max_value=1.20, value=0.86, step=0.01, format="%.2f", key="sb_rate_gbp")

    st.markdown("---")
    st.markdown("### 🛡️ 구단 로고 사전 조회 & 수정")
    st.caption(f"구글 드라이브 폴더 자동 인식 구단: **{len(scanned_drive_logos)}개**")
    if st.button("🔄 드라이브 로고 폴더 새로고침", use_container_width=True, key="sb_refresh_drive_btn"):
        st.cache_data.clear()
        st.rerun()

    with st.expander("구단 로고 직접 확인 / 변경하기", expanded=False):
        known_clubs = sorted(list(st.session_state["custom_club_logos"].keys()))
        sel_club_edit = st.selectbox("등록된 구단 확인 (또는 아래에 직접 입력)", ["+ 새 구단 직접 입력"] + known_clubs, key="sb_logo_sel")
        target_club_key = st.text_input("구단명 입력", value="" if sel_club_edit == "+ 새 구단 직접 입력" else sel_club_edit, placeholder="예: 아스날", key="sb_logo_name")
        curr_logo_val = st.session_state["custom_club_logos"].get(target_club_key.strip(), "")
        new_logo_val = st.text_input("구단 로고 (구글 드라이브 공유 링크 등)", value=curr_logo_val, placeholder="https://drive.google.com/file/d/...", key="sb_logo_url")
        if curr_logo_val:
            preview_b64 = url_to_base64_img(curr_logo_val)
            if preview_b64:
                st.markdown(f"<div style='text-align:center; padding:6px; background:#0F172A; border-radius:8px;'><img src='{preview_b64}' style='height:48px; object-fit:contain;'/></div>", unsafe_allow_html=True)
        if st.button("💾 구단 로고 사전에 저장/수정", use_container_width=True, key="sb_logo_save_btn"):
            if target_club_key.strip() and new_logo_val.strip():
                st.session_state["custom_club_logos"][target_club_key.strip()] = new_logo_val.strip()
                st.cache_data.clear()
                st.success(f"✅ '{target_club_key.strip()}' 로고가 업데이트되었습니다!")
                st.rerun()

    st.markdown("---")
    st.markdown("### 🧮 영국/국내 보도 금액 변환기")
    conv_gbp_m = st.number_input("파운드 이적료 (£m, 백만 파운드)", min_value=0.0, value=0.0, step=1.0, key="sb_conv_gbp_m")
    if conv_gbp_m > 0:
        eur_man_from_gbp = int(round((conv_gbp_m * 100.0) / rate_gbp))
        st.info(f"➔ **`{eur_man_from_gbp:,}` 만 유로 (€)**")
        if st.button("실제 이적료 칸에 바로 적용", use_container_width=True, key="apply_gbp_fee"):
            if "current_form" in st.session_state:
                st.session_state["current_form"]["fee"] = eur_man_from_gbp
                st.session_state["form_key_id"] += 1
                st.rerun()

    conv_gbp_k = st.number_input("파운드 주급 (£k/주, 천 파운드)", min_value=0.0, value=0.0, step=5.0, key="sb_conv_gbp_k")
    if conv_gbp_k > 0:
        eur_man_wage_from_gbp = round((conv_gbp_k / 10.0) / rate_gbp, 1)
        st.info(f"➔ 주급 **`{eur_man_wage_from_gbp}` 만 유로 (€/주)**")
        if st.button("선수 주급 칸에 바로 적용", use_container_width=True, key="apply_gbp_wage"):
            if "current_form" in st.session_state:
                st.session_state["current_form"]["wage"] = eur_man_wage_from_gbp
                st.session_state["form_key_id"] += 1
                st.rerun()

    conv_krw_eok = st.number_input("원화 이적료 (억원)", min_value=0.0, value=0.0, step=10.0, key="sb_conv_krw")
    if conv_krw_eok > 0:
        eur_man_from_krw = int(round((conv_krw_eok * 100000000.0) / (rate_krw * 10000.0)))
        st.info(f"➔ **`{eur_man_from_krw:,}` 만 유로 (€)**")

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

def format_currency_desc(eur_man_euro):
    if eur_man_euro <= 0: return "₩0억 | £0만"
    total_eur = eur_man_euro * 10000
    krw_eok = (total_eur * rate_krw) / 100000000.0
    gbp_man = eur_man_euro * rate_gbp
    return f"약 {krw_eok:,.1f}억원 | £{gbp_man:,.1f}만"

def to_public_index(weight_val, min_w=0.65, max_w=1.08):
    norm = (weight_val - min_w) / (max_w - min_w) if max_w > min_w else 0.5
    return int(round(max(55, min(98, 60 + norm * 38))))

def find_val(row_dict, candidates, default=0):
    for c in candidates:
        for k in row_dict.keys():
            if c.lower() in k.lower().replace(" ", "").replace("_", ""):
                val = row_dict[k]
                if pd.notnull(val) and str(val).strip() not in ["", "nan", "None"]:
                    try:
                        return float(val) if isinstance(default, float) else int(float(val))
                    except:
                        return val
    return default

# 3. 메인 7개 탭 구성
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "💰 적정 이적료 평가", 
    "📱 FotMob 시즌 성적 & 이적 예측",
    "🔍 과거 유사 이적 사례 비교 (Comps)",
    "🎯 시즌 종료 최종 성적 & 모델 검증",
    "⏱️ 시즌 중 라운드별 중간 점검 (메모장)",
    "👥 과거 선수 대조 & 후보 A vs B 비교",
    "🏆 구단/리그별 결산 & 전술판 데이터룸"
])

# ================= TAB 1: 적정 이적료 평가 =================
with tab1:
    if st.session_state["last_saved_msg"]:
        st.success(st.session_state["last_saved_msg"])
        st.session_state["last_saved_msg"] = None

    default_form_template = {
        "name": "", "nat": "", "age": 28, "from_team": "", "to_team": "",
        "from_logo": "", "to_logo": "", "sub_pos_list": [],
        "tm": 4500, "fee": 5960, "wage": 0.0, "notes": "",
        "season": "26/27 여름 (Summer)",
        "pos": list(POSITION_WEIGHTS.keys())[4],
        "vers": list(VERSATILITY_WEIGHTS.keys())[0],
        "from_league": list(LEAGUE_WEIGHTS.keys())[0],
        "to_league": list(LEAGUE_WEIGHTS.keys())[0],
        "buying_tier": list(CLUB_TIERS.keys())[1],
        "contract": list(CONTRACT_WEIGHTS.keys())[2],
        "transfer_type": list(TRANSFER_TYPE_WEIGHTS.keys())[0],
        "trade_type": "🔵 영입 (IN)",
        "reg_status": list(REGISTRATION_WEIGHTS.keys())[1],
        "big_stage": list(BIG_STAGE_WEIGHTS.keys())[0],
        "injury": list(INJURY_WEIGHTS.keys())[1],
        "urgency": list(URGENCY_WEIGHTS.keys())[0]
    }

    if "current_form" not in st.session_state:
        st.session_state["current_form"] = default_form_template.copy()
    else:
        for k_def, v_def in default_form_template.items():
            if k_def not in st.session_state["current_form"]:
                st.session_state["current_form"][k_def] = v_def

    c_mode1, c_mode2 = st.columns([1, 1])
    with c_mode1:
        edit_toggle = st.toggle("✏️ 기존 저장된 선수 불러와서 수정/주급·로고 변경 모드", value=False)
    with c_mode2:
        ai_paste_toggle = st.toggle("🤖 제미나이(AI) 텍스트 ➔ 1초 자동 입력기 열기", value=False)

    if ai_paste_toggle:
        with st.expander("🤖 제미나이 데이터 한 번에 붙여넣기 (1·2번 탭 20여 개 항목 자동 입력)", expanded=True):
            st.caption("제미나이에게 아래 프롬프트를 복사해 질문한 뒤, 답변을 그대로 아래 칸에 붙여넣고 버튼을 누르세요!")
            st.code('Ezri Konsa 선수의 이적 및 직전 시즌 FotMob 스탯을 아래 JSON 형식으로만 출력해줘:\n{"name":"Ezri Konsa","nat":"잉글랜드","age":27,"from_team":"아스톤 빌라","to_team":"아스날","tm":4500,"fee":5500,"wage":12.0,"matches":35,"starts":35,"mins":3100,"rating":7.25,"goals":1,"xg":1.5,"assists":0,"xa":0.8,"shots":15,"sot":5,"chances":10,"dribbles":12,"touches_box":25,"tackles":45}', language="json")
            ai_raw_txt = st.text_area("제미나이 답변 붙여넣기 (JSON 형식)", height=100, key="ai_paste_area")
            if st.button("⚡ 1번 & 2번 탭에 1초 자동 채우기", type="primary", use_container_width=True):
                if ai_raw_txt.strip():
                    try:
                        json_match = re.search(r'\{.*\}', ai_raw_txt, re.DOTALL)
                        parsed = json.loads(json_match.group(0)) if json_match else {}
                        cf_now = st.session_state["current_form"]
                        for k_p in ["name", "nat", "from_team", "to_team", "from_logo", "to_logo"]:
                            if k_p in parsed: cf_now[k_p] = str(parsed[k_p])
                        for k_i in ["age", "tm", "fee"]:
                            if k_i in parsed: cf_now[k_i] = int(float(parsed[k_i]))
                        if "wage" in parsed: cf_now["wage"] = float(parsed["wage"])

                        stat_map = {
                            "matches": "f_matches", "starts": "f_starts", "mins": "f_mins", "rating": "f_rating",
                            "goals": "f_goals", "xg": "f_xg", "assists": "f_assists", "xa": "f_xa",
                            "shots": "f_shots", "sot": "f_sot", "chances": "f_chances",
                            "dribbles": "f_dribbles", "touches_box": "f_touches_box", "tackles": "f_tackles"
                        }
                        for s_k, st_k in stat_map.items():
                            if s_k in parsed:
                                st.session_state[st_k] = float(parsed[s_k]) if s_k in ["rating", "xg", "xa"] else int(float(parsed[s_k]))
                        st.session_state["form_key_id"] += 1
                        st.success("✅ 제미나이 데이터가 1·2번 탭에 완벽하게 자동 입력되었습니다!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"⚠️ 텍스트 형식 확인 필요: JSON 중괄호 형식으로 붙여넣어 주세요. ({e})")

    if edit_toggle:
        st.markdown("##### 🔍 불러올 선수 선택")
        if history_df.empty or "선수명" not in history_df.columns:
            st.warning("⚠️ 시트에 저장된 기존 데이터가 없습니다.")
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
                        row_raw = e_season_df[e_season_df["선수명"] == sel_e_player].iloc[-1]
                        rd = row_raw.to_dict()

                        pos_saved = str(rd.get("포지션", ""))
                        pos_match = next((p_k for p_k in POSITION_WEIGHTS.keys() if pos_saved and pos_saved in p_k), list(POSITION_WEIGHTS.keys())[4])
                        fl_saved = str(rd.get("원소속리그", ""))
                        from_l_match = next((l_k for l_k in LEAGUE_WEIGHTS.keys() if fl_saved and fl_saved in l_k), list(LEAGUE_WEIGHTS.keys())[0])
                        tl_saved = str(rd.get("이적팀리그", ""))
                        to_l_match = next((l_k for l_k in LEAGUE_WEIGHTS.keys() if tl_saved and tl_saved in l_k), list(LEAGUE_WEIGHTS.keys())[0])

                        notes_val = str(rd.get("스카우팅메모", ""))
                        saved_from_logo, saved_to_logo = extract_logos_from_notes(notes_val)
                        saved_sub_pos = extract_subpos_from_notes(notes_val)
                        cleaned_notes_val = clean_notes_display(notes_val)

                        tier_saved = str(rd.get("영입구단규모", ""))
                        tier_match = next((t_k for t_k in CLUB_TIERS.keys() if tier_saved and tier_saved in t_k), list(CLUB_TIERS.keys())[1])
                        contract_match = next((c_k for c_k in CONTRACT_WEIGHTS.keys() if c_k.split(" (")[0] in notes_val), list(CONTRACT_WEIGHTS.keys())[2])
                        tt_saved = str(rd.get("이적형태", ""))
                        ttype_match = next((tt_k for tt_k in TRANSFER_TYPE_WEIGHTS.keys() if tt_saved and tt_saved in tt_k), list(TRANSFER_TYPE_WEIGHTS.keys())[0])
                        reg_match = next((r_k for r_k in REGISTRATION_WEIGHTS.keys() if r_k.split(" (")[0] in notes_val), list(REGISTRATION_WEIGHTS.keys())[1])
                        urg_match = next((u_k for u_k in URGENCY_WEIGHTS.keys() if u_k.split(" (")[0] in notes_val), list(URGENCY_WEIGHTS.keys())[0])
                        vers_match = list(VERSATILITY_WEIGHTS.keys())[2] if len(saved_sub_pos) >= 2 else (list(VERSATILITY_WEIGHTS.keys())[1] if len(saved_sub_pos) == 1 else list(VERSATILITY_WEIGHTS.keys())[0])

                        st.session_state["current_form"] = {
                            "name": str(rd.get("선수명", "")),
                            "nat": str(rd.get("국적", "")),
                            "age": int(find_val(rd, ["나이"], 28)),
                            "from_team": str(rd.get("원소속팀명", "")),
                            "to_team": str(rd.get("이적팀명", "")),
                            "from_logo": saved_from_logo,
                            "to_logo": saved_to_logo,
                            "sub_pos_list": [sp for sp in SUB_POS_OPTIONS if sp in saved_sub_pos],
                            "tm": int(find_val(rd, ["시장가치", "tm"], 4500)),
                            "fee": int(find_val(rd, ["실제이적료", "이적료", "fee"], 0)),
                            "wage": float(find_val(rd, ["선수주급", "주급", "wage"], 0.0)),
                            "notes": cleaned_notes_val,
                            "season": sel_e_season,
                            "pos": pos_match,
                            "vers": vers_match,
                            "from_league": from_l_match,
                            "to_league": to_l_match,
                            "buying_tier": tier_match,
                            "contract": contract_match,
                            "transfer_type": ttype_match,
                            "trade_type": "🔴 방출 / 판매 (OUT)" if str(rd.get("거래구분", "")).strip() == "OUT" else "🔵 영입 (IN)",
                            "reg_status": reg_match,
                            "big_stage": list(BIG_STAGE_WEIGHTS.keys())[0],
                            "injury": list(INJURY_WEIGHTS.keys())[1],
                            "urgency": urg_match
                        }

                        st.session_state["f_matches"] = int(find_val(rd, ["이전_출전경기", "직전_경기수", "출전경기", "matches"], 28))
                        st.session_state["f_starts"] = int(find_val(rd, ["선발출전", "직전_선발", "선발", "starts"], 25))
                        st.session_state["f_mins"] = int(find_val(rd, ["이전_출전시간", "직전_출전시간", "출전시간", "mins"], 2206))
                        st.session_state["f_rating"] = float(find_val(rd, ["이전_FotMob평점", "직전_평점", "이전평점", "FotMob평점", "평점", "rating"], 7.32))
                        st.session_state["f_goals"] = int(find_val(rd, ["이전_골", "직전_골", "골", "goals"], 16))
                        st.session_state["f_xg"] = float(find_val(rd, ["이전_xg", "직전_xg", "xg"], 17.44))
                        st.session_state["f_shots"] = int(find_val(rd, ["이전_총슈팅", "직전_슈팅", "슈팅", "shots"], 88))
                        st.session_state["f_sot"] = int(find_val(rd, ["이전_유효슈팅", "직전_유효슈팅", "유효슈팅", "sot"], 43))
                        st.session_state["f_assists"] = int(find_val(rd, ["이전_도움", "직전_도움", "도움", "assists"], 4))
                        st.session_state["f_xa"] = float(find_val(rd, ["이전_xa", "직전_xa", "xa"], 3.33))
                        st.session_state["f_chances"] = int(find_val(rd, ["이전_찬스메이킹", "직전_기회창출", "기회창출", "chances"], 25))
                        st.session_state["f_dribbles"] = int(find_val(rd, ["이전_성공드리블", "직전_드리블", "드리블", "dribbles"], 14))
                        st.session_state["f_touches_box"] = int(find_val(rd, ["이전_박스터치", "직전_박스터치", "박스터치", "touches"], 153))
                        st.session_state["f_tackles"] = int(find_val(rd, ["이전_태클성공", "직전_태클", "태클", "tackles"], 24))
                        st.session_state["f_big_chances"] = int(find_val(rd, ["빅찬스메이킹", "big_chances"], 2))
                        st.session_state["f_pk"] = int(find_val(rd, ["pk득점", "pk", "penalties"], 0))
                        st.session_state["f_pass_pct"] = float(find_val(rd, ["패스성공률", "pass_pct"], 88.2))
                        st.session_state["f_duels_pct"] = float(find_val(rd, ["지상경합승률", "duels_pct"], 62.4))
                        st.session_state["f_aerial_pct"] = float(find_val(rd, ["공중볼승률", "aerial_pct"], 65.8))
                        st.session_state["f_gk_saves"] = int(find_val(rd, ["gk선방", "선방", "saves"], 0))
                        st.session_state["f_gk_conceded"] = int(find_val(rd, ["gk실점", "실점", "conceded"], 0))
                        st.session_state["f_gk_prevented"] = float(find_val(rd, ["gk득점차단", "득점차단", "prevented"], 0.0))
                        st.session_state["f_gk_cs"] = int(find_val(rd, ["gk클린시트", "클린시트", "cs"], 0))
                        st.session_state["f_gk_errors"] = int(find_val(rd, ["gk실수", "실수", "errors"], 0))
                        st.session_state["f_gk_claims"] = int(find_val(rd, ["gk공중볼", "공중볼", "claims"], 0))

                        st.session_state["form_key_id"] += 1
                        st.rerun()

    k_id = st.session_state["form_key_id"]
    cf = st.session_state["current_form"]

    st.markdown("---")
    trade_type_choice = st.radio("거래 유형 구분", ["🔵 영입 (IN)", "🔴 방출 / 판매 (OUT)"], index=0 if cf.get("trade_type", "🔵 영입 (IN)") == "🔵 영입 (IN)" else 1, horizontal=True, key=f"trade_type_{k_id}")
    is_out_trade = "방출" in trade_type_choice

    col1, col2 = st.columns([0.85, 1.25])

    with col1:
        st.subheader(f"📝 {'[수정 모드] ' if edit_toggle else ''}{'방출(OUT)' if is_out_trade else '영입(IN)'} 선수 & 계약 정보")
        c_s1, c_s2 = st.columns(2)
        with c_s1: 
            season_val = st.selectbox("이적 시즌 / 시장", ["26/27 여름 (Summer)", "26/27 겨울 (Winter)", "기타"], index=["26/27 여름 (Summer)", "26/27 겨울 (Winter)", "기타"].index(cf.get("season", "26/27 여름 (Summer)")) if cf.get("season", "") in ["26/27 여름 (Summer)", "26/27 겨울 (Winter)", "기타"] else 0, key=f"season_{k_id}")
        with c_s2: 
            transfer_type = st.selectbox("이적 형태 & 계약 조항", list(TRANSFER_TYPE_WEIGHTS.keys()), index=list(TRANSFER_TYPE_WEIGHTS.keys()).index(cf.get("transfer_type", list(TRANSFER_TYPE_WEIGHTS.keys())[0])) if cf.get("transfer_type", "") in TRANSFER_TYPE_WEIGHTS else 0, key=f"ttype_{k_id}")

        c_n1, c_n2, c_n3 = st.columns([2, 1, 1])
        with c_n1: player_name = st.text_input("선수 이름", value=cf.get("name", ""), placeholder="예: Ezri Konsa", key=f"name_{k_id}")
        with c_n2: player_nat = st.text_input("국적", value=cf.get("nat", ""), placeholder="예: 잉글랜드", key=f"nat_{k_id}")
        with c_n3: player_age = st.number_input("나이(만)", min_value=15, max_value=45, value=cf.get("age", 28), key=f"age_{k_id}")

        if not edit_toggle and player_name.strip() and not history_df.empty and "선수명" in history_df.columns:
            dup_matches = history_df[
                (history_df["선수명"].astype(str).str.strip().str.lower() == player_name.strip().lower()) & 
                (history_df["이적시즌"].astype(str).str.strip() == season_val.strip())
            ]
            if not dup_matches.empty:
                last_dup = dup_matches.iloc[-1]
                st.warning(f"⚠️ **중복 등록 알림**: **'{player_name.strip()}'** 선수는 이미 `{season_val}` 시즌에 등록된 내역이 있습니다! (`[{last_dup.get('원소속팀명', '미상')} ➔ {last_dup.get('이적팀명', '미상')}]`)")

        c_t1, c_t2, c_t3 = st.columns(3)
        with c_t1: in_from_team = st.text_input("원소속팀명 (보내는 팀)", value=cf.get("from_team", ""), placeholder="예: 뉴캐슬", key=f"from_team_{k_id}")
        with c_t2: in_to_team = st.text_input("이적팀명 (영입 구단)", value=cf.get("to_team", ""), placeholder="예: 아스날", key=f"to_team_{k_id}")
        with c_t3: in_to_league_choice = st.selectbox("이적팀 리그", list(LEAGUE_WEIGHTS.keys()), index=list(LEAGUE_WEIGHTS.keys()).index(cf.get("to_league", list(LEAGUE_WEIGHTS.keys())[0])) if cf.get("to_league", "") in LEAGUE_WEIGHTS else 0, key=f"to_league_choice_{k_id}")

        auto_from_logo = get_raw_club_logo(in_from_team, cf.get("from_logo", ""))
        auto_to_logo = get_raw_club_logo(in_to_team, cf.get("to_logo", ""))

        with st.expander("🛡️ 구단 로고 자동 매칭 확인 & 수동 변경 (드라이브 폴더 자동 스캔 연동)", expanded=False):
            st.caption("구글 드라이브 로고 폴더에 '구단명.webp' 또는 '구단명.png' 파일을 올려두면 링크 입력 없이 자동 매칭됩니다.")
            lg_c1, lg_c2 = st.columns(2)
            with lg_c1:
                in_from_logo_manual = st.text_input("원소속팀 로고 링크", value=auto_from_logo, placeholder="폴더/사전 자동 매칭됨", key=f"from_logo_{k_id}")
            with lg_c2:
                in_to_logo_manual = st.text_input("이적팀 로고 링크", value=auto_to_logo, placeholder="폴더/사전 자동 매칭됨", key=f"to_logo_{k_id}")

        raw_from_logo = get_raw_club_logo(in_from_team, in_from_logo_manual)
        raw_to_logo = get_raw_club_logo(in_to_team, in_to_logo_manual)
        final_from_logo = url_to_base64_img(raw_from_logo)
        final_to_logo = url_to_base64_img(raw_to_logo)

        is_tracked_target = any(k in in_to_league_choice for k in TRACKED_LEAGUE_NAMES)
        st.caption("✅ **10대 핵심 리그 이적**: 시즌 종료 후 4번 탭 사후 검증 대상에 **자동 등록**됩니다." if is_tracked_target else "ℹ️ **기타 리그 이적**: 메인 결산 장부에만 기록됩니다.")

        pos_col1, pos_col2 = st.columns(2)
        with pos_col1: main_position = st.selectbox("주 포지션 (🟢 천연 포지션)", list(POSITION_WEIGHTS.keys()), index=list(POSITION_WEIGHTS.keys()).index(cf.get("pos", list(POSITION_WEIGHTS.keys())[4])) if cf.get("pos", "") in POSITION_WEIGHTS else 4, key=f"pos_{k_id}")
        with pos_col2: 
            vers_init = cf.get("vers", list(VERSATILITY_WEIGHTS.keys())[0])
            versatility = st.selectbox("멀티 포지션 소화 능력", list(VERSATILITY_WEIGHTS.keys()), index=list(VERSATILITY_WEIGHTS.keys()).index(vers_init) if vers_init in VERSATILITY_WEIGHTS else 0, key=f"vers_{k_id}")

        if "단일" not in versatility:
            manual_sub_positions = st.multiselect(
                "🟡 서브 포지션 선택 (클릭 시 미니 축구장에 노란불 점등 · 비워두면 스탯 기반 자동 추론)",
                options=SUB_POS_OPTIONS,
                default=cf.get("sub_pos_list", []),
                key=f"subpos_{k_id}"
            )
        else:
            manual_sub_positions = []

        c_r1, c_r2 = st.columns(2)
        with c_r1: 
            reg_val = cf.get("reg_status", list(REGISTRATION_WEIGHTS.keys())[1])
            reg_status = st.selectbox("스쿼드 등록 / HG 쿼터", list(REGISTRATION_WEIGHTS.keys()), index=list(REGISTRATION_WEIGHTS.keys()).index(reg_val) if reg_val in REGISTRATION_WEIGHTS else 1, key=f"reg_{k_id}")
        with c_r2: 
            stage_val = cf.get("big_stage", list(BIG_STAGE_WEIGHTS.keys())[0])
            big_stage = st.selectbox("UCL / 빅매치 검증도", list(BIG_STAGE_WEIGHTS.keys()), index=list(BIG_STAGE_WEIGHTS.keys()).index(stage_val) if stage_val in BIG_STAGE_WEIGHTS else 0, key=f"stage_{k_id}")

        c_i1, c_i2 = st.columns(2)
        with c_i1: 
            inj_val = cf.get("injury", list(INJURY_WEIGHTS.keys())[1])
            injury_status = st.selectbox("부상 내구성 & 메디컬 리스크", list(INJURY_WEIGHTS.keys()), index=list(INJURY_WEIGHTS.keys()).index(inj_val) if inj_val in INJURY_WEIGHTS else 1, key=f"inj_{k_id}")
        with c_i2: 
            urg_val = cf.get("urgency", list(URGENCY_WEIGHTS.keys())[0])
            urgency_status = st.selectbox("영입 구단 절박성 & 취약 포지션", list(URGENCY_WEIGHTS.keys()), index=list(URGENCY_WEIGHTS.keys()).index(urg_val) if urg_val in URGENCY_WEIGHTS else 0, key=f"urg_{k_id}")

        selling_league = st.selectbox("보내는 리그 (원소속 리그)", list(LEAGUE_WEIGHTS.keys()), index=list(LEAGUE_WEIGHTS.keys()).index(cf.get("from_league", list(LEAGUE_WEIGHTS.keys())[0])) if cf.get("from_league", "") in LEAGUE_WEIGHTS else 0, key=f"league_{k_id}")
        buying_club_tier = st.selectbox("영입하는 구단 규모", list(CLUB_TIERS.keys()), index=list(CLUB_TIERS.keys()).index(cf.get("buying_tier", list(CLUB_TIERS.keys())[1])) if cf.get("buying_tier", "") in CLUB_TIERS else 1, key=f"tier_{k_id}")
        remaining_contract = st.selectbox("이적 당시 잔여 계약 기간", list(CONTRACT_WEIGHTS.keys()), index=list(CONTRACT_WEIGHTS.keys()).index(cf.get("contract", list(CONTRACT_WEIGHTS.keys())[2])) if cf.get("contract", "") in CONTRACT_WEIGHTS else 2, key=f"contract_{k_id}")

        st.markdown("---")

        f_p90 = (st.session_state["f_mins"] / 90.0) if st.session_state["f_mins"] > 0 else 1.0
        cur_p90_exp = (st.session_state["f_xg"] + st.session_state["f_xa"]) / f_p90
        cur_p90_tackles = st.session_state.get("f_tackles", 0) / f_p90
        cur_duels_avg = (st.session_state.get("f_duels_pct", 60.0) + st.session_state.get("f_aerial_pct", 60.0)) / 2.0
        cur_rating = st.session_state["f_rating"]

        is_def_or_mid = any(k in main_position for k in ["CB", "RB/LB", "CM/CDM"])
        is_gk_pos = "GK" in main_position

        if is_gk_pos:
            gk_prev = st.session_state.get("f_gk_prevented", 0.0)
            if cur_rating >= 7.35 or gk_prev >= 3.5: opta_w, opta_desc = 1.02, "🌟 최상위권 엘리트 선방쇼"
            elif cur_rating >= 7.05 or gk_prev >= 1.5: opta_w, opta_desc = 1.01, "🔥 주전급 안정적 선방"
            elif cur_rating >= 6.75 or gk_prev >= -1.0: opta_w, opta_desc = 1.00, "⚖️ 리그 평균 수준"
            else: opta_w, opta_desc = 0.98, "⚠️ 선방력 저조 / 불안"
        elif is_def_or_mid:
            if cur_rating >= 7.35 or cur_p90_exp >= 0.45 or (cur_duels_avg >= 64.0 and cur_p90_tackles >= 1.6): opta_w, opta_desc = 1.02, "🌟 최상위권 엘리트 수비/중원 지배력"
            elif cur_rating >= 7.08 or cur_p90_exp >= 0.25 or (cur_duels_avg >= 58.0 and cur_p90_tackles >= 1.1): opta_w, opta_desc = 1.01, "🔥 주전급 준수한 경합·수비 활약"
            elif cur_rating >= 6.75 or cur_duels_avg >= 50.0: opta_w, opta_desc = 1.00, "⚖️ 리그 평균 수준"
            else: opta_w, opta_desc = 0.98, "⚠️ 기대 이하 / 부진"
        else:
            if cur_rating >= 7.45 or cur_p90_exp >= 0.75: opta_w, opta_desc = 1.02, "🌟 최상위권 엘리트 공격 생산력"
            elif cur_rating >= 7.15 or cur_p90_exp >= 0.50: opta_w, opta_desc = 1.01, "🔥 주전급 준수한 공격 활약"
            elif cur_rating >= 6.80 or cur_p90_exp >= 0.25: opta_w, opta_desc = 1.00, "⚖️ 리그 평균 수준"
            else: opta_w, opta_desc = 0.98, "⚠️ 기대 이하 / 부진"

        with st.expander("🔗 [FotMob 탭 연동] 지난 시즌 실적 및 포지션 맞춤형 등급", expanded=True):
            if is_gk_pos:
                st.markdown(f"- **골키퍼 실적**: 선방 `{st.session_state.get('f_gk_saves', 78)}회` / 실점 `{st.session_state.get('f_gk_conceded', 28)}` / 클린시트 `{st.session_state.get('f_gk_cs', 10)}경기` | **평점**: `★ {cur_rating:.2f}` ({opta_desc})")
            elif is_def_or_mid:
                st.markdown(f"- **수비/중원 실적**: `{st.session_state['f_goals']}골 {st.session_state['f_assists']}도움` | **90분당 태클**: `{cur_p90_tackles:.2f}회` | **평균 경합승률**: `{cur_duels_avg:.1f}%` | **평점**: `★ {cur_rating:.2f}` ({opta_desc})")
            else:
                st.markdown(f"- **공격 실적**: `{st.session_state['f_goals']}골 {st.session_state['f_assists']}도움` (xG `{st.session_state['f_xg']:.2f}` / xA `{st.session_state['f_xa']:.2f}`) | **평점**: `★ {cur_rating:.2f}` ({opta_desc})")

        tm_market_value = st.number_input("트랜스퍼마르크트 시장 가치 (만 유로, €)", min_value=0, value=cf.get("tm", 4500), step=50, key=f"tm_{k_id}")
        if tm_market_value > 0: st.caption(f"💡 시장가치 환산: **{format_currency_desc(tm_market_value)}**")

        is_loan_type = "임대" in transfer_type and "의무" not in transfer_type
        is_undisclosed = "비공개" in transfer_type
        is_fa = "FA" in transfer_type

        fee_label = "실제 수령/지출 임대료 (Loan Fee, 만 유로, €)" if is_loan_type else ("실제 방출(판매) 보장 이적료 (만 유로, €)" if is_out_trade else "실제 영입(지출) 보장 이적료 (만 유로, €)")
        actual_transfer_fee = st.number_input(fee_label, min_value=0, value=0 if is_undisclosed else cf.get("fee", 0), step=50, key=f"fee_{k_id}", disabled=is_undisclosed)

        if is_undisclosed:
            st.info("💡 **비공개 이적 선택됨**: 시장 적정가와 동일하게 추정하여 분석합니다.")
        elif actual_transfer_fee > 0:
            st.caption(f"💡 실제금액 환산: **{format_currency_desc(actual_transfer_fee)}**")

        with st.expander("💼 [선택/수정 입력] 주급(Weekly Wage) & 연간 총비용 분석", expanded=True if cf.get("wage", 0.0) > 0 or is_fa or is_loan_type else False):
            weekly_wage_in = st.number_input("선수 주급 (만 유로, €/주)", min_value=0.0, value=float(cf.get("wage", 0.0)), step=0.5, key=f"wage_{k_id}")
            annual_wage_eur = weekly_wage_in * 52
            annual_transfer_amort = (actual_transfer_fee / 4.0) if actual_transfer_fee > 0 else 0.0
            total_annual_cost = annual_transfer_amort + annual_wage_eur
            if weekly_wage_in > 0:
                st.caption(f"📌 **주급 환산**: 주당 약 {weekly_wage_in*10000*rate_krw/100000000:.1f}억원 (£{weekly_wage_in*rate_gbp:.1f}만) | **연간 총비용**: `€{total_annual_cost:,.1f}만`")

        player_notes = st.text_area("개인 메모 / 스카우팅 코멘트 (시트 저장 전용 · 인포그래픽 미표시)", value=cf.get("notes", ""), placeholder="예: 대인 방어 및 후방 빌드업 우수 (구글 시트에만 기록됩니다)", key=f"note_{k_id}")

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
            overpay_pct = ((weekly_wage_in - expected_fair_weekly_wage) / expected_fair_weekly_wage) * 100
            diff = (weekly_wage_in - expected_fair_weekly_wage) * 52 
        else: overpay_pct, diff = 0.0, 0.0
    elif is_loan_type:
        expected_1yr_use_val = fair_value
        actual_1yr_cost = calc_actual_fee + (weekly_wage_in * 52)
        overpay_pct = ((actual_1yr_cost - expected_1yr_use_val) / expected_1yr_use_val) * 100 if expected_1yr_use_val > 0 else 0.0
        diff = actual_1yr_cost - expected_1yr_use_val if expected_1yr_use_val > 0 else 0.0
    else:
        diff = calc_actual_fee - fair_value
        overpay_pct = (diff / fair_value) * 100 if fair_value > 0 else 0.0

    if is_undisclosed: status_label = "⚖️ 비공개 (적정가 추정)"
    elif is_fa and weekly_wage_in > 0:
        status_label = "⚖️ 적정 주급 FA 영입" if abs(overpay_pct) <= 10.0 else (f"⚠️ 주급 오버페이 FA (+{overpay_pct:.1f}%)" if overpay_pct > 0 else f"💎 주급 혜자 FA ({overpay_pct:.1f}%)")
    elif fair_value == 0 and calc_actual_fee == 0: status_label = "입력 대기 중"
    elif abs(diff) <= (fair_value * 0.05): status_label = "⚖️ 적정가 (Fair Deal)"
    elif diff > 0: status_label = f"⚠️ {'고가 매각 성공' if is_out_trade else '고평가/오버페이'} (+{overpay_pct:.1f}%)"
    else: status_label = f"💎 {'헐값 매각 손해' if is_out_trade else '저평가/혜자'} ({overpay_pct:.1f}%)"

    market_min = base_calc_val * (1.15 if is_winter else 1.05)
    market_max = base_calc_val * (1.20 if is_winter else 1.10)
    market_mid = (market_min + market_max) / 2.0
    ext_diff = calc_actual_fee - market_mid
    ext_overpay_pct = (ext_diff / market_mid) * 100 if market_mid > 0 else 0.0

    if tm_market_value > 0 and (calc_actual_fee > 0 or is_loan_type or is_fa or is_undisclosed):
        if is_fa:
            base_deal_score = 8.00
            val_score_delta = max(-3.0, min(1.5, -(overpay_pct / 30.0))) if weekly_wage_in > 0 else 0.5
        elif is_loan_type:
            base_deal_score = 7.50
            val_score_delta = max(-3.0, min(2.0, -(overpay_pct / 25.0)))
        else:
            base_deal_score = 7.50
            score_multiplier = 1.0 if is_out_trade else -1.0
            val_score_delta = 0.0 if is_undisclosed else max(-3.5, min(2.5, score_multiplier * (overpay_pct / 20.0)))
            if weekly_wage_in > 0 and expected_fair_weekly_wage > 0 and weekly_wage_in > expected_fair_weekly_wage * 1.5:
                val_score_delta -= min(0.6, (weekly_wage_in - expected_fair_weekly_wage * 1.5) / 10.0)

        rating_delta = max(-0.8, min(1.0, (cur_rating - 7.00) * 1.5))
        age_delta = max(-1.0, min(0.8, (age_w - 1.00) * 8.0))
        risk_delta = (stage_w - 1.00) * 5.0 + (inj_w - 1.00) * 5.0 + (reg_w - 1.00) * 3.0 + (urg_w - 1.00) * 2.0

        final_deal_score = round(max(1.00, min(10.00, base_deal_score + val_score_delta + rating_delta + age_delta + risk_delta)), 2)
        ext_val_score_delta = val_score_delta if (is_fa or is_loan_type) else (0.0 if is_undisclosed else max(-3.5, min(2.5, score_multiplier * (ext_overpay_pct / 20.0))))
        ext_deal_score = round(max(1.00, min(10.00, base_deal_score + ext_val_score_delta + rating_delta + age_delta + risk_delta)), 2)

        def get_grade_info(score):
            if score >= 9.00: return "💎 S등급 (Masterclass)", "#10B981"
            elif score >= 8.00: return "🌟 A등급 (Excellent)", "#38BDF8"
            elif score >= 7.00: return "⚖️ B등급 (Solid / Fair)", "#FBBF24"
            elif score >= 6.00: return "⚠️ C등급 (Risky Deal)", "#F97316"
            else: return "🚨 D등급 (Panic / Bad)", "#EF4444"

        deal_grade, grade_hex_color = get_grade_info(final_deal_score)
        ext_deal_grade, ext_hex_color = get_grade_info(ext_deal_score)
    else:
        final_deal_score, ext_deal_score = 0.00, 0.00
        deal_grade, grade_hex_color = "분석 대기 중", "#94A3B8"
        ext_deal_grade, ext_hex_color = "분석 대기 중", "#94A3B8"

    if not is_loan_type and fair_value > 0:
        future_age = player_age + 3
        future_age_w = get_positional_age_weight(future_age, main_position)
        age_retention_ratio = (future_age_w / age_w) if age_w > 0 else 1.0
        pot_growth_bonus = 1.15 if player_age <= 22 else (1.05 if player_age <= 24 else 0.95)
        proj_3yr_val = fair_value * age_retention_ratio * pot_growth_bonus
        recovery_pct = (proj_3yr_val / calc_actual_fee * 100.0) if calc_actual_fee > 0 else 100.0
    else:
        future_age, proj_3yr_val, recovery_pct = player_age + 3, 0.0, 0.0

    is_gk = "GK" in main_position
    f_target_mins_t1 = 1440 if is_winter else 3036
    raw_lf_t1 = LEAGUE_WEIGHTS[selling_league] / (LEAGUE_WEIGHTS.get(in_to_league_choice, 1.0))
    adapt_p_t1 = max(0.80, 1.0 - (max(0.0, LEAGUE_WEIGHTS.get(in_to_league_choice, 1.0) - LEAGUE_WEIGHTS[selling_league]) * 0.45))
    final_lf_t1 = raw_lf_t1 * adapt_p_t1
    t_p90_t1 = f_target_mins_t1 / 90.0

    if not is_gk:
        p90_xg_t1 = (float(st.session_state["f_xg"]) / f_p90) * final_lf_t1
        p90_xa_t1 = (float(st.session_state["f_xa"]) / f_p90) * final_lf_t1
        p90_shots_t1 = (float(st.session_state["f_shots"]) / f_p90) * final_lf_t1
        p90_sot_t1 = (float(st.session_state["f_sot"]) / f_p90) * final_lf_t1
        p90_chances_t1 = (float(st.session_state["f_chances"]) / f_p90) * final_lf_t1
        p90_dribbles_t1 = (float(st.session_state["f_dribbles"]) / f_p90) * final_lf_t1
        p90_box_t1 = (float(st.session_state["f_touches_box"]) / f_p90) * final_lf_t1
        p90_tackles_t1 = (float(st.session_state["f_tackles"]) / f_p90) * (1.0 / final_lf_t1)

        fin_ratio_t1 = float(st.session_state["f_goals"]) / float(st.session_state["f_xg"]) if float(st.session_state["f_xg"]) > 0 else 1.0
        pj_goals_t1 = round(p90_xg_t1 * t_p90_t1 * fin_ratio_t1, 1)
        pj_xg_t1 = round(p90_xg_t1 * t_p90_t1, 2)
        pj_assists_t1 = round(p90_xa_t1 * t_p90_t1, 1)
        pj_xa_t1 = round(p90_xa_t1 * t_p90_t1, 2)
        pj_shots_t1 = round(p90_shots_t1 * t_p90_t1, 0)
        pj_sot_t1 = round(p90_sot_t1 * t_p90_t1, 0)
        pj_chances_t1 = round(p90_chances_t1 * t_p90_t1, 0)
        pj_dribbles_t1 = round(p90_dribbles_t1 * t_p90_t1, 0)
        pj_box_t1 = round(p90_box_t1 * t_p90_t1, 0)
        pj_tackles_t1 = round(p90_tackles_t1 * t_p90_t1, 0)
    else:
        pj_goals_t1 = pj_xg_t1 = pj_assists_t1 = pj_xa_t1 = pj_shots_t1 = pj_sot_t1 = pj_chances_t1 = pj_dribbles_t1 = pj_box_t1 = pj_tackles_t1 = 0.0

    pj_rating_t1 = round(max(6.0, cur_rating - (1.0 - final_lf_t1) * 0.9), 2)

    with col2:
        st.subheader("🖼️ [V8 Pro FM Scouting Edition] 초고화질 스카우팅 인포그래픽 보드")
        display_name = player_name.strip() if player_name.strip() else "선수명 미입력"
        display_nat = f"({player_nat.strip()})" if player_nat.strip() else ""
        pos_short = main_position.split(" (")[0]
        ttype_short = transfer_type.split(" (")[0]
        reg_short = reg_status.split(" (")[0]
        urg_short = urgency_status.split(" (")[0]

        from_t_disp = in_from_team.strip() if in_from_team.strip() else "원소속팀"
        to_t_disp = in_to_team.strip() if in_to_team.strip() else "영입구단"
        tag_badge_txt = "TRANSFER OUT · 방출/매각" if is_out_trade else "TRANSFER IN · 영입/보강"
        badge_bg = "linear-gradient(90deg, #E11D48, #BE123C)" if is_out_trade else "linear-gradient(90deg, #2563EB, #4F46E5)"
        fee_display = "비공개 (추정)" if is_undisclosed else (f"€{calc_actual_fee:,.1f}만" if not is_fa else "FA (€0)")

        idx_league = to_public_index(league_w, 0.45, 1.00)
        idx_age = to_public_index(age_w, 0.70, 1.05)
        idx_perf = int(round(max(55, min(98, (cur_rating - 6.0) * 22 + 52))))
        idx_stage = to_public_index(stage_w, 0.98, 1.03)
        idx_inj = to_public_index(inj_w, 0.94, 1.01)
        idx_tactic = to_public_index((pos_w + vers_w + reg_w + urg_w) / 4.0, 0.98, 1.04)

        hex_cats = ['리그 경쟁력', '에이징/포텐', '직전 퍼포먼스', '빅매치 검증', '피지컬 내구성', '전술 적합성']
        hex_scores = [idx_league, idx_age, idx_perf, idx_stage, idx_inj, idx_tactic]
        svg_radar_t1 = build_svg_radar(hex_cats, hex_scores, color_a="#38BDF8" if not is_out_trade else "#F43F5E", size=330)

        donut_main = build_svg_donut_ring(final_deal_score, 10.0, grade_hex_color, "모델 정밀 평점", size=110)
        donut_ext = build_svg_donut_ring(ext_deal_score, 10.0, ext_hex_color, "외부 시장 평점", size=110)

        max_v_ref = max([tm_market_value, fair_value, calc_actual_fee, proj_3yr_val, 1000.0]) * 1.12
        w_tm = min(100, int(tm_market_value / max_v_ref * 100))
        w_fair = min(100, int(fair_value / max_v_ref * 100))
        w_act = min(100, int(calc_actual_fee / max_v_ref * 100))
        w_3yr = min(100, int(proj_3yr_val / max_v_ref * 100))

        mini_from_img = f"<img src='{final_from_logo}' style='width:22px; height:22px; object-fit:contain; vertical-align:middle; margin-right:5px; filter:drop-shadow(0 1px 2px rgba(0,0,0,0.6));'/>" if final_from_logo else "🏟️ "
        mini_to_img = f"<img src='{final_to_logo}' style='width:22px; height:22px; object-fit:contain; vertical-align:middle; margin-right:5px; filter:drop-shadow(0 1px 2px rgba(0,0,0,0.6));'/>" if final_to_logo else "🛡️ "
        route_with_logos_html = f"<span style='display:inline-flex; align-items:center;'>{mini_from_img}<b>{from_t_disp}</b> &nbsp;➔&nbsp; {mini_to_img}<b style='color:#FFFFFF;'>{to_t_disp}</b> &nbsp;<span style='font-size:11.5px; color:#93C5FD;'>({in_to_league_choice.split(' (')[0]})</span></span>"

        hero_logo_url = final_to_logo if final_to_logo else final_from_logo
        hero_club_emblem_html = (
            f"<div style='width:80px; height:80px; border-radius:18px; background:radial-gradient(circle, rgba(30,41,59,0.95) 0%, rgba(9,13,22,0.98) 100%); border:2px solid #38BDF8; box-shadow:0 0 18px rgba(56,189,248,0.45); display:flex; align-items:center; justify-content:center; padding:8px; margin-right:18px; flex-shrink:0;'>"
            f"<img src='{hero_logo_url}' style='width:100%; height:100%; object-fit:contain; filter:drop-shadow(0 2px 4px rgba(0,0,0,0.65));'/></div>"
            if hero_logo_url else
            f"<div style='width:74px; height:74px; border-radius:18px; background:linear-gradient(135deg, #1E293B, #0F172A); border:2px solid #38BDF8; display:flex; align-items:center; justify-content:center; font-size:30px; font-weight:900; color:#38BDF8; margin-right:18px; flex-shrink:0;'>🛡️</div>"
        )

        act_bar_bg = "linear-gradient(90deg, #0284C7, #38BDF8)" if overpay_pct <= 5 else "linear-gradient(90deg, #E11D48, #FB7185)"
        proj_stat_line = (
            f"예상 득점 <b style='color:#10B981;'>{pj_goals_t1:.1f}골</b>(xG {pj_xg_t1:.2f}) · 예상 도움 <b style='color:#A855F7;'>{pj_assists_t1:.1f}도움</b>(xA {pj_xa_t1:.2f}) · 슈팅 <b>{int(pj_shots_t1)}회</b> · 기회창출 <b>{int(pj_chances_t1)}회</b> · 예상 평점 <b style='color:#FBBF24;'>★{pj_rating_t1:.2f}</b>"
            if not is_gk else
            f"골키퍼 첫 시즌 예상 FotMob 평점 <b style='color:#FBBF24;'>★{pj_rating_t1:.2f}</b> (직전 선방 {st.session_state.get('f_gk_saves', 78)}회 · 클린시트 {st.session_state.get('f_gk_cs', 10)}회)"
        )

        # [90종 FM 스카우팅 리포트 생성]
        fm_mini_pitch_svg = build_fm_mini_pitch_svg(
            main_position, versatility, manual_sub_positions,
            {
                "pass_pct": st.session_state.get("f_pass_pct", 88.2),
                "p90_drib": st.session_state.get("f_dribbles", 14) / f_p90,
                "p90_box": st.session_state.get("f_touches_box", 153) / f_p90,
                "p90_tkl": cur_p90_tackles
            }
        )
        fm_traits, fm_pros, fm_cons = generate_fm_scouting_features(
            main_position, player_age, cur_rating,
            st.session_state["f_goals"], st.session_state["f_xg"],
            st.session_state["f_assists"], st.session_state["f_xa"],
            st.session_state["f_shots"], st.session_state["f_sot"],
            st.session_state["f_chances"], st.session_state.get("f_big_chances", 2),
            st.session_state["f_dribbles"], st.session_state["f_touches_box"],
            st.session_state["f_tackles"], st.session_state.get("f_pass_pct", 88.2),
            st.session_state.get("f_duels_pct", 62.4), st.session_state.get("f_aerial_pct", 65.8),
            st.session_state.get("f_pk", 0),
            st.session_state.get("f_gk_saves", 78), st.session_state.get("f_gk_conceded", 28),
            st.session_state.get("f_gk_prevented", 2.45), st.session_state.get("f_gk_cs", 10),
            st.session_state.get("f_gk_errors", 0), st.session_state.get("f_gk_claims", 18),
            st.session_state["f_matches"], st.session_state.get("f_starts", 25),
            st.session_state["f_mins"], overpay_pct, big_stage, injury_status,
            reg_status, versatility, remaining_contract, urgency_status, league_w
        )

        traits_badges_html = "".join([
            f"<span style='background:rgba(56,189,248,0.14); border:1px solid rgba(56,189,248,0.45); color:#E0F2FE; padding:5px 10px; border-radius:8px; font-size:11.5px; font-weight:800; display:inline-block;'>{tr}</span>"
            for tr in fm_traits
        ])
        pros_items_html = "".join([
            f"<div style='display:flex; align-items:center; gap:7px; background:rgba(16,185,129,0.10); border-left:3px solid #10B981; padding:6px 10px; border-radius:6px; margin-bottom:5px; font-size:11.5px; color:#E2E8F0; font-weight:700;'><span style='color:#34D399;'>🟢</span> {pr}</div>"
            for pr in fm_pros
        ])
        cons_items_html = "".join([
            f"<div style='display:flex; align-items:center; gap:7px; background:rgba(244,63,94,0.10); border-left:3px solid #F43F5E; padding:6px 10px; border-radius:6px; margin-bottom:5px; font-size:11.5px; color:#E2E8F0; font-weight:700;'><span style='color:#FB7185;'>🔴</span> {cn}</div>"
            for cn in fm_cons
        ])

        tab1_board_html = f"""
        <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px; margin-bottom:16px; padding-bottom:12px; border-bottom:1px solid rgba(148,163,184,0.18);">
            <div style="display:flex; align-items:center; gap:10px;">
                <span style="background:{badge_bg}; color:#FFFFFF; font-size:11px; font-weight:900; padding:5px 12px; border-radius:20px; letter-spacing:0.5px;">{tag_badge_txt}</span>
                <span style="background:rgba(30,41,59,0.9); border:1px solid #475569; color:#E2E8F0; font-size:12px; font-weight:700; padding:4px 11px; border-radius:20px;">{season_val.split(' (')[0]} · {ttype_short}</span>
            </div>
            <div style="background:rgba(14,165,233,0.14); border:1px solid rgba(56,189,248,0.45); color:#38BDF8; font-size:13.5px; font-weight:800; padding:6px 15px; border-radius:20px;">
                {route_with_logos_html}
            </div>
        </div>

        <div class="glass-panel" style="padding:18px 22px; margin-bottom:16px; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:16px;">
            <div style="display:flex; align-items:center; flex:1; min-width:260px;">
                {hero_club_emblem_html}
                <div>
                    <div style="font-size:11px; font-weight:800; color:#38BDF8; letter-spacing:1px; margin-bottom:3px;">OFFICIAL TRANSFER SCOUTING REPORT</div>
                    <div style="font-size:30px; font-weight:900; color:#FFFFFF; letter-spacing:-0.8px; line-height:1.15;">
                        {display_name} <span style="font-size:16px; font-weight:600; color:#94A3B8;">{display_nat}</span>
                    </div>
                    <div style="display:flex; flex-wrap:wrap; gap:6px; margin-top:9px;">
                        <span style="background:#0F172A; border:1px solid #334155; padding:4px 10px; border-radius:8px; font-size:11.5px; color:#E2E8F0;">🎂 <b>만 {player_age}세</b></span>
                        <span style="background:#0F172A; border:1px solid #38BDF8; padding:4px 10px; border-radius:8px; font-size:11.5px; color:#7DD3FC;">⚽ <b>{pos_short}</b></span>
                        <span style="background:#0F172A; border:1px solid #334155; padding:4px 10px; border-radius:8px; font-size:11.5px; color:#E2E8F0;">🌍 출발: <b>{selling_league.split(' (')[0]}</b></span>
                    </div>
                </div>
            </div>
            <div style="display:flex; gap:14px; align-items:center;">
                <div style="text-align:center;">{donut_main}</div>
                <div style="text-align:center;">{donut_ext}</div>
            </div>
        </div>

        <div style="display:grid; grid-template-columns:repeat(4, 1fr); gap:12px; margin-bottom:16px;">
            <div class="kpi-card" style="border-top:3px solid #64748B;">
                <div style="font-size:11px; color:#94A3B8; font-weight:700;">TM 기준 시장가치</div>
                <div style="font-size:21px; font-weight:900; color:#F8FAFC; margin-top:5px;">€{tm_market_value:,.0f}만</div>
                <div style="font-size:11px; color:#64748B; margin-top:3px;">{format_currency_desc(tm_market_value).split(' | ')[0]}</div>
            </div>
            <div class="kpi-card" style="border-top:3px solid #10B981;">
                <div style="font-size:11px; color:#6EE7B7; font-weight:700;">모델 산출 적정가</div>
                <div style="font-size:21px; font-weight:900; color:#10B981; margin-top:5px;">€{fair_value:,.1f}만</div>
                <div style="font-size:11px; color:#64748B; margin-top:3px;">{format_currency_desc(fair_value).split(' | ')[0]}</div>
            </div>
            <div class="kpi-card" style="border-top:3px solid #38BDF8;">
                <div style="font-size:11px; color:#7DD3FC; font-weight:700;">실제 거래 이적료</div>
                <div style="font-size:21px; font-weight:900; color:#38BDF8; margin-top:5px;">{fee_display}</div>
                <div style="font-size:11px; color:#94A3B8; margin-top:3px;">적정가 대비 {diff:+,.1f}만 €</div>
            </div>
            <div class="kpi-card" style="border-top:3px solid #F59E0B;">
                <div style="font-size:11px; color:#FCD34D; font-weight:700;">현실 시장 적정 범위</div>
                <div style="font-size:17px; font-weight:900; color:#FBBF24; margin-top:7px;">€{market_min:,.0f}~{market_max:,.0f}만</div>
                <div style="font-size:11px; color:#E2E8F0; margin-top:4px;">{status_label.split(' (')[0]} ({overpay_pct:+.1f}%)</div>
            </div>
        </div>

        <div style="display:grid; grid-template-columns: 1.02fr 1.12fr; gap:14px; margin-bottom:16px; align-items:stretch;">
            <div class="glass-panel" style="padding:16px; text-align:center; display:flex; flex-direction:column; justify-content:center;">
                <div style="font-size:13.5px; font-weight:900; color:#38BDF8; letter-spacing:0.3px; margin-bottom:6px;">💠 6각형 스카우팅 밸런스 인덱스</div>
                {svg_radar_t1}
            </div>
            <div class="glass-panel" style="padding:18px; display:flex; flex-direction:column; justify-content:space-between;">
                <div>
                    <div style="font-size:13.5px; font-weight:900; color:#10B981; margin-bottom:14px;">💰 이적료 밸류에이션 & 3년 후(만 {future_age}세) 가치 비교</div>
                    <div style="margin-bottom:12px;">
                        <div style="display:flex; justify-content:space-between; font-size:12px; margin-bottom:5px;"><span style="color:#94A3B8; font-weight:700;">TM 시장가치 (기준점)</span><b style="color:#F8FAFC;">€{tm_market_value:,.0f}만 ({format_currency_desc(tm_market_value).split(' | ')[0]})</b></div>
                        <div style="background:#090D16; height:12px; border-radius:6px; overflow:hidden; border:1px solid #1E293B;"><div style="width:{w_tm}%; background:linear-gradient(90deg, #475569, #94A3B8); height:100%; border-radius:6px;"></div></div>
                    </div>
                    <div style="margin-bottom:12px;">
                        <div style="display:flex; justify-content:space-between; font-size:12px; margin-bottom:5px;"><span style="color:#6EE7B7; font-weight:700;">모델 산출 적정가</span><b style="color:#10B981;">€{fair_value:,.1f}만 ({format_currency_desc(fair_value).split(' | ')[0]})</b></div>
                        <div style="background:#090D16; height:12px; border-radius:6px; overflow:hidden; border:1px solid #1E293B;"><div style="width:{w_fair}%; background:linear-gradient(90deg, #059669, #34D399); height:100%; border-radius:6px;"></div></div>
                    </div>
                    <div style="margin-bottom:12px;">
                        <div style="display:flex; justify-content:space-between; font-size:12px; margin-bottom:5px;"><span style="color:#7DD3FC; font-weight:700;">실제 거래 이적료 ({status_label.split(' (')[0]})</span><b style="color:#38BDF8;">{fee_display}</b></div>
                        <div style="background:#090D16; height:12px; border-radius:6px; overflow:hidden; border:1px solid #1E293B;"><div style="width:{w_act}%; background:{act_bar_bg}; height:100%; border-radius:6px;"></div></div>
                    </div>
                    <div style="margin-bottom:14px;">
                        <div style="display:flex; justify-content:space-between; font-size:12px; margin-bottom:5px;"><span style="color:#D8B4FE; font-weight:700;">3년 후 예상 리세일 가치 (회수율 {recovery_pct:.0f}%)</span><b style="color:#C084FC;">€{proj_3yr_val:,.1f}만</b></div>
                        <div style="background:#090D16; height:12px; border-radius:6px; overflow:hidden; border:1px solid #1E293B;"><div style="width:{w_3yr}%; background:linear-gradient(90deg, #7E22CE, #C084FC); height:100%; border-radius:6px;"></div></div>
                    </div>
                </div>
                <div style="background:linear-gradient(135deg, rgba(2,132,199,0.18), rgba(15,23,42,0.9)); border:1px solid rgba(56,189,248,0.35); border-radius:12px; padding:12px 14px;">
                    <div style="font-size:11.5px; font-weight:900; color:#38BDF8; margin-bottom:5px;">📱 FOTMOB 이적 첫 시즌 예상 성적 ({f_target_mins_t1:,}분 출전 기준)</div>
                    <div style="font-size:12.5px; color:#F8FAFC; line-height:1.5;">{proj_stat_line}</div>
                </div>
            </div>
        </div>

        <!-- [90종 FM 스카우팅 리포트 패널] 미니 포지션 숙련도 피치 + 전술 아키타입/선호 플레이 + 장단점 배지 -->
        <div class="glass-panel" style="padding:16px 18px; margin-bottom:16px;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
                <div style="font-size:13px; font-weight:900; color:#34D399; letter-spacing:0.3px;">🎮 FM SCOUTING INTELLIGENCE · 포지션 숙련도 & 전술 아키타입 & 장단점 리포트</div>
                <div style="font-size:11px; color:#94A3B8; font-weight:700;"><span style="color:#10B981;">●</span> 천연(주포지션) &nbsp;<span style="color:#FBBF24;">●</span> 능숙(서브포지션)</div>
            </div>
            <div style="display:grid; grid-template-columns: 165px 1fr; gap:16px; align-items:center;">
                <div style="background:#090D16; border:1px solid #1E293B; border-radius:12px; padding:10px; text-align:center;">
                    {fm_mini_pitch_svg}
                </div>
                <div style="display:flex; flex-direction:column; gap:10px;">
                    <div style="background:#090D16; border:1px solid #1E293B; border-radius:10px; padding:10px 12px;">
                        <div style="font-size:11px; font-weight:800; color:#38BDF8; margin-bottom:6px;">🧬 전술 롤 아키타입 & 선호하는 플레이 (Tactical Role & Player Traits)</div>
                        <div style="display:flex; flex-wrap:wrap; gap:6px;">{traits_badges_html}</div>
                    </div>
                    <div style="display:grid; grid-template-columns: 1fr 1fr; gap:10px;">
                        <div style="background:#090D16; border:1px solid rgba(16,185,129,0.28); border-radius:10px; padding:10px 12px;">
                            <div style="font-size:11px; font-weight:900; color:#34D399; margin-bottom:6px;">🟢 핵심 강점 (PROS)</div>
                            {pros_items_html}
                        </div>
                        <div style="background:#090D16; border:1px solid rgba(244,63,94,0.28); border-radius:10px; padding:10px 12px;">
                            <div style="font-size:11px; font-weight:900; color:#FB7185; margin-bottom:6px;">🔴 약점 및 리스크 (CONS)</div>
                            {cons_items_html}
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <div class="glass-panel" style="padding:16px 18px;">
            <div style="font-size:12.5px; font-weight:900; color:#94A3B8; margin-bottom:12px; letter-spacing:0.3px;">📋 12대 세부 스카우팅 프로파일링 (가중치 알고리즘 반영 · 배율 비공개)</div>
            <div style="display:grid; grid-template-columns:repeat(4, 1fr); gap:9px; font-size:12px;">
                <div style="background:#090D16; padding:9px 11px; border-radius:10px; border-left:3px solid #38BDF8;"><div style="color:#64748B; font-size:10.5px; font-weight:700;">01. 출발 리그 수준</div><div style="color:#F8FAFC; font-weight:800; margin-top:2px;">{selling_league.split(' (')[0]}</div></div>
                <div style="background:#090D16; padding:9px 11px; border-radius:10px; border-left:3px solid #10B981;"><div style="color:#64748B; font-size:10.5px; font-weight:700;">02. 에이징 커브 구간</div><div style="color:#F8FAFC; font-weight:800; margin-top:2px;">만 {player_age}세 ({pos_short})</div></div>
                <div style="background:#090D16; padding:9px 11px; border-radius:10px; border-left:3px solid #A855F7;"><div style="color:#64748B; font-size:10.5px; font-weight:700;">03. 영입 구단 스케일</div><div style="color:#F8FAFC; font-weight:800; margin-top:2px;">{buying_club_tier.split(':')[0]}</div></div>
                <div style="background:#090D16; padding:9px 11px; border-radius:10px; border-left:3px solid #F59E0B;"><div style="color:#64748B; font-size:10.5px; font-weight:700;">04. 잔여 계약 기간</div><div style="color:#F8FAFC; font-weight:800; margin-top:2px;">{remaining_contract.split(' (')[0]}</div></div>
                <div style="background:#090D16; padding:9px 11px; border-radius:10px; border-left:3px solid #EC4899;"><div style="color:#64748B; font-size:10.5px; font-weight:700;">05. 주 포지션 가치</div><div style="color:#F8FAFC; font-weight:800; margin-top:2px;">{pos_short}</div></div>
                <div style="background:#090D16; padding:9px 11px; border-radius:10px; border-left:3px solid #2DD4BF;"><div style="color:#64748B; font-size:10.5px; font-weight:700;">06. 멀티 포지션 소화</div><div style="color:#F8FAFC; font-weight:800; margin-top:2px;">{versatility.split(' (')[0]}</div></div>
                <div style="background:#090D16; padding:9px 11px; border-radius:10px; border-left:3px solid #38BDF8;"><div style="color:#64748B; font-size:10.5px; font-weight:700;">07. 등록 쿼터 / HG</div><div style="color:#F8FAFC; font-weight:800; margin-top:2px;">{reg_short}</div></div>
                <div style="background:#090D16; padding:9px 11px; border-radius:10px; border-left:3px solid #10B981;"><div style="color:#64748B; font-size:10.5px; font-weight:700;">08. 직전 시즌 활약도</div><div style="color:#38BDF8; font-weight:800; margin-top:2px;">★{cur_rating:.2f} ({opta_desc.split(' ')[1]})</div></div>
                <div style="background:#090D16; padding:9px 11px; border-radius:10px; border-left:3px solid #A855F7;"><div style="color:#64748B; font-size:10.5px; font-weight:700;">09. 계약 및 이적 형태</div><div style="color:#F8FAFC; font-weight:800; margin-top:2px;">{ttype_short}</div></div>
                <div style="background:#090D16; padding:9px 11px; border-radius:10px; border-left:3px solid #F59E0B;"><div style="color:#64748B; font-size:10.5px; font-weight:700;">10. 빅매치 / UCL 검증</div><div style="color:#F8FAFC; font-weight:800; margin-top:2px;">{big_stage.split(' (')[0]}</div></div>
                <div style="background:#090D16; padding:9px 11px; border-radius:10px; border-left:3px solid #EC4899;"><div style="color:#64748B; font-size:10.5px; font-weight:700;">11. 메디컬 / 내구성</div><div style="color:#F8FAFC; font-weight:800; margin-top:2px;">{injury_status.split(' (')[0]}</div></div>
                <div style="background:#090D16; padding:9px 11px; border-radius:10px; border-left:3px solid #2DD4BF;"><div style="color:#64748B; font-size:10.5px; font-weight:700;">12. 구단 영입 절박성</div><div style="color:#F8FAFC; font-weight:800; margin-top:2px;">{urg_short}</div></div>
            </div>
        </div>
        """
        render_copyable_infographic(tab1_board_html, filename=f"scouting_{display_name}", height=1135)

        with st.expander("🔍 [내부 관리용] 12대 세부 가중치 적용 현황표 & 누적 배율 (외부 비공개 확인용)", expanded=False):
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
                    reg_status.split(" (")[0], f"★{cur_rating:.2f} ({opta_desc})", ttype_short,
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
    btn_label_t1 = f"🔄 '{display_pname_t1}' 수정된 데이터 구글 시트에 업데이트(덮어쓰기)" if edit_toggle else f"💾 {tag_btn_name_t1} 구글 시트에 바로 저장하기 (구단 로고·서브포지션 자동 저장)"

    if st.button(btn_label_t1, type="primary", use_container_width=True, key="save_btn_tab1"):
        if not player_name.strip():
            st.warning("⚠️ 선수 이름을 먼저 입력해 주세요.")
        else:
            action_type = "update_existing" if edit_toggle else "save_all"
            with st.spinner("구글 시트에 데이터를 기록 중입니다..."):
                if in_from_team.strip() and raw_from_logo:
                    st.session_state["custom_club_logos"][in_from_team.strip()] = raw_from_logo
                if in_to_team.strip() and raw_to_logo:
                    st.session_state["custom_club_logos"][in_to_team.strip()] = raw_to_logo

                contract_desc = remaining_contract.split(" (")[0]
                nat_str = player_nat if player_nat.strip() else "미상"
                clean_user_note = clean_notes_display(player_notes)
                detailed_notes = f"[{'방출' if is_out_trade else '영입'}|{ttype_short}|{reg_short}|{urg_short}|UCL:{stage_w:.2f}|메디컬:{inj_w:.2f}] 계약:{contract_desc}"
                if clean_user_note: detailed_notes += f" | {clean_user_note}"
                if is_gk: detailed_notes += f" | GK[선방:{st.session_state.get('f_gk_saves', 78)}|실점:{st.session_state.get('f_gk_conceded', 28)}]"
                if manual_sub_positions: detailed_notes += f" ||SUBPOS:{','.join(manual_sub_positions)}||"
                if raw_from_logo: detailed_notes += f" ||LOGO_FROM:{raw_from_logo}||"
                if raw_to_logo: detailed_notes += f" ||LOGO_TO:{raw_to_logo}||"

                payload = {
                    "action": action_type, "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "season": season_val, "name": player_name, "nat": nat_str, "age": int(player_age),
                    "pos": pos_short, "from_league": selling_league.split(" (")[0],
                    "buying_tier": buying_club_tier.split(":")[0], "transfer_type": ttype_short,
                    "tm_val": float(tm_market_value), "fee": float(calc_actual_fee),
                    "fair_val": round(fair_value, 1), "diff": round(diff, 1),
                    "status": status_label, "deal_score": float(final_deal_score),
                    "prev_matches": int(st.session_state["f_matches"]), "prev_mins": int(st.session_state["f_mins"]),
                    "prev_goals": int(st.session_state["f_goals"]), "prev_xg": float(st.session_state["f_xg"]),
                    "prev_assists": int(st.session_state["f_assists"]), "prev_xa": float(st.session_state["f_xa"]),
                    "prev_shots": int(st.session_state["f_shots"]), "prev_sot": int(st.session_state["f_sot"]),
                    "prev_chances": int(st.session_state["f_chances"]), "prev_dribbles": int(st.session_state["f_dribbles"]),
                    "prev_touches_box": int(st.session_state["f_touches_box"]), "prev_tackles": int(st.session_state["f_tackles"]),
                    "prev_rating": float(cur_rating), "prev_starts": int(st.session_state.get("f_starts", 25)),
                    "prev_big_chances": int(st.session_state.get("f_big_chances", 2)), "prev_pk": int(st.session_state.get("f_pk", 0)),
                    "prev_pass_pct": float(st.session_state.get("f_pass_pct", 88.2)), "prev_duels_pct": float(st.session_state.get("f_duels_pct", 62.4)),
                    "prev_aerial_pct": float(st.session_state.get("f_aerial_pct", 65.8)),
                    "to_league": in_to_league_choice.split(" (")[0], "proj_mins": int(f_target_mins_t1),
                    "proj_goals": float(pj_goals_t1), "proj_xg": float(pj_xg_t1),
                    "proj_assists": float(pj_assists_t1), "proj_xa": float(pj_xa_t1),
                    "proj_shots": float(pj_shots_t1), "proj_sot": float(pj_sot_t1),
                    "proj_chances": float(pj_chances_t1), "proj_dribbles": float(pj_dribbles_t1),
                    "proj_box": float(pj_box_t1), "proj_tackles": float(pj_tackles_t1),
                    "proj_rating": float(pj_rating_t1), "notes": detailed_notes,
                    "from_team": in_from_team.strip(), "to_team": in_to_team.strip(),
                    "to_league_name": in_to_league_choice.split(" (")[0],
                    "trade_type": "OUT" if is_out_trade else "IN",
                    "weekly_wage": float(weekly_wage_in) if 'weekly_wage_in' in locals() else 0.0,
                    "gk_saves": int(st.session_state.get("f_gk_saves", 0)) if is_gk else 0,
                    "gk_conceded": int(st.session_state.get("f_gk_conceded", 0)) if is_gk else 0,
                    "gk_prevented": float(st.session_state.get("f_gk_prevented", 0.0)) if is_gk else 0.0,
                    "gk_cs": int(st.session_state.get("f_gk_cs", 0)) if is_gk else 0,
                    "gk_errors": int(st.session_state.get("f_gk_errors", 0)) if is_gk else 0,
                    "gk_claims": int(st.session_state.get("f_gk_claims", 0)) if is_gk else 0
                }
                try:
                    res = requests.post(GOOGLE_SHEET_WEBAPP_URL, data=json.dumps(payload), headers={"Content-Type": "text/plain;charset=utf-8"}, timeout=30, allow_redirects=True)
                    res_json = res.json()
                    if res.status_code in [200, 302] and res_json.get("status") == "success":
                        st.session_state["last_saved_msg"] = f"✅ '{player_name}' 선수의 데이터와 구단 로고가 성공적으로 {'수정' if edit_toggle else '저장'}되었습니다!"
                        st.cache_data.clear()
                        st.session_state["current_form"] = default_form_template.copy()
                        st.session_state["form_key_id"] += 1
                        st.rerun()
                    else: st.error(f"⚠️ 저장 실패: {res_json.get('message', '통신 오류')}")
                except Exception as e: st.error(f"⚠️ 저장 오류: {e}")

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
        index=1 if is_winter else 0, horizontal=True, key=f"global_data_source_radio_{k_id}"
    )
    is_winter_mode = "겨울" in winter_data_source

    role_options = [
        "🔥 1티어 핵심 주전 (메인 스타터)",
        "⭐ 2티어 일반 주전 (로테이션 핵심)",
        "⚖️ 3티어 스쿼드 뎁스 / 로테이션 (백업)",
        "🌱 4티어 유망주 / 컵대회 자원 (신예)",
        "✏️ 직접 분 단위로 입력하기"
    ]
    selected_role = st.selectbox("선수의 팀 내 예상 위상 (역할군 선택)", role_options, index=0, key=f"role_selector_{k_id}")

    state_mins_key = f"target_mins_state_{k_id}"
    last_mode_key = f"last_mode_state_{k_id}"
    current_mode_sig = f"{is_winter_mode}_{selected_role}"
    if last_mode_key not in st.session_state or st.session_state[last_mode_key] != current_mode_sig:
        st.session_state[last_mode_key] = current_mode_sig
        if "1티어" in selected_role: st.session_state[state_mins_key] = 1440 if is_winter_mode else 3000
        elif "2티어" in selected_role: st.session_state[state_mins_key] = 1200 if is_winter_mode else 2500
        elif "3티어" in selected_role: st.session_state[state_mins_key] = 900 if is_winter_mode else 1800
        elif "4티어" in selected_role: st.session_state[state_mins_key] = 400 if is_winter_mode else 800

    f_c1, f_c2, f_c3, f_c4 = st.columns(4)
    with f_c1: f_pos = st.selectbox("선수 포지션 분류", ["⚽ 필드 플레이어 (공격수/미드필더/수비수)", "🧤 골키퍼 (Goalkeeper)"], index=1 if "GK" in main_position else 0, key=f"f_tab_pos_{k_id}")
    with f_c2: f_from_l = st.selectbox("원소속 리그 (기록 기준)", list(LEAGUE_WEIGHTS.keys()), index=list(LEAGUE_WEIGHTS.keys()).index(selling_league) if selling_league in LEAGUE_WEIGHTS else 0, key=f"f_tab_from_l_{k_id}")
    with f_c3: f_to_l = st.selectbox("이적할 리그", list(LEAGUE_WEIGHTS.keys()), index=list(LEAGUE_WEIGHTS.keys()).index(in_to_league_choice) if in_to_league_choice in LEAGUE_WEIGHTS else 0, key=f"f_tab_to_l_{k_id}")
    with f_c4:
        default_input_val = st.session_state.get(state_mins_key, 1440 if is_winter_mode else 3000)
        f_target_mins = st.number_input("이적 팀 예상 출전 시간(분)", min_value=90, max_value=4500, value=int(default_input_val), step=90, key=state_mins_key)

    raw_l_factor = LEAGUE_WEIGHTS[f_from_l] / LEAGUE_WEIGHTS[f_to_l]
    if LEAGUE_WEIGHTS[f_to_l] > LEAGUE_WEIGHTS[f_from_l]:
        adapt_penalty = max(0.80, 1.0 - ((LEAGUE_WEIGHTS[f_to_l] - LEAGUE_WEIGHTS[f_from_l]) * 0.45))
        adapt_desc = "상위 리그 스텝업 적응 과정 반영"
    else:
        adapt_penalty = 1.00
        adapt_desc = "동급/하위 리그 이적 (즉시 전력감)"
    final_l_factor = raw_l_factor * adapt_penalty

    st.divider()
    b1, b2, b3, b4 = st.columns(4)
    with b1: in_matches = st.number_input("출전 경기 (Matches)", 1, 60, value=min(int(st.session_state["f_matches"]), 60), key=f"in_matches_box_{k_id}")
    with b2: in_starts = st.number_input("선발 출전 (Starts)", 0, 60, value=min(int(st.session_state["f_starts"]), 60), key=f"in_starts_box_{k_id}")
    with b3: in_mins = st.number_input("출전 시간 (Minutes)", 90, 4500, value=min(int(st.session_state["f_mins"]), 4500), key=f"in_mins_box_{k_id}")
    with b4: in_rating = st.number_input("FotMob 평균 평점", 5.0, 10.0, value=float(st.session_state["f_rating"]), step=0.01, key=f"in_rating_box_{k_id}")

    st.session_state["f_mins"] = in_mins
    st.session_state["f_rating"] = in_rating
    st.session_state["f_matches"] = in_matches
    st.session_state["f_starts"] = in_starts

    base_p90 = in_mins / 90.0 if in_mins > 0 else 1.0
    target_p90 = f_target_mins / 90.0

    if "골키퍼" not in f_pos:
        s1, s2, s3, s4, s5 = st.columns(5)
        with s1: in_goals = st.number_input("득점 (Goals)", 0, 50, value=min(int(st.session_state["f_goals"]), 50), key=f"in_goals_box_{k_id}")
        with s2: in_xg = st.number_input("기대 득점 (xG)", 0.0, 50.0, value=min(float(st.session_state["f_xg"]), 50.0), step=0.01, key=f"in_xg_box_{k_id}")
        with s3: in_shots = st.number_input("총 슈팅 (Shots)", 0, 200, value=min(int(st.session_state["f_shots"]), 200), key=f"in_shots_box_{k_id}")
        with s4: in_sot = st.number_input("유효 슈팅 (On Target)", 0, 100, value=min(int(st.session_state["f_sot"]), 100), key=f"in_sot_box_{k_id}")
        with s5: in_pk_goals = st.number_input("PK 득점 (Penalty)", 0, 20, int(st.session_state.get("f_pk", 0)), key=f"in_pk_box_{k_id}")

        st.session_state["f_goals"], st.session_state["f_xg"], st.session_state["f_shots"], st.session_state["f_sot"], st.session_state["f_pk"] = in_goals, in_xg, in_shots, in_sot, in_pk_goals

        p1, p2, p3, p4, p5 = st.columns(5)
        with p1: in_assists = st.number_input("도움 (Assists)", 0, 50, value=min(int(st.session_state["f_assists"]), 50), key=f"in_assists_box_{k_id}")
        with p2: in_xa = st.number_input("기대 도움 (xA)", 0.0, 50.0, value=min(float(st.session_state["f_xa"]), 50.0), step=0.01, key=f"in_xa_box_{k_id}")
        with p3: in_chances = st.number_input("기회 창출 (Chances)", 0, 150, value=min(int(st.session_state["f_chances"]), 150), key=f"in_chances_box_{k_id}")
        with p4: in_big_chances = st.number_input("빅 찬스 메이킹", 0, 50, value=int(st.session_state.get("f_big_chances", 2)), key=f"in_bc_box_{k_id}")
        with p5: in_pass_pct = st.number_input("패스 성공률 (%)", 30.0, 100.0, value=float(st.session_state.get("f_pass_pct", 88.2)), step=0.1, key=f"in_pass_pct_box_{k_id}")

        st.session_state["f_assists"], st.session_state["f_xa"], st.session_state["f_chances"], st.session_state["f_big_chances"], st.session_state["f_pass_pct"] = in_assists, in_xa, in_chances, in_big_chances, in_pass_pct

        d1, d2, d3, d4, d5 = st.columns(5)
        with d1: in_dribbles = st.number_input("성공한 드리블", 0, 100, value=min(int(st.session_state["f_dribbles"]), 100), key=f"in_dribbles_box_{k_id}")
        with d2: in_touches_box = st.number_input("박스 안 터치", 0, 300, value=min(int(st.session_state["f_touches_box"]), 300), key=f"in_touches_box_{k_id}")
        with d3: in_duels_pct = st.number_input("지상 경합 승률 (%)", 20.0, 100.0, value=float(st.session_state.get("f_duels_pct", 62.4)), step=0.1, key=f"in_duels_box_{k_id}")
        with d4: in_aerial_pct = st.number_input("공중볼 승률 (%)", 20.0, 100.0, value=float(st.session_state.get("f_aerial_pct", 65.8)), step=0.1, key=f"in_aerial_box_{k_id}")
        with d5: in_tackles = st.number_input("태클 성공", 0, 150, value=min(int(st.session_state["f_tackles"]), 150), key=f"in_tackles_box_{k_id}")

        st.session_state["f_dribbles"], st.session_state["f_touches_box"], st.session_state["f_tackles"], st.session_state["f_duels_pct"], st.session_state["f_aerial_pct"] = in_dribbles, in_touches_box, in_tackles, in_duels_pct, in_aerial_pct
    else:
        gk1, gk2, gk3, gk4, gk5, gk6 = st.columns(6)
        with gk1: in_gk_saves = st.number_input("선방", 0, 250, value=int(st.session_state["f_gk_saves"]), key=f"in_gk_saves_box_{k_id}")
        with gk2: in_gk_conceded = st.number_input("실점 수", 0, 120, value=int(st.session_state["f_gk_conceded"]), key=f"in_gk_conceded_box_{k_id}")
        with gk3: in_gk_prevented = st.number_input("득점 차단", -20.0, 30.0, value=float(st.session_state["f_gk_prevented"]), step=0.01, key=f"in_gk_prevented_box_{k_id}")
        with gk4: in_gk_cs = st.number_input("클린 시트", 0, 35, value=int(st.session_state["f_gk_cs"]), key=f"in_gk_cs_box_{k_id}")
        with gk5: in_gk_errors = st.number_input("골 실수", 0, 15, value=int(st.session_state["f_gk_errors"]), key=f"in_gk_errors_box_{k_id}")
        with gk6: in_gk_claims = st.number_input("공중볼 잡기", 0, 80, value=int(st.session_state["f_gk_claims"]), key=f"in_gk_claims_box_{k_id}")

        st.session_state["f_gk_saves"], st.session_state["f_gk_conceded"], st.session_state["f_gk_prevented"], st.session_state["f_gk_cs"], st.session_state["f_gk_errors"], st.session_state["f_gk_claims"] = in_gk_saves, in_gk_conceded, in_gk_prevented, in_gk_cs, in_gk_errors, in_gk_claims
        in_goals = in_shots = in_sot = in_assists = in_chances = in_dribbles = in_touches_box = in_tackles = 0
        in_xg = in_xa = 0.0

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
        proj_sot = round(p90_sot * target_p90, 0)
        proj_chances = round(p90_chances * target_p90, 0)
        proj_dribbles = round(p90_dribbles * target_p90, 0)
        proj_box_touches = round(p90_box_touches * target_p90, 0)
        proj_tackles = round(p90_tackles * target_p90, 0)
        proj_rating = round(max(6.0, in_rating - (1.0 - final_l_factor) * 0.9), 2)

        season_type_desc = "후반기 잔여 시즌(약 16~19경기)" if is_winter_mode else "1시즌 풀 타임"

        def make_comp_bar_row(label, prev_v, proj_v, max_v, unit=""):
            w1 = min(100, int((prev_v / max_v) * 100)) if max_v > 0 else 10
            w2 = min(100, int((proj_v / max_v) * 100)) if max_v > 0 else 10
            return f"""
            <div style="margin-bottom:11px;">
                <div style="display:flex; justify-content:space-between; font-size:12px; margin-bottom:4px;">
                    <span style="color:#E2E8F0; font-weight:700;">{label}</span>
                    <span><span style="color:#94A3B8;">직전 {prev_v}{unit}</span> &nbsp;➔&nbsp; <b style="color:#38BDF8;">예측 {proj_v}{unit}</b></span>
                </div>
                <div style="display:grid; grid-template-columns:1fr 1fr; gap:8px;">
                    <div style="background:#090D16; height:9px; border-radius:5px; overflow:hidden; border:1px solid #1E293B;"><div style="width:{w1}%; background:linear-gradient(90deg, #475569, #94A3B8); height:100%;"></div></div>
                    <div style="background:#090D16; height:9px; border-radius:5px; overflow:hidden; border:1px solid #1E293B;"><div style="width:{w2}%; background:linear-gradient(90deg, #0284C7, #38BDF8); height:100%;"></div></div>
                </div>
            </div>
            """

        tab2_rad_cats = ['예상 평점', '득점력(xG)', '기회창출(xA)', '슈팅 볼륨', '돌파/박스터치', '수비/경합']
        t2_prev_rad = [int(min(98, max(50, (in_rating - 6.0) * 22 + 52))), int(min(98, max(45, (in_xg / base_p90) * 115 + 45))), int(min(98, max(45, (in_xa / base_p90) * 140 + 45))), int(min(98, max(45, (in_shots / base_p90) * 22 + 40))), int(min(98, max(45, ((in_dribbles + in_touches_box * 0.3) / base_p90) * 18 + 45))), int(min(98, max(45, (in_tackles / base_p90) * 25 + 48)))]
        t2_proj_rad = [int(min(98, max(50, (proj_rating - 6.0) * 22 + 52))), int(min(98, max(45, p90_xg * 115 + 45))), int(min(98, max(45, p90_xa * 140 + 45))), int(min(98, max(45, p90_shots * 22 + 40))), int(min(98, max(45, (p90_dribbles + p90_box_touches * 0.3) * 18 + 45))), int(min(98, max(45, p90_tackles * 25 + 48)))]
        svg_t2_radar = build_svg_radar(tab2_rad_cats, t2_proj_rad, color_a="#38BDF8", values_b=t2_prev_rad, color_b="#64748B", size=310)
        donut_t2_rat = build_svg_donut_ring(proj_rating, 10.0, "#38BDF8", "예상 FotMob 평점", size=105)

        tab2_board_html = f"""
        <div class="glass-panel" style="padding:16px 20px; margin-bottom:16px; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px;">
            <div style="display:flex; align-items:center;">
                {hero_club_emblem_html}
                <div>
                    <div style="font-size:11px; font-weight:800; color:#38BDF8; letter-spacing:1px;">FOTMOB FIRST-SEASON STATISTICAL PROJECTION</div>
                    <div style="font-size:26px; font-weight:900; color:#FFFFFF; margin-top:2px;">📱 {display_name} · 이적 첫 시즌 성적 예측 리포트</div>
                    <div style="font-size:13px; color:#94A3B8; margin-top:4px;">{route_with_logos_html} &nbsp;|&nbsp; 예상 출전: <b>{f_target_mins:,}분 (약 {target_p90:.0f}경기)</b></div>
                </div>
            </div>
            <div>{donut_t2_rat}</div>
        </div>
        <div style="display:grid; grid-template-columns:repeat(4, 1fr); gap:12px; margin-bottom:16px;">
            <div class="kpi-card" style="border-top:3px solid #10B981;"><div style="font-size:11px; color:#94A3B8;">예상 득점 (기대득점)</div><div style="font-size:22px; font-weight:900; color:#10B981; margin-top:4px;">{proj_goals:.1f} 골</div><div style="font-size:11px; color:#64748B;">xG {proj_xg:.2f} (직전 {in_goals}골)</div></div>
            <div class="kpi-card" style="border-top:3px solid #A855F7;"><div style="font-size:11px; color:#94A3B8;">예상 도움 (기대도움)</div><div style="font-size:22px; font-weight:900; color:#C084FC; margin-top:4px;">{proj_assists:.1f} 도움</div><div style="font-size:11px; color:#64748B;">xA {proj_xa:.2f} (직전 {in_assists}도움)</div></div>
            <div class="kpi-card" style="border-top:3px solid #F59E0B;"><div style="font-size:11px; color:#94A3B8;">예상 총 공격포인트</div><div style="font-size:22px; font-weight:900; color:#FBBF24; margin-top:4px;">{proj_goals + proj_assists:.1f} P</div><div style="font-size:11px; color:#64748B;">직전 시즌 {in_goals + in_assists} P</div></div>
            <div class="kpi-card" style="border-top:3px solid #EC4899;"><div style="font-size:11px; color:#94A3B8;">예상 슈팅 (유효슈팅)</div><div style="font-size:22px; font-weight:900; color:#F472B6; margin-top:4px;">{int(proj_shots)} 회</div><div style="font-size:11px; color:#64748B;">유효 슈팅 {int(proj_sot)}회</div></div>
        </div>
        <div style="display:grid; grid-template-columns: 0.95fr 1.15fr; gap:14px; align-items:stretch;">
            <div class="glass-panel" style="padding:14px; text-align:center; display:flex; flex-direction:column; justify-content:center;">
                <div style="font-size:13px; font-weight:900; color:#38BDF8; margin-bottom:4px;">💠 첫 시즌 예측(청색) vs 직전 시즌(회색)</div>
                {svg_t2_radar}
            </div>
            <div class="glass-panel" style="padding:16px;">
                <div style="font-size:13px; font-weight:900; color:#10B981; margin-bottom:12px;">📊 13대 핵심 스탯 직전 기록(좌) vs 첫 시즌 예측(우)</div>
                {make_comp_bar_row("득점 (Goals)", in_goals, proj_goals, 30, "골")}
                {make_comp_bar_row("기대 득점 (xG)", round(in_xg,1), round(proj_xg,1), 30, "")}
                {make_comp_bar_row("도움 (Assists)", in_assists, proj_assists, 20, "도움")}
                {make_comp_bar_row("총 슈팅 / 유효 슈팅", in_shots, int(proj_shots), 120, "회")}
                {make_comp_bar_row("기회 창출 (Chances)", in_chances, int(proj_chances), 90, "회")}
                {make_comp_bar_row("박스 안 터치 (Box Touches)", in_touches_box, int(proj_box_touches), 200, "회")}
                {make_comp_bar_row("태클 성공 (Tackles Won)", in_tackles, int(proj_tackles), 90, "회")}
            </div>
        </div>
        """
        render_copyable_infographic(tab2_board_html, filename=f"projection_{display_name}", height=780)
    else:
        proj_gk_saves = round((in_gk_saves / base_p90) * target_p90 * (1.0 / raw_l_factor), 0)
        proj_gk_conceded = round((in_gk_conceded / base_p90) * target_p90 * (1.0 / final_l_factor), 0)
        proj_gk_prevented = round((in_gk_prevented / base_p90) * target_p90 * final_l_factor, 2)
        proj_gk_cs = round((in_gk_cs / base_p90) * target_p90 * final_l_factor, 0)
        proj_rating = round(max(6.0, in_rating - (1.0 - final_l_factor) * 0.9), 2)
        season_type_desc = "후반기 잔여 시즌" if is_winter_mode else "1시즌 풀 타임"

        gk_board_html = f"""
        <div class="glass-panel" style="padding:16px 20px; margin-bottom:16px; display:flex; justify-content:space-between; align-items:center;">
            <div style="font-size:22px; font-weight:900; color:#FFFFFF;">🧤 {display_name} · 골키퍼 첫 시즌 성적 예측 ({season_type_desc})</div>
            <div style="font-size:13px; color:#34D399; font-weight:700;">{route_with_logos_html} | 예상 {f_target_mins:,}분</div>
        </div>
        <div style="display:grid; grid-template-columns:repeat(5, 1fr); gap:10px; text-align:center;">
            <div class="kpi-card" style="border-top:3px solid #38BDF8;"><div style="font-size:11px; color:#94A3B8;">예상 평점</div><div style="font-size:22px; font-weight:900; color:#38BDF8; margin-top:4px;">★ {proj_rating:.2f}</div><div style="font-size:11px; color:#64748B;">직전 ★{in_rating:.2f}</div></div>
            <div class="kpi-card" style="border-top:3px solid #10B981;"><div style="font-size:11px; color:#94A3B8;">예상 클린시트</div><div style="font-size:22px; font-weight:900; color:#10B981; margin-top:4px;">{int(proj_gk_cs)} 경기</div><div style="font-size:11px; color:#64748B;">직전 {in_gk_cs}경기</div></div>
            <div class="kpi-card" style="border-top:3px solid #A855F7;"><div style="font-size:11px; color:#94A3B8;">예상 득점차단</div><div style="font-size:22px; font-weight:900; color:#C084FC; margin-top:4px;">{proj_gk_prevented:+.2f}</div><div style="font-size:11px; color:#64748B;">직전 {in_gk_prevented:+.2f}</div></div>
            <div class="kpi-card" style="border-top:3px solid #F59E0B;"><div style="font-size:11px; color:#94A3B8;">예상 선방</div><div style="font-size:22px; font-weight:900; color:#FBBF24; margin-top:4px;">{int(proj_gk_saves)} 회</div><div style="font-size:11px; color:#64748B;">직전 {in_gk_saves}회</div></div>
            <div class="kpi-card" style="border-top:3px solid #EF4444;"><div style="font-size:11px; color:#94A3B8;">예상 실점</div><div style="font-size:22px; font-weight:900; color:#F87171; margin-top:4px;">{int(proj_gk_conceded)} 실점</div><div style="font-size:11px; color:#64748B;">직전 {in_gk_conceded}실점</div></div>
        </div>
        """
        render_copyable_infographic(gk_board_html, filename=f"gk_projection_{display_name}", height=360)

# ================= TAB 3: 과거 유사 이적 사례 비교 =================
with tab3:
    st.subheader("🔍 과거 유사 이적 사례 검색 및 벤치마크 비교 (Comps TOP 5 & 10)")

    c_in1, c_in2, c_in3, c_in4, c_in5 = st.columns(5)
    with c_in1: target_fee = st.number_input("비교 기준 이적료 (만 €)", min_value=0, value=int(calc_actual_fee) if calc_actual_fee > 0 else 5000, step=100, key=f"comps_fee_{k_id}")
    with c_in2: target_score = st.number_input("비교 기준 이적 평점", min_value=1.00, max_value=10.00, value=float(final_deal_score) if final_deal_score > 0 else 7.50, step=0.1, key=f"comps_score_{k_id}")
    with c_in3: target_overpay = st.number_input("비교 기준 평가율 (%)", min_value=-100.0, max_value=200.0, value=float(overpay_pct), step=1.0, key=f"comps_overpay_{k_id}")
    with c_in4: pos_filter = st.selectbox("포지션 필터", ["전체 포지션", "스트라이커 (ST/CF)", "윙어/공미 (WG/CAM)", "미드필더 (CM/CDM)", "수비수 (CB/FB/WB)", "골키퍼 (GK)"], index=0, key=f"comps_pos_filter_{k_id}")
    with c_in5: league_filter = st.selectbox("원소속 리그 필터", ["전체 리그"] + list(LEAGUE_WEIGHTS.keys()), index=0, key=f"comps_league_filter_{k_id}")

    st.markdown("---")
    if history_df.empty or "선수명" not in history_df.columns:
        st.info("💡 아직 구글 시트에 누적된 과거 이적 데이터가 없습니다.")
    else:
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

                if pos_filter != "전체 포지션":
                    pos_match_map = {
                        "스트라이커 (ST/CF)": ["스트라이커", "센터포워드", "ST", "CF"],
                        "윙어/공미 (WG/CAM)": ["윙어", "공격형", "WG", "CAM"],
                        "미드필더 (CM/CDM)": ["중앙", "수비형", "미드필더", "CM", "CDM"],
                        "수비수 (CB/FB/WB)": ["센터백", "풀백", "윙백", "수비", "CB", "RB", "LB", "WB"],
                        "골키퍼 (GK)": ["골키퍼", "GK"]
                    }
                    if not any(kw in p_pos for kw in pos_match_map.get(pos_filter, [])): continue

                if league_filter != "전체 리그" and league_filter.split(" (")[0] not in p_league: continue

                fee_diff_norm = abs(p_fee - target_fee) / (max(target_fee, 1000) * 1.5)
                score_diff_norm = abs(p_score - target_score) / 5.0
                overpay_diff_norm = abs(p_overpay - target_overpay) / 50.0
                target_l_w = LEAGUE_WEIGHTS.get(selling_league, 1.0)
                row_l_w = next((l_v for l_k, l_v in LEAGUE_WEIGHTS.items() if p_league in l_k), 0.80)
                league_diff_norm = abs(target_l_w - row_l_w) / 0.70

                total_dist = (fee_diff_norm * 0.30) + (score_diff_norm * 0.25) + (overpay_diff_norm * 0.25) + (league_diff_norm * 0.20)
                sim_pct = max(0.0, round((1.0 - total_dist) * 100, 1))

                valid_rows.append({
                    "시즌": p_season, "선수명": p_name, "포지션": p_pos, "원소속리그": p_league,
                    "실제이적료(만€)": p_fee, "산출적정가(만€)": p_fair, "평가율(%)": round(p_overpay, 1),
                    "이적평점": round(p_score, 2), "유사도(%)": sim_pct, "스카우팅메모": clean_notes_display(str(row.get("스카우팅메모", "")))
                })
            except Exception: continue

        if valid_rows:
            match_df = pd.DataFrame(valid_rows).sort_values(by="유사도(%)", ascending=False).head(10)
            top5_df = match_df.head(5)

            cards_html_items = ""
            for idx_c, r_c in top5_df.reset_index(drop=True).iterrows():
                sim_v = r_c['유사도(%)']
                cards_html_items += f"""
                <div class="glass-panel" style="padding:15px;">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
                        <span style="font-size:16.5px; font-weight:900; color:#38BDF8;">{idx_c+1}위. {r_c['선수명']} <span style="font-size:12px; color:#94A3B8;">({r_c['시즌']})</span></span>
                        <span style="background:rgba(16,185,129,0.18); border:1px solid #10B981; color:#34D399; font-weight:900; padding:3px 10px; border-radius:20px; font-size:12px;">일치도 {sim_v}%</span>
                    </div>
                    <div style="background:#090D16; height:6px; border-radius:3px; overflow:hidden; margin-bottom:8px;"><div style="width:{sim_v}%; background:linear-gradient(90deg, #0284C7, #10B981); height:100%;"></div></div>
                    <div style="font-size:12px; color:#CBD5E1; margin-bottom:10px;">포지션: <b>{r_c['포지션']}</b> &nbsp;|&nbsp; 출발리그: <b>{r_c['원소속리그']}</b></div>
                    <div style="display:grid; grid-template-columns:repeat(3, 1fr); gap:6px; background:#090D16; padding:8px; border-radius:8px; text-align:center;">
                        <div><div style="font-size:10px; color:#94A3B8;">실제 이적료</div><div style="font-size:13.5px; font-weight:800;">€{r_c['실제이적료(만€)']:,.0f}만</div></div>
                        <div><div style="font-size:10px; color:#94A3B8;">산출 적정가</div><div style="font-size:13.5px; font-weight:800; color:#10B981;">€{r_c['산출적정가(만€)']:,.1f}만</div></div>
                        <div><div style="font-size:10px; color:#94A3B8;">거래 평점</div><div style="font-size:13.5px; font-weight:800; color:#FBBF24;">★ {r_c['이적평점']:.2f}</div></div>
                    </div>
                </div>
                """

            tab3_board_html = f"""
            <div class="glass-panel" style="padding:14px 20px; display:flex; justify-content:space-between; align-items:center; margin-bottom:14px;">
                <div style="font-size:19px; font-weight:900; color:#FFFFFF;">🔍 '{display_name}' 과거 유사 이적 사례 TOP {len(top5_df)} 벤치마크 보드</div>
                <div style="font-size:12px; color:#38BDF8; font-weight:700;">비교 기준: €{target_fee:,.0f}만 · ★{target_score:.2f} · 괴리율 {target_overpay:+.1f}%</div>
            </div>
            <div style="display:grid; grid-template-columns:repeat(2, 1fr); gap:12px;">
                {cards_html_items}
            </div>
            """
            render_copyable_infographic(tab3_board_html, filename=f"comps_{display_name}", height=580)
            st.dataframe(match_df, use_container_width=True)

_part1_end = True
   # ================= TAB 4: 이적 첫 시즌 최종 성적 입력 & 모델 검증 =================
with tab4:
    st.subheader("🎯 시즌 종료 후 최종 실제 성적 입력 & 모델 예측 정확도 사후 검증")

    @st.cache_data(ttl=60)
    def fetch_validation_data():
        try:
            df = pd.read_csv(VAL_SHEET_CSV_URL)
            if not df.empty and "선수명" in df.columns:
                return df
        except Exception:
            pass
        return pd.DataFrame()

    val_df = fetch_validation_data()

    if val_df.empty or "이적시즌" not in val_df.columns:
        st.info("💡 아직 [검증데이터] 시트에 저장된 데이터가 없습니다.")
    else:
        def check_val_status(r):
            r_str = str(r.get("실제평점", "")).strip()
            m_str = str(r.get("실제출전시간", "")).strip()
            if r_str not in ["", "nan"] and m_str not in ["", "nan", "0"]:
                return "✅ 검증 완료"
            return "⏳ 검증 대기"

        val_df["입력상태"] = val_df.apply(check_val_status, axis=1)
        available_seasons = list(val_df["이적시즌"].dropna().unique())
        v_top1, v_top2 = st.columns([1, 1])
        with v_top1:
            sel_val_season = st.selectbox("이적 시즌 선택", available_seasons, key="val_sel_season")
        filtered_season_df = val_df[val_df["이적시즌"] == sel_val_season]

        completed_df = filtered_season_df[filtered_season_df["입력상태"] == "✅ 검증 완료"].copy()
        completed_cnt = len(completed_df)
        total_in_season = len(filtered_season_df)
        with v_top2:
            st.info(f"📊 **`{sel_val_season}` 검증 진행도**: **총 {total_in_season}명 중 {completed_cnt}명 완료**")

        if completed_cnt > 0:
            with st.expander(f"🏆 [{sel_val_season} 시즌] 내 예측 모델 전체 적중률 종합 성적표 ({completed_cnt}명 검증 완료 기준)", expanded=True):
                try:
                    c_proj_r = completed_df["예측평점"].astype(float)
                    c_act_r = completed_df["실제평점"].astype(float)
                    r_errors = (c_act_r - c_proj_r).abs()
                    r_acc_series = ((1.0 - (r_errors / 1.5)) * 100.0).clip(lower=0.0)
                    completed_df["_개별적중률"] = r_acc_series.round(1)
                    best_pred_row = completed_df.sort_values(by="_개별적중률", ascending=False).iloc[0]

                    va1, va2, va3 = st.columns(3)
                    va1.metric("모델 전체 평균 평점 적중률", f"{r_acc_series.mean():.1f}%", f"{completed_cnt}명 표본 평균")
                    va2.metric("평점 평균 절대 오차 (MAE)", f"±{r_errors.mean():.2f}점", "0.00에 가까울수록 정밀")
                    va3.metric("최고 적중 선수 (Best Hit)", f"{best_pred_row.get('선수명', '-')}", f"적중률 {best_pred_row['_개별적중률']:.1f}%")
                except Exception:
                    pass

        show_pending_only = st.checkbox("⏳ 실제 성적 미입력(검증 대기) 선수만 모아보기", value=False, key="filter_pending_only")
        target_player_pool = filtered_season_df[filtered_season_df["입력상태"] == "⏳ 검증 대기"] if show_pending_only else filtered_season_df
        available_players = list(target_player_pool["선수명"].dropna().unique())

        if available_players:
            sel_val_player = st.selectbox(f"선수 선택 ({len(available_players)}명 대상)", available_players, key="val_sel_player")
            target_row = target_player_pool[target_player_pool["선수명"] == sel_val_player].iloc[-1]
            v_ukey = f"{sel_val_season}_{sel_val_player}"

            p_pos = str(target_row.get("포지션", "CB"))
            p_to_l = str(target_row.get("이적리그", "EPL"))
            proj_m = float(target_row.get("예측출전시간", 3000)) if pd.notnull(target_row.get("예측출전시간")) else 3000.0
            proj_g = float(target_row.get("예측득점", 0)) if pd.notnull(target_row.get("예측득점")) else 0.0
            proj_xg = float(target_row.get("예측xG", 0)) if pd.notnull(target_row.get("예측xG")) else 0.0
            proj_a = float(target_row.get("예측도움", 0)) if pd.notnull(target_row.get("예측도움")) else 0.0
            proj_xa = float(target_row.get("예측xA", 0)) if pd.notnull(target_row.get("예측xA")) else 0.0
            proj_r = float(target_row.get("예측평점", 7.0)) if pd.notnull(target_row.get("예측평점")) else 7.0

            exist_act_mins = int(target_row.get("실제출전시간", proj_m)) if pd.notnull(target_row.get("실제출전시간")) and str(target_row.get("실제출전시간")).strip() not in ["", "nan"] else int(proj_m)
            exist_act_rating = float(target_row.get("실제평점", proj_r)) if pd.notnull(target_row.get("실제평점")) and str(target_row.get("실제평점")).strip() not in ["", "nan"] else float(proj_r)
            exist_act_notes = str(target_row.get("검증메모", "")) if pd.notnull(target_row.get("검증메모")) else ""
            is_gk_target = "GK" in p_pos or "골키퍼" in p_pos

            def get_int_val(col, def_v):
                v = target_row.get(col, def_v)
                if pd.notnull(v) and str(v).strip() not in ["", "nan"]:
                    return int(float(v))
                return def_v

            def get_flt_val(col, def_v):
                v = target_row.get(col, def_v)
                if pd.notnull(v) and str(v).strip() not in ["", "nan"]:
                    return float(v)
                return def_v

            if not is_gk_target:
                in_ac1, in_ac2, in_ac3, in_ac4, in_ac5, in_ac6 = st.columns(6)
                with in_ac1: act_mins_val = st.number_input("실제 출전 시간(분)", 0, 4500, value=exist_act_mins, step=90, key=f"val_act_mins_{v_ukey}")
                with in_ac2: act_goals_val = st.number_input("실제 득점(Goals)", 0, 60, value=get_int_val("실제득점", int(round(proj_g))), step=1, key=f"val_act_goals_{v_ukey}")
                with in_ac3: act_xg_val = st.number_input("실제 기대득점(xG)", 0.0, 50.0, value=get_flt_val("실제xG", float(proj_xg)), step=0.01, key=f"val_act_xg_{v_ukey}")
                with in_ac4: act_assists_val = st.number_input("실제 도움(Assists)", 0, 40, value=get_int_val("실제도움", int(round(proj_a))), step=1, key=f"val_act_assists_{v_ukey}")
                with in_ac5: act_xa_val = st.number_input("실제 기대도움(xA)", 0.0, 30.0, value=get_flt_val("실제xA", float(proj_xa)), step=0.01, key=f"val_act_xa_{v_ukey}")
                with in_ac6: act_rating_val = st.number_input("실제 FotMob 평점", 4.0, 10.0, value=exist_act_rating, step=0.01, key=f"val_act_rating_{v_ukey}")

                in_bc1, in_bc2, in_bc3, in_bc4, in_bc5, in_bc6 = st.columns(6)
                with in_bc1: act_shots_val = st.number_input("실제 총 슈팅", 0, 200, value=get_int_val("실제총슈팅", 40), key=f"val_act_shots_{v_ukey}")
                with in_bc2: act_sot_val = st.number_input("실제 유효 슈팅", 0, 100, value=get_int_val("실제유효슈팅", 15), key=f"val_act_sot_{v_ukey}")
                with in_bc3: act_chances_val = st.number_input("실제 기회 창출", 0, 150, value=get_int_val("실제기회창출", 20), key=f"val_act_chances_{v_ukey}")
                with in_bc4: act_dribbles_val = st.number_input("실제 성공 드리블", 0, 100, value=get_int_val("실제성공드리블", 15), key=f"val_act_dribbles_{v_ukey}")
                with in_bc5: act_box_val = st.number_input("실제 박스 터치", 0, 300, value=get_int_val("실제박스터치", 50), key=f"val_act_box_{v_ukey}")
                with in_bc6: act_tackles_val = st.number_input("실제 태클 성공", 0, 150, value=get_int_val("실제태클성공", 25), key=f"val_act_tackles_{v_ukey}")

                in_cc1, in_cc2, in_cc3, in_cc4, in_cc5 = st.columns(5)
                with in_cc1: act_big_chances_val = st.number_input("실제 빅찬스 메이킹", 0, 50, value=get_int_val("실제빅찬스메이킹", 5), key=f"val_act_bc_{v_ukey}")
                with in_cc2: act_pk_val = st.number_input("실제 PK 득점", 0, 20, value=get_int_val("실제PK득점", 0), key=f"val_act_pk_{v_ukey}")
                with in_cc3: act_pass_pct_val = st.number_input("실제 패스 성공률(%)", 30.0, 100.0, value=get_flt_val("실제패스성공률", 85.0), step=0.1, key=f"val_act_pass_{v_ukey}")
                with in_cc4: act_duels_pct_val = st.number_input("실제 지상경합승률(%)", 20.0, 100.0, value=get_flt_val("실제지상경합승률", 60.0), step=0.1, key=f"val_act_duels_{v_ukey}")
                with in_cc5: act_aerial_pct_val = st.number_input("실제 공중볼승률(%)", 20.0, 100.0, value=get_flt_val("실제공중볼승률", 55.0), step=0.1, key=f"val_act_aerial_{v_ukey}")
                act_gk_saves_val = act_gk_conceded_val = act_gk_cs_val = act_gk_errors_val = act_gk_claims_val = 0
                act_gk_prevented_val = 0.0
            else:
                gk_c1, gk_c2, gk_c3, gk_c4 = st.columns(4)
                with gk_c1: act_mins_val = st.number_input("실제 출전 시간(분)", 0, 4500, value=exist_act_mins, step=90, key=f"val_act_mins_gk_{v_ukey}")
                with gk_c2: act_rating_val = st.number_input("실제 FotMob 평점", 4.0, 10.0, value=exist_act_rating, step=0.01, key=f"val_act_rating_gk_{v_ukey}")
                with gk_c3: act_gk_saves_val = st.number_input("실제 선방", 0, 250, value=get_int_val("실제선방", 80), key=f"val_act_gksaves_{v_ukey}")
                with gk_c4: act_gk_conceded_val = st.number_input("실제 실점 수", 0, 120, value=get_int_val("실제실점", 35), key=f"val_act_gkconc_{v_ukey}")
                gk_c5, gk_c6, gk_c7, gk_c8 = st.columns(4)
                with gk_c5: act_gk_prevented_val = st.number_input("실제 득점 차단", -20.0, 30.0, value=get_flt_val("실제득점차단", 1.5), step=0.01, key=f"val_act_gkprev_{v_ukey}")
                with gk_c6: act_gk_cs_val = st.number_input("실제 클린 시트", 0, 35, value=get_int_val("실제클린시트", 10), key=f"val_act_gkcs_{v_ukey}")
                with gk_c7: act_gk_errors_val = st.number_input("실제 골 실수", 0, 15, value=get_int_val("실제실수", 0), key=f"val_act_gkerr_{v_ukey}")
                with gk_c8: act_gk_claims_val = st.number_input("실제 공중볼 잡기", 0, 80, value=get_int_val("실제공중볼", 15), key=f"val_act_gkclaims_{v_ukey}")
                act_goals_val = act_assists_val = act_shots_val = act_sot_val = act_chances_val = act_dribbles_val = act_box_val = act_tackles_val = act_big_chances_val = act_pk_val = 0
                act_xg_val = act_xa_val = act_pass_pct_val = act_duels_pct_val = act_aerial_pct_val = 0.0

            act_notes_val = st.text_input("사후 검증 스카우팅 총평 / 비고", value=exist_act_notes, key=f"val_act_notes_{v_ukey}")
            rating_accuracy = max(0.0, round((1.0 - (abs(act_rating_val - proj_r) / 1.5)) * 100, 1))
            mins_diff = act_mins_val - proj_m

            kpi3_title = "실제 득점 (xG)" if not is_gk_target else "실제 선방"
            kpi3_val = f"{act_goals_val}골 (xG {act_xg_val:.2f})" if not is_gk_target else f"{act_gk_saves_val}회"
            kpi3_sub = f"예측 {proj_g:.1f}골 (xG {proj_xg:.2f})" if not is_gk_target else f"실점 {act_gk_conceded_val}"
            kpi4_title = "실제 도움 (xA)" if not is_gk_target else "실제 클린시트"
            kpi4_val = f"{act_assists_val}도움 (xA {act_xa_val:.2f})" if not is_gk_target else f"{act_gk_cs_val}경기"
            kpi4_sub = f"예측 {proj_a:.1f}도움 (xA {proj_xa:.2f})" if not is_gk_target else f"득점차단 {act_gk_prevented_val:+.2f}"

            val_board_html = f"""
            <div class="glass-panel" style="padding:14px 20px; display:flex; justify-content:space-between; align-items:center; margin-bottom:16px;">
                <div style="font-size:19px; font-weight:900; color:#FFFFFF;">🎯 '{sel_val_player}' ({sel_val_season}) 모델 예측 적중 최종 검증 리포트</div>
                <div style="font-size:13px; color:#34D399; font-weight:700;">포지션: {p_pos} | 활약리그: {p_to_l}</div>
            </div>
            <div style="display:grid; grid-template-columns:repeat(4, 1fr); gap:10px; text-align:center;">
                <div class="kpi-card" style="border-top:3px solid #10B981;"><div style="font-size:11px; color:#6EE7B7;">평점 예측 적중률</div><div style="font-size:24px; font-weight:900; color:#10B981; margin-top:4px;">{rating_accuracy}%</div><div style="font-size:11px; color:#94A3B8;">예측 ★{proj_r:.2f} vs 실제 ★{act_rating_val:.2f}</div></div>
                <div class="kpi-card" style="border-top:3px solid #38BDF8;"><div style="font-size:11px; color:#94A3B8;">실제 출전 시간</div><div style="font-size:20px; font-weight:800; color:#38BDF8; margin-top:4px;">{act_mins_val:,}분</div><div style="font-size:11px; color:#64748B;">예측 {int(proj_m):,}분 ({mins_diff:+,.0f}분)</div></div>
                <div class="kpi-card" style="border-top:3px solid #A855F7;"><div style="font-size:11px; color:#94A3B8;">{kpi3_title}</div><div style="font-size:20px; font-weight:800; color:#C084FC; margin-top:4px;">{kpi3_val}</div><div style="font-size:11px; color:#64748B;">{kpi3_sub}</div></div>
                <div class="kpi-card" style="border-top:3px solid #F59E0B;"><div style="font-size:11px; color:#94A3B8;">{kpi4_title}</div><div style="font-size:20px; font-weight:800; color:#FBBF24; margin-top:4px;">{kpi4_val}</div><div style="font-size:11px; color:#64748B;">{kpi4_sub}</div></div>
            </div>
            """
            render_copyable_infographic(val_board_html, filename=f"validation_{sel_val_player}", height=340)

            if st.button("🚀 '검증데이터' 시트에 최종 실제 성적 전체 업데이트하기", type="primary", use_container_width=True, key=f"update_actual_btn_{v_ukey}"):
                update_payload = {
                    "action": "update_actual", "season": sel_val_season, "name": sel_val_player,
                    "act_mins": int(act_mins_val), "act_goals": int(act_goals_val), "act_xg": float(act_xg_val),
                    "act_assists": int(act_assists_val), "act_xa": float(act_xa_val), "act_shots": int(act_shots_val),
                    "act_sot": int(act_sot_val), "act_chances": int(act_chances_val), "act_dribbles": int(act_dribbles_val),
                    "act_box": int(act_box_val), "act_tackles": int(act_tackles_val), "act_rating": float(act_rating_val),
                    "act_big_chances": int(act_big_chances_val), "act_pk": int(act_pk_val), "act_pass_pct": float(act_pass_pct_val),
                    "act_duels_pct": float(act_duels_pct_val), "act_aerial_pct": float(act_aerial_pct_val),
                    "act_gk_saves": int(act_gk_saves_val), "act_gk_conceded": int(act_gk_conceded_val),
                    "act_gk_prevented": float(act_gk_prevented_val), "act_gk_cs": int(act_gk_cs_val),
                    "act_gk_errors": int(act_gk_errors_val), "act_gk_claims": int(act_gk_claims_val),
                    "rating_accuracy": float(rating_accuracy), "notes": act_notes_val
                }
                res = requests.post(GOOGLE_SHEET_WEBAPP_URL, data=json.dumps(update_payload), headers={"Content-Type": "text/plain;charset=utf-8"}, timeout=30, allow_redirects=True)
                if res.json().get("status") == "success":
                    st.success("✅ 실제 성적이 업데이트되었습니다!")
                    st.cache_data.clear()
                    st.rerun()

        st.markdown("---")
        st.dataframe(val_df, use_container_width=True)

# ================= TAB 5: 시즌 중 라운드별 중간 점검 시뮬레이터 (시트 미저장 · 메모장) =================
with tab5:
    st.subheader("⏱️ 시즌 중 라운드별 중간 점검 시뮬레이터 (In-Season Pace Tracker · 시트 미저장)")
    st.info("💡 **구글 시트에 저장하지 않고** 시즌 도중(예: 10R, 19R 반환점, 25R 등)에 선수의 현재 기록을 넣으면, **현재 라운드 기준 기대 목표치 대비 달성도**와 **시즌 완주 시 최종 예상 페이스(Pace)**를 즉석 계산하여 구단 로고가 포함된 인포그래픽 이미지 및 메모장으로 뽑아줍니다.")

    use_sheet_player = st.toggle("📂 시트에 저장된 기존 선수 목표치 불러오기", value=True if not history_df.empty else False)
    
    if use_sheet_player and not history_df.empty and "선수명" in history_df.columns:
        p_list_ms = [str(x).strip() for x in history_df["선수명"].dropna().unique() if str(x).strip() not in ["", "nan"]]
        sel_ms_p = st.selectbox("점검할 선수 선택", p_list_ms, key="ms_sel_p")
        ms_row = history_df[history_df["선수명"] == sel_ms_p].iloc[-1].to_dict()
        ms_name_def = str(ms_row.get("선수명", "선수"))
        ms_team_def = str(ms_row.get("이적팀명", "소속팀"))
        ms_pos_def = str(ms_row.get("포지션", "ST"))
        ms_fee_def = float(find_val(ms_row, ["실제이적료", "이적료"], 5000.0))
        ms_proj_m_def = int(find_val(ms_row, ["예측출전시간", "proj_mins"], 3000))
        ms_proj_g_def = float(find_val(ms_row, ["예측득점", "proj_goals"], 12.0))
        ms_proj_a_def = float(find_val(ms_row, ["예측도움", "proj_assists"], 5.0))
        ms_proj_r_def = float(find_val(ms_row, ["예측평점", "proj_rating"], 7.15))
    else:
        ms_name_def = player_name.strip() if player_name.strip() else "중간점검 선수"
        ms_team_def = in_to_team.strip() if in_to_team.strip() else "영입 구단"
        ms_pos_def = pos_short
        ms_fee_def = float(calc_actual_fee)
        ms_proj_m_def = int(f_target_mins_t1)
        ms_proj_g_def = float(pj_goals_t1)
        ms_proj_a_def = float(pj_assists_t1)
        ms_proj_r_def = float(pj_rating_t1)

    st.markdown("##### 1️⃣ 시즌 진행 라운드 및 1시즌 전체 목표치(기준점) 설정")
    r_col1, r_col2, r_col3, r_col4, r_col5, r_col6 = st.columns(6)
    with r_col1: ms_name = st.text_input("선수명", value=ms_name_def, key="ms_in_name")
    with r_col2: ms_total_r = st.number_input("리그 총 라운드", 20, 46, value=38, step=2, key="ms_tot_r")
    with r_col3: ms_curr_r = st.number_input("현재 진행 라운드(R)", 1, 46, value=15, step=1, key="ms_cur_r")
    with r_col4: ms_full_m = st.number_input("1시즌 목표 출전(분)", 300, 4500, value=ms_proj_m_def, step=90, key="ms_fm")
    with r_col5: ms_full_g = st.number_input("1시즌 목표 득점", 0.0, 50.0, value=ms_proj_g_def, step=0.5, key="ms_fg")
    with r_col6: ms_full_a = st.number_input("1시즌 목표 도움", 0.0, 40.0, value=ms_proj_a_def, step=0.5, key="ms_fa")

    st.markdown("##### 2️⃣ 현재 라운드까지의 실제 기록 입력 (FotMob 기준)")
    a_col1, a_col2, a_col3, a_col4, a_col5, a_col6 = st.columns(6)
    prog_ratio = min(1.0, ms_curr_r / ms_total_r) if ms_total_r > 0 else 0.5
    with a_col1: ms_act_m = st.number_input("현재 실제 출전(분)", 0, 4500, value=int(round(ms_full_m * prog_ratio)), step=45, key="ms_am")
    with a_col2: ms_act_g = st.number_input("현재 실제 득점", 0, 50, value=int(round(ms_full_g * prog_ratio)), step=1, key="ms_ag")
    with a_col3: ms_act_xg = st.number_input("현재 실제 xG", 0.0, 50.0, value=round(ms_full_g * prog_ratio, 2), step=0.1, key="ms_axg")
    with a_col4: ms_act_a = st.number_input("현재 실제 도움", 0, 40, value=int(round(ms_full_a * prog_ratio)), step=1, key="ms_aa")
    with a_col5: ms_act_xa = st.number_input("현재 실제 xA", 0.0, 40.0, value=round(ms_full_a * prog_ratio, 2), step=0.1, key="ms_axa")
    with a_col6: ms_act_r = st.number_input("현재 FotMob 평점", 4.0, 10.0, value=ms_proj_r_def, step=0.01, key="ms_ar")

    exp_now_m = round(ms_full_m * prog_ratio, 0)
    exp_now_g = round(ms_full_g * prog_ratio, 1)
    exp_now_a = round(ms_full_a * prog_ratio, 1)
    exp_now_p = round(exp_now_g + exp_now_a, 1)

    pace_full_m = int(round(ms_act_m / prog_ratio)) if prog_ratio > 0 else 0
    pace_full_g = round(ms_act_g / prog_ratio, 1) if prog_ratio > 0 else 0.0
    pace_full_a = round(ms_act_a / prog_ratio, 1) if prog_ratio > 0 else 0.0
    pace_full_p = round(pace_full_g + pace_full_a, 1)

    m_ratio = min(1.25, ms_act_m / max(180.0, exp_now_m))
    p_diff_now = (ms_act_g + ms_act_a) - exp_now_p
    r_diff_now = ms_act_r - ms_proj_r_def
    in_season_score = round(max(1.0, min(10.0, 7.50 + r_diff_now * 3.0 + p_diff_now * 0.25 + (m_ratio - 1.0) * 1.5)), 2)

    if in_season_score >= 8.5: ms_verdict, ms_col = "🔥 기대치 초과 폭격 (초대박 페이스)", "#10B981"
    elif in_season_score >= 7.3: ms_verdict, ms_col = "✅ 소프트 랜딩 & 순항 중 (기대치 부합)", "#38BDF8"
    elif in_season_score >= 6.2: ms_verdict, ms_col = "⚠️ 적응기 지연 (분발 필요)", "#FBBF24"
    else: ms_verdict, ms_col = "🚨 심각한 부진 / 먹튀 경보", "#EF4444"

    donut_ms = build_svg_donut_ring(in_season_score, 10.0, ms_col, f"{ms_curr_r}R 중간평점", size=110)
    donut_prog = build_svg_donut_ring(prog_ratio * 100.0, 100.0, "#38BDF8", f"{ms_curr_r}/{ms_total_r}R 진행률", size=110)

    ms_logo_url = resolve_club_logo(ms_team_def)
    ms_emblem_html = (
        f"<div style='width:70px; height:70px; border-radius:16px; background:#0F172A; border:2px solid #38BDF8; display:flex; align-items:center; justify-content:center; padding:6px; margin-right:16px; flex-shrink:0;'>"
        f"<img src='{ms_logo_url}' style='width:100%; height:100%; object-fit:contain; filter:drop-shadow(0 2px 4px rgba(0,0,0,0.65));'/></div>"
        if ms_logo_url else ""
    )

    ms_board_html = f"""
    <div class="glass-panel" style="padding:18px 22px; margin-bottom:16px; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:14px;">
        <div style="display:flex; align-items:center;">
            {ms_emblem_html}
            <div>
                <div style="font-size:11px; font-weight:900; color:#38BDF8; letter-spacing:1px;">IN-SEASON PACE & PERFORMANCE TRACKER ({ms_curr_r}R / {ms_total_r}R)</div>
                <div style="font-size:28px; font-weight:900; color:#FFFFFF; margin-top:3px;">⏱️ {ms_name} <span style="font-size:15px; color:#94A3B8;">({ms_team_def} · {ms_pos_def} · 이적료 €{ms_fee_def:,.0f}만)</span></div>
                <div style="font-size:14px; font-weight:800; color:{ms_col}; margin-top:6px;">중간 진단: {ms_verdict}</div>
            </div>
        </div>
        <div style="display:flex; gap:14px;">
            <div>{donut_prog}</div>
            <div>{donut_ms}</div>
        </div>
    </div>

    <div style="display:grid; grid-template-columns:repeat(4, 1fr); gap:12px; margin-bottom:16px;">
        <div class="kpi-card" style="border-top:3px solid #38BDF8;">
            <div style="font-size:11px; color:#94A3B8;">출전 시간 (현재 vs 기대)</div>
            <div style="font-size:21px; font-weight:900; color:#38BDF8; margin-top:4px;">{ms_act_m:,}분</div>
            <div style="font-size:11px; color:#CBD5E1;">{ms_curr_r}R 기대치: {int(exp_now_m):,}분 ({ms_act_m - int(exp_now_m):+,}분)</div>
        </div>
        <div class="kpi-card" style="border-top:3px solid #10B981;">
            <div style="font-size:11px; color:#94A3B8;">현재 득점 (실제 vs 기대)</div>
            <div style="font-size:21px; font-weight:900; color:#10B981; margin-top:4px;">{ms_act_g}골 <span style="font-size:12px; color:#6EE7B7;">(xG {ms_act_xg:.2f})</span></div>
            <div style="font-size:11px; color:#CBD5E1;">{ms_curr_r}R 기대치: {exp_now_g:.1f}골 ({ms_act_g - exp_now_g:+.1f})</div>
        </div>
        <div class="kpi-card" style="border-top:3px solid #A855F7;">
            <div style="font-size:11px; color:#94A3B8;">현재 도움 (실제 vs 기대)</div>
            <div style="font-size:21px; font-weight:900; color:#C084FC; margin-top:4px;">{ms_act_a}도움 <span style="font-size:12px; color:#D8B4FE;">(xA {ms_act_xa:.2f})</span></div>
            <div style="font-size:11px; color:#CBD5E1;">{ms_curr_r}R 기대치: {exp_now_a:.1f}도움 ({ms_act_a - exp_now_a:+.1f})</div>
        </div>
        <div class="kpi-card" style="border-top:3px solid #F59E0B;">
            <div style="font-size:11px; color:#94A3B8;">FotMob 평점 (실제 vs 예상)</div>
            <div style="font-size:21px; font-weight:900; color:#FBBF24; margin-top:4px;">★ {ms_act_r:.2f}</div>
            <div style="font-size:11px; color:#CBD5E1;">시즌전 예상: ★{ms_proj_r_def:.2f} ({r_diff_now:+.2f})</div>
        </div>
    </div>

    <div class="glass-panel" style="padding:16px 20px;">
        <div style="font-size:13.5px; font-weight:900; color:#34D399; margin-bottom:10px;">🚀 현재 페이스 유지 시 {ms_total_r}라운드 완주 최종 예상 성적 (Full-Season On-Pace Projection)</div>
        <div style="display:grid; grid-template-columns:repeat(4, 1fr); gap:10px; background:#090D16; padding:12px; border-radius:12px; text-align:center; font-size:13px;">
            <div><span style="color:#94A3B8; font-size:11px;">최종 출전 페이스</span><br><b style="font-size:16px; color:#F8FAFC;">{pace_full_m:,}분</b> <span style="font-size:11px; color:#64748B;">(목표 {ms_full_m:,}분)</span></div>
            <div><span style="color:#94A3B8; font-size:11px;">최종 득점 페이스</span><br><b style="font-size:16px; color:#10B981;">{pace_full_g:.1f}골</b> <span style="font-size:11px; color:#64748B;">(목표 {ms_full_g:.1f}골)</span></div>
            <div><span style="color:#94A3B8; font-size:11px;">최종 도움 페이스</span><br><b style="font-size:16px; color:#C084FC;">{pace_full_a:.1f}도움</b> <span style="font-size:11px; color:#64748B;">(목표 {ms_full_a:.1f}도움)</span></div>
            <div><span style="color:#94A3B8; font-size:11px;">최종 공포 페이스</span><br><b style="font-size:16px; color:#FBBF24;">{pace_full_p:.1f} P</b> <span style="font-size:11px; color:#64748B;">(목표 {ms_full_g+ms_full_a:.1f}P)</span></div>
        </div>
    </div>
    """
    render_copyable_infographic(ms_board_html, filename=f"midseason_{ms_name}_{ms_curr_r}R", height=520)

    with st.expander("📋 [블로그/카페 본문용] 시즌 중 라운드별 중간 점검 텍스트 메모장 복사", expanded=True):
        memo_txt = (
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"⏱️ [{ms_curr_r}R / {ms_total_r}R 중간 점검] {ms_name} ({ms_team_def} · 진행률 {prog_ratio*100:.1f}%)\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"• 현재 라운드 성적 : {ms_act_m:,}분 출전 | {ms_act_g}골(xG {ms_act_xg:.2f}) · {ms_act_a}도움(xA {ms_act_xa:.2f}) | 평점 ★{ms_act_r:.2f}\n"
            f"• {ms_curr_r}R 시점 기대치 : {int(exp_now_m):,}분 출전 | {exp_now_g:.1f}골 · {exp_now_a:.1f}도움 (공격P {p_diff_now:+.1f}P 격차)\n"
            f"• {ms_total_r}R 완주 환산 페이스 : 최종 {pace_full_m:,}분 · {pace_full_g:.1f}골 {pace_full_a:.1f}도움 ({pace_full_p:.1f}P) 페이스\n"
            f"• 중간 점검 평점 : ★ {in_season_score:.2f} / 10.00 ({ms_verdict})\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        )
        st.code(memo_txt, language="text")

# ================= TAB 6: 과거 선수 대조 & 영입 후보 A vs B 비교 시뮬레이터 =================
with tab6:
    st.subheader("👥 과거 선수 1:1 대조 & 영입 후보 A vs B 즉석 동시 비교 시뮬레이터")

    def calc_pos_custom_metric(pos_text, p90_xg_xa, duels_avg_pct, p90_tkl, pass_pct, gk_prev, gk_cs_or_saves):
        if any(k in pos_text for k in ["GK", "골키퍼"]):
            idx = int(round(min(98, max(45, 70 + gk_prev * 4.5 + gk_cs_or_saves * 0.4))))
            return "선방·골문 지배력", idx, f"득점차단 {gk_prev:+.2f}"
        elif any(k in pos_text for k in ["CB", "RB", "LB", "WB", "CM", "CDM", "센터백", "풀백", "윙백", "중앙", "수비형", "미드필더"]):
            raw_sc = (duels_avg_pct - 45.0) * 1.15 + (p90_tkl * 11.5) + max(0.0, (pass_pct - 75.0) * 0.5) + 46.0
            idx = int(round(min(98, max(45, raw_sc))))
            return "수비·경합 지배력", idx, f"경합 {duels_avg_pct:.1f}% · 태클 {p90_tkl:.2f}"
        else:
            idx = int(round(min(98, max(45, p90_xg_xa * 95.0 + 42.0))))
            return "90분당 공격생산력", idx, f"90분당 xG+xA {p90_xg_xa:.2f}"

    bench_mode = st.radio(
        "비교 분석 모드 선택",
        [
            "⚖️ 영입 후보 A vs 후보 B 즉석 동시 비교 시뮬레이터 (포지션 맞춤형 스탯 자동 적용)",
            "🗂️ 신규 분석 선수 (1번 탭) vs 구글 시트 과거 저장 선수 1:1 대조 (Historical Head-to-Head)"
        ],
        horizontal=True, key="tab6_mode_radio"
    )
    st.markdown("---")

    p_curr_name = player_name.strip() if player_name.strip() else "영입 후보 A (1번 탭)"
    p_curr_age = int(player_age)
    p_curr_pos = main_position.split(" (")[0]
    p_curr_fee = float(calc_actual_fee) if calc_actual_fee > 0 else 5000.0
    p_curr_score = float(final_deal_score) if final_deal_score > 0 else 7.50
    p_curr_mins_p90 = (st.session_state["f_mins"] / 90.0) if st.session_state["f_mins"] > 0 else 1.0
    p_curr_p90 = (st.session_state["f_xg"] + st.session_state["f_xa"]) / p_curr_mins_p90
    p_curr_tkl_p90 = st.session_state.get("f_tackles", 24) / p_curr_mins_p90
    p_curr_duels = (st.session_state.get("f_duels_pct", 62.4) + st.session_state.get("f_aerial_pct", 65.8)) / 2.0
    p_curr_pass = st.session_state.get("f_pass_pct", 88.2)
    p_curr_gk_prev = st.session_state.get("f_gk_prevented", 2.45)
    p_curr_gk_cs = st.session_state.get("f_gk_cs", 10)
    p_curr_rating = float(st.session_state["f_rating"])

    a_axis_label, a_pos_metric_idx, a_stat_summary = calc_pos_custom_metric(
        main_position, p_curr_p90, p_curr_duels, p_curr_tkl_p90, p_curr_pass, p_curr_gk_prev, p_curr_gk_cs
    )

    if "후보 A vs 후보 B" in bench_mode:
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown(f"##### 🔵 **후보 A: {p_curr_name}** *(1번·2번 탭 자동 연동)*")
            st.write(f"- **나이 / 포지션**: 만 `{p_curr_age}세` / `{p_curr_pos}` | **리그**: `{selling_league.split(' (')[0]}`")
            st.write(f"- **산출 적정가**: `€{fair_value:,.1f}만` vs **요구액**: `€{p_curr_fee:,.0f}만` (`{overpay_pct:+.1f}%`)")
            st.write(f"- **포지션 핵심 지표 ({a_axis_label})**: `{a_stat_summary}` (지수 `{a_pos_metric_idx}점`)")
            st.write(f"- **최종 거래 평점**: **`★ {p_curr_score:.2f} / 10.00`**")

        with col_b:
            st.markdown("##### 🟠 **후보 B: 비교 대상 타겟 스펙 입력**")
            b_c1, b_c2, b_c3 = st.columns([2, 1, 1])
            with b_c1: b_name = st.text_input("후보 B 이름", value="영입 후보 B", key="sim_b_name")
            with b_c2: b_age = st.number_input("후보 B 나이(만)", 15, 45, value=24, key="sim_b_age")
            with b_c3: b_pos_full = st.selectbox("후보 B 포지션", list(POSITION_WEIGHTS.keys()), index=list(POSITION_WEIGHTS.keys()).index(main_position), key="sim_b_pos")

            b_c4, b_c5, b_c6, b_c7 = st.columns(4)
            with b_c4: b_from_l = st.selectbox("후보 B 리그", list(LEAGUE_WEIGHTS.keys()), index=0, key="sim_b_league")
            with b_c5: b_contract = st.selectbox("후보 B 계약", list(CONTRACT_WEIGHTS.keys()), index=2, key="sim_b_contract")
            with b_c6: b_tm = st.number_input("후보 B TM가치(만€)", 0, 30000, value=4500, step=100, key="sim_b_tm")
            with b_c7: b_fee = st.number_input("후보 B 요구액(만€)", 0, 30000, value=5500, step=100, key="sim_b_fee")

            b_is_gk = "GK" in b_pos_full
            b_is_def_mid = any(k in b_pos_full for k in ["CB", "RB/LB", "CM/CDM"])

            if b_is_gk:
                b_c8, b_c9, b_c10 = st.columns(3)
                with b_c8: b_rating = st.number_input("후보 B FotMob 평점", 5.0, 10.0, value=7.15, step=0.01, key="sim_b_rating_gk")
                with b_c9: b_gk_prev = st.number_input("후보 B 득점 차단", -15.0, 25.0, value=2.0, step=0.1, key="sim_b_gk_prev")
                with b_c10: b_gk_cs = st.number_input("후보 B 클린시트", 0, 35, value=10, step=1, key="sim_b_gk_cs")
                b_p90, b_duels, b_tkl_p90, b_pass = 0.0, 60.0, 0.0, 80.0
            elif b_is_def_mid:
                b_c8, b_c9, b_c10, b_c11 = st.columns(4)
                with b_c8: b_rating = st.number_input("후보 B FotMob 평점", 5.0, 10.0, value=7.20, step=0.01, key="sim_b_rating_dm")
                with b_c9: b_duels = st.number_input("후보 B 평균 경합승률(%)", 30.0, 90.0, value=63.0, step=0.5, key="sim_b_duels")
                with b_c10: b_tkl_p90 = st.number_input("후보 B 90분당 태클", 0.0, 6.0, value=1.80, step=0.1, key="sim_b_tkl")
                with b_c11: b_pass = st.number_input("후보 B 패스 성공률(%)", 50.0, 98.0, value=87.5, step=0.5, key="sim_b_pass")
                b_p90, b_gk_prev, b_gk_cs = 0.20, 0.0, 0
            else:
                b_c8, b_c9 = st.columns(2)
                with b_c8: b_rating = st.number_input("후보 B 직전 FotMob 평점", 5.0, 10.0, value=7.25, step=0.01, key="sim_b_rating")
                with b_c9: b_p90 = st.number_input("후보 B 90분당 xG+xA", 0.0, 2.5, value=0.55, step=0.05, key="sim_b_p90")
                b_duels, b_tkl_p90, b_pass, b_gk_prev, b_gk_cs = 55.0, 0.8, 82.0, 0.0, 0

        b_lw = LEAGUE_WEIGHTS[b_from_l]
        b_aw = get_positional_age_weight(b_age, b_pos_full)
        b_cw = CONTRACT_WEIGHTS[b_contract]
        b_pw = POSITION_WEIGHTS[b_pos_full]

        if b_is_gk:
            b_opta_w = 1.02 if (b_rating >= 7.35 or b_gk_prev >= 3.5) else (1.01 if (b_rating >= 7.05 or b_gk_prev >= 1.5) else (1.00 if b_rating >= 6.75 else 0.98))
        elif b_is_def_mid:
            b_opta_w = 1.02 if (b_rating >= 7.35 or (b_duels >= 64.0 and b_tkl_p90 >= 1.6)) else (1.01 if (b_rating >= 7.08 or (b_duels >= 58.0 and b_tkl_p90 >= 1.1)) else (1.00 if b_rating >= 6.75 else 0.98))
        else:
            b_opta_w = 1.02 if (b_rating >= 7.45 or b_p90 >= 0.75) else (1.01 if (b_rating >= 7.15 or b_p90 >= 0.50) else (1.00 if b_rating >= 6.80 else 0.98))

        b_fair = b_tm * b_lw * b_aw * club_w * b_cw * b_pw * b_opta_w * season_factor
        b_diff = b_fee - b_fair
        b_overpay = (b_diff / b_fair * 100.0) if b_fair > 0 else 0.0

        b_val_delta = max(-3.5, min(2.5, -(b_overpay / 20.0)))
        b_rat_delta = max(-0.8, min(1.0, (b_rating - 7.00) * 1.5))
        b_age_delta = max(-1.0, min(0.8, (b_aw - 1.00) * 8.0))
        b_score = round(max(1.00, min(10.00, 7.50 + b_val_delta + b_rat_delta + b_age_delta)), 2)
        b_pos_short = b_pos_full.split(" (")[0]

        b_axis_label, b_pos_metric_idx, b_stat_summary = calc_pos_custom_metric(
            b_pos_full, b_p90, b_duels, b_tkl_p90, b_pass, b_gk_prev, b_gk_cs
        )
        radar_4th_label = a_axis_label if a_axis_label == b_axis_label else "포지션 핵심기여도"

        winner_str = f"🏆 최종 추천 타겟: {p_curr_name} (평점 +{p_curr_score - b_score:.2f}점 우위)" if p_curr_score > b_score else (f"🏆 최종 추천 타겟: {b_name} (평점 +{b_score - p_curr_score:.2f}점 우위)" if b_score > p_curr_score else "⚖️ 두 후보의 종합 거래 평점이 동률입니다.")

        ab_cats = ['거래 평점', '가성비 지수', 'FotMob 평점', radar_4th_label, '나이 포텐셜', '리그 경쟁력']
        a_radar = [int(round(p_curr_score * 10)), int(round(max(45, min(98, 78 - overpay_pct * 0.7)))), int(round(max(50, min(98, (p_curr_rating - 6.0) * 22 + 52)))), a_pos_metric_idx, to_public_index(age_w, 0.70, 1.05), to_public_index(league_w, 0.45, 1.00)]
        b_radar = [int(round(b_score * 10)), int(round(max(45, min(98, 78 - b_overpay * 0.7)))), int(round(max(50, min(98, (b_rating - 6.0) * 22 + 52)))), b_pos_metric_idx, to_public_index(b_aw, 0.70, 1.05), to_public_index(b_lw, 0.45, 1.00)]
        svg_ab_radar = build_svg_radar(ab_cats, a_radar, color_a="#38BDF8", values_b=b_radar, color_b="#F97316", size=330)
        donut_a = build_svg_donut_ring(p_curr_score, 10.0, "#38BDF8", "CANDIDATE A", size=100)
        donut_b = build_svg_donut_ring(b_score, 10.0, "#F97316", "CANDIDATE B", size=100)

        tab6_ab_board_html = f"""
        <div style="text-align:center; background:linear-gradient(90deg, rgba(16,185,129,0.12), rgba(16,185,129,0.28), rgba(16,185,129,0.12)); border:1px solid #10B981; border-radius:12px; padding:12px; font-size:18px; font-weight:900; color:#34D399; margin-bottom:16px;">
            {winner_str}
        </div>
        <div style="display:grid; grid-template-columns: 1fr 1.15fr 1fr; gap:14px; align-items:center;">
            <div class="glass-panel" style="border-top:3px solid #38BDF8; padding:18px; text-align:center;">
                <div style="font-size:11px; color:#38BDF8; font-weight:900;">🔵 CANDIDATE A</div>
                <div style="font-size:23px; font-weight:900; color:#FFFFFF; margin-top:4px;">{p_curr_name}</div>
                <div style="font-size:12px; color:#94A3B8; margin-bottom:12px;">만 {p_curr_age}세 · {p_curr_pos}<br>{selling_league.split(' (')[0]}</div>
                <div style="margin-bottom:10px;">{donut_a}</div>
                <div style="background:#090D16; padding:8px; border-radius:8px; font-size:12px; margin-bottom:6px;">산출 적정가: <b style="color:#10B981;">€{fair_value:,.0f}만</b></div>
                <div style="background:#090D16; padding:8px; border-radius:8px; font-size:12px; margin-bottom:6px;">요구 이적료: <b style="color:#38BDF8;">€{p_curr_fee:,.0f}만</b> ({overpay_pct:+.1f}%)</div>
                <div style="background:#090D16; padding:8px; border-radius:8px; font-size:11.5px;">직전 ★{p_curr_rating:.2f} | {a_stat_summary}</div>
            </div>
            <div class="glass-panel" style="padding:12px; text-align:center;">
                <div style="font-size:13.5px; font-weight:900; color:#F8FAFC; margin-bottom:4px;">⚔️ 포지션 맞춤형 6각형 맞대결</div>
                {svg_ab_radar}
            </div>
            <div class="glass-panel" style="border-top:3px solid #F97316; padding:18px; text-align:center;">
                <div style="font-size:11px; color:#F97316; font-weight:900;">🟠 CANDIDATE B</div>
                <div style="font-size:23px; font-weight:900; color:#FFFFFF; margin-top:4px;">{b_name}</div>
                <div style="font-size:12px; color:#94A3B8; margin-bottom:12px;">만 {b_age}세 · {b_pos_short}<br>{b_from_l.split(' (')[0]}</div>
                <div style="margin-bottom:10px;">{donut_b}</div>
                <div style="background:#090D16; padding:8px; border-radius:8px; font-size:12px; margin-bottom:6px;">산출 적정가: <b style="color:#10B981;">€{b_fair:,.0f}만</b></div>
                <div style="background:#090D16; padding:8px; border-radius:8px; font-size:12px; margin-bottom:6px;">요구 이적료: <b style="color:#F97316;">€{b_fee:,.0f}만</b> ({b_overpay:+.1f}%)</div>
                <div style="background:#090D16; padding:8px; border-radius:8px; font-size:11.5px;">직전 ★{b_rating:.2f} | {b_stat_summary}</div>
            </div>
        </div>
        """
        render_copyable_infographic(tab6_ab_board_html, filename=f"matchup_{p_curr_name}_vs_{b_name}", height=590)

    else:
        if history_df.empty or "선수명" not in history_df.columns:
            st.info("💡 아직 구글 시트에 누적된 과거 이적 데이터가 없습니다.")
        else:
            past_player_names = [str(n).strip() for n in history_df["선수명"].dropna().unique() if str(n).strip() not in ["", "nan"]]
            if past_player_names:
                selected_past_player = st.selectbox("과거 비교 대상 선수 선택", past_player_names, index=0, key="bench_player_select")
                pt_dict = history_df[history_df["선수명"] == selected_past_player].iloc[-1].to_dict()

                t_name, t_season = str(pt_dict.get("선수명", "선수")), str(pt_dict.get("이적시즌", "26/27"))
                t_age, t_pos = int(find_val(pt_dict, ["나이"], 25)), str(pt_dict.get("포지션", "CB"))
                t_fee, t_fair = float(find_val(pt_dict, ["실제이적료", "이적료"], 0.0)), float(find_val(pt_dict, ["산출적정가", "적정가"], 0.0))
                t_score = float(find_val(pt_dict, ["이적평점"], 7.50))
                t_xg, t_xa = float(find_val(pt_dict, ["이전_xg", "직전_xg", "xg"], 0.0)), float(find_val(pt_dict, ["이전_xa", "직전_xa", "xa"], 0.0))
                t_mins = float(find_val(pt_dict, ["이전_출전시간", "직전_출전시간", "출전시간"], 2500.0))
                t_rating = float(find_val(pt_dict, ["이전_FotMob평점", "직전_평점", "이전평점", "FotMob평점"], 7.0))
                t_p90_mins = (t_mins / 90.0) if t_mins > 0 else 1.0
                t_p90 = (t_xg + t_xa) / t_p90_mins
                t_tkl_p90 = float(find_val(pt_dict, ["이전_태클성공", "직전_태클", "태클", "tackles"], 24.0)) / t_p90_mins
                t_duels = (float(find_val(pt_dict, ["지상경합승률", "duels_pct"], 60.0)) + float(find_val(pt_dict, ["공중볼승률", "aerial_pct"], 60.0))) / 2.0
                t_pass = float(find_val(pt_dict, ["패스성공률", "pass_pct"], 85.0))
                t_gk_prev = float(find_val(pt_dict, ["gk득점차단", "득점차단", "prevented"], 1.5))
                t_gk_cs = float(find_val(pt_dict, ["gk클린시트", "클린시트", "cs"], 10.0))

                t_axis_label, t_pos_metric_idx, t_stat_summary = calc_pos_custom_metric(
                    t_pos, t_p90, t_duels, t_tkl_p90, t_pass, t_gk_prev, t_gk_cs
                )
                h2h_4th_label = a_axis_label if a_axis_label == t_axis_label else "포지션 핵심기여도"

                h2h_cats = ['거래 평점', '이적료 규모', 'FotMob 평점', h2h_4th_label, '나이 적정성', '적정가 가치']
                p_rad = [int(final_deal_score*10), int(min(98, max(45, p_curr_fee/120))), int(min(98, max(50, (p_curr_rating-6)*22+52))), a_pos_metric_idx, int(max(45, min(98, (35-p_curr_age)*5))), int(min(98, max(45, fair_value/120)))]
                t_rad = [int(t_score*10), int(min(98, max(45, t_fee/120))), int(min(98, max(50, (t_rating-6)*22+52))), t_pos_metric_idx, int(max(45, min(98, (35-t_age)*5))), int(min(98, max(45, t_fair/120)))]
                svg_h2h = build_svg_radar(h2h_cats, p_rad, color_a="#38BDF8", values_b=t_rad, color_b="#F97316", size=325)

                h2h_board_html = f"""
                <div style="display:grid; grid-template-columns: 1fr 1.15fr 1fr; gap:14px; align-items:center;">
                    <div class="glass-panel" style="border-top:3px solid #38BDF8; padding:18px; text-align:center;">
                        <div style="font-size:11px; color:#38BDF8; font-weight:800;">🔵 신규 분석 대상</div>
                        <div style="font-size:22px; font-weight:900; color:#FFFFFF; margin-top:4px;">{p_curr_name}</div>
                        <div style="font-size:12px; color:#94A3B8; margin-bottom:12px;">만 {p_curr_age}세 · {p_curr_pos}</div>
                        <div style="background:#090D16; padding:8px; border-radius:8px; font-size:12px; margin-bottom:6px;">적정가: <b style="color:#10B981;">€{fair_value:,.0f}만</b></div>
                        <div style="background:#090D16; padding:8px; border-radius:8px; font-size:12px; margin-bottom:6px;">실제 거래액: <b style="color:#38BDF8;">€{p_curr_fee:,.0f}만</b></div>
                        <div style="background:#090D16; padding:7px; border-radius:8px; font-size:11.5px; color:#CBD5E1;">★{p_curr_rating:.2f} | {a_stat_summary}</div>
                        <div style="font-size:24px; font-weight:900; color:#38BDF8; margin-top:8px;">★ {final_deal_score:.2f}</div>
                    </div>
                    <div class="glass-panel" style="padding:12px; text-align:center;">
                        <div style="font-size:13px; font-weight:900; color:#F8FAFC; margin-bottom:4px;">⚔️ 과거 사례 1:1 6각형 비교</div>
                        {svg_h2h}
                    </div>
                    <div class="glass-panel" style="border-top:3px solid #F97316; padding:18px; text-align:center;">
                        <div style="font-size:11px; color:#F97316; font-weight:800;">🟠 과거 비교 사례 ({t_season})</div>
                        <div style="font-size:22px; font-weight:900; color:#FFFFFF; margin-top:4px;">{t_name}</div>
                        <div style="font-size:12px; color:#94A3B8; margin-bottom:12px;">만 {t_age}세 · {t_pos}</div>
                        <div style="background:#090D16; padding:8px; border-radius:8px; font-size:12px; margin-bottom:6px;">적정가: <b style="color:#10B981;">€{t_fair:,.0f}만</b></div>
                        <div style="background:#090D16; padding:8px; border-radius:8px; font-size:12px; margin-bottom:6px;">실제 거래액: <b style="color:#F97316;">€{t_fee:,.0f}만</b></div>
                        <div style="background:#090D16; padding:7px; border-radius:8px; font-size:11.5px; color:#CBD5E1;">★{t_rating:.2f} | {t_stat_summary}</div>
                        <div style="font-size:24px; font-weight:900; color:#F97316; margin-top:8px;">★ {t_score:.2f}</div>
                    </div>
                </div>
                """
                render_copyable_infographic(h2h_board_html, filename=f"h2h_{p_curr_name}_vs_{t_name}", height=530)

# ================= TAB 7: 구단/리그별 결산 & 전술판 데이터룸 =================
with tab7:
    st.subheader("🏆 이적시장 구단별 종합 성적표 (전술판 배치도) & 리그 파워 랭킹 & 데이터룸")

    if history_df.empty or "이적시즌" not in history_df.columns:
        st.info("💡 아직 구글 시트에 누적된 이적 데이터가 없습니다.")
    else:
        rank_mode = st.radio("분석 모드 선택", ["🏢 구단별 이적시장 성적표 & 영입 전술판 (Club Report & Tactical Pitch)", "🌍 리그별 / 10대 리그 통합 파워 랭킹 (Power Rankings)", "🛠️ 저장 데이터 조회 및 삭제 관리 (Data Management)"], horizontal=True)
        st.markdown("---")

        if "구단별" in rank_mode:
            c_rc1, c_rc2 = st.columns(2)
            all_seasons = list(history_df["이적시즌"].dropna().unique())
            with c_rc1: sel_season_club = st.selectbox("조회할 이적 시즌", ["전체 시즌"] + all_seasons, index=0, key="report_season_sel")

            club_filtered_df = history_df if sel_season_club == "전체 시즌" else history_df[history_df["이적시즌"] == sel_season_club]
            to_teams = [str(t).strip() for t in club_filtered_df["이적팀명"].dropna().unique() if str(t).strip() not in ["", "nan"]] if "이적팀명" in club_filtered_df.columns else []
            from_teams = [str(t).strip() for t in club_filtered_df["원소속팀명"].dropna().unique() if str(t).strip() not in ["", "nan"]] if "원소속팀명" in club_filtered_df.columns else []
            all_club_names = sorted(list(set(to_teams + from_teams)))

            if all_club_names:
                with c_rc2: sel_team_name = st.selectbox("조회할 구단(팀) 선택", all_club_names, key="report_team_sel")

                team_in_df = club_filtered_df[club_filtered_df["이적팀명"].astype(str).str.strip() == sel_team_name].copy() if "이적팀명" in club_filtered_df.columns else pd.DataFrame()
                team_out_df = club_filtered_df[club_filtered_df["원소속팀명"].astype(str).str.strip() == sel_team_name].copy() if "원소속팀명" in club_filtered_df.columns else pd.DataFrame()

                total_in_spent = team_in_df["실제이적료(만€)"].astype(float).sum() if not team_in_df.empty and "실제이적료(만€)" in team_in_df.columns else 0.0
                total_out_income = team_out_df["실제이적료(만€)"].astype(float).sum() if not team_out_df.empty and "실제이적료(만€)" in team_out_df.columns else 0.0
                net_spend = total_in_spent - total_out_income

                def get_adjusted_deal_score(row, is_buy_side):
                    recorded_score = float(row.get("이적평점", 7.50))
                    orig_trade_type = str(row.get("거래구분", "IN")).strip()
                    if (is_buy_side and orig_trade_type == "OUT") or (not is_buy_side and orig_trade_type == "IN"):
                        return round(max(1.0, min(10.0, 15.00 - recorded_score)), 2)
                    return recorded_score

                if not team_in_df.empty: team_in_df["이적평점"] = team_in_df.apply(lambda r: get_adjusted_deal_score(r, True), axis=1)
                if not team_out_df.empty: team_out_df["이적평점"] = team_out_df.apply(lambda r: get_adjusted_deal_score(r, False), axis=1)

                all_team_trades = pd.concat([team_in_df, team_out_df])
                if not all_team_trades.empty and "이적평점" in all_team_trades.columns:
                    fees = all_team_trades["실제이적료(만€)"].astype(float)
                    scores = all_team_trades["이적평점"].astype(float)
                    weights = fees.apply(lambda x: max(x, 500.0))
                    weighted_avg_score = (scores * weights).sum() / weights.sum() if fees.sum() > 0 else scores.mean()
                else: weighted_avg_score = 7.50

                if weighted_avg_score >= 8.5: club_grade, cg_col = "💎 S등급 (이적시장 대성공)", "#10B981"
                elif weighted_avg_score >= 7.5: club_grade, cg_col = "🌟 A등급 (매우 훌륭한 이적시장)", "#38BDF8"
                elif weighted_avg_score >= 6.8: club_grade, cg_col = "⚖️ B등급 (준수한 실리 운영)", "#FBBF24"
                elif weighted_avg_score >= 6.0: club_grade, cg_col = "⚠️ C등급 (다소 아쉬운 이적시장)", "#F97316"
                else: club_grade, cg_col = "🚨 D등급 (패닉 / 재정 낭비)", "#EF4444"

                donut_club = build_svg_donut_ring(weighted_avg_score, 10.0, cg_col, "CLUB RATING", size=108)
                pitch_html = build_tactical_pitch_html(team_in_df)
                club_rep_logo = resolve_club_logo(sel_team_name)
                club_rep_emblem_html = (
                    f"<div style='width:74px; height:74px; border-radius:16px; background:#0F172A; border:2px solid #38BDF8; display:flex; align-items:center; justify-content:center; padding:7px; margin-right:16px; flex-shrink:0;'>"
                    f"<img src='{club_rep_logo}' style='width:100%; height:100%; object-fit:contain; filter:drop-shadow(0 2px 4px rgba(0,0,0,0.65));'/></div>"
                    if club_rep_logo else
                    f"<div style='width:68px; height:68px; border-radius:16px; background:#0F172A; border:2px solid #38BDF8; display:flex; align-items:center; justify-content:center; font-size:28px; margin-right:16px; flex-shrink:0;'>🛡️</div>"
                )

                in_badges_html = ""
                if not team_in_df.empty:
                    for _, r in team_in_df.iterrows():
                        in_badges_html += (
                            f"<div style='background:#090D16; border-left:3px solid #38BDF8; padding:6px 10px; border-radius:6px; font-size:12px; margin-bottom:5px; display:flex; justify-content:space-between;'>"
                            f"<span><b>{r.get('선수명','')}</b> ({r.get('포지션','')})</span>"
                            f"<span>€{float(r.get('실제이적료(만€)',0)):,.0f}만 · <b style='color:#38BDF8;'>★{float(r.get('이적평점',7.5)):.2f}</b></span></div>"
                        )
                else:
                    in_badges_html = "<div style='color:#64748B; font-size:12px;'>영입 내역 없음</div>"

                out_badges_html = ""
                if not team_out_df.empty:
                    for _, r in team_out_df.iterrows():
                        out_badges_html += (
                            f"<div style='background:#090D16; border-left:3px solid #F43F5E; padding:6px 10px; border-radius:6px; font-size:12px; margin-bottom:5px; display:flex; justify-content:space-between;'>"
                            f"<span><b>{r.get('선수명','')}</b> ({r.get('포지션','')})</span>"
                            f"<span>€{float(r.get('실제이적료(만€)',0)):,.0f}만 · <b style='color:#10B981;'>★{float(r.get('이적평점',7.5)):.2f}</b></span></div>"
                        )
                else:
                    out_badges_html = "<div style='color:#64748B; font-size:12px;'>방출 내역 없음</div>"

                net_type_txt = "순지출" if net_spend >= 0 else "순수익 흑자"

                html_club_board = f"""
                <div class="glass-panel" style="padding:16px 22px; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; margin-bottom:16px;">
                    <div style="display:flex; align-items:center;">
                        {club_rep_emblem_html}
                        <div>
                            <div style="font-size:11px; color:#38BDF8; font-weight:800; letter-spacing:1px;">CLUB TRANSFER WINDOW & TACTICAL PITCH REPORT</div>
                            <div style="font-size:28px; font-weight:900; color:#FFFFFF; margin-top:2px;">{sel_team_name} <span style="font-size:15px; color:#94A3B8;">({sel_season_club})</span></div>
                            <div style="font-size:13px; font-weight:800; color:{cg_col}; margin-top:4px;">종합 판정: {club_grade}</div>
                        </div>
                    </div>
                    <div>{donut_club}</div>
                </div>
                <div style="display:grid; grid-template-columns:repeat(3, 1fr); gap:12px; text-align:center; margin-bottom:16px;">
                    <div class="kpi-card" style="border-top:3px solid #38BDF8;"><div style="font-size:11px; color:#94A3B8;">총 영입 지출액 (IN · {len(team_in_df)}명)</div><div style="font-size:21px; font-weight:900; color:#38BDF8; margin-top:4px;">€{total_in_spent:,.0f}만</div><div style="font-size:11px; color:#64748B;">{format_currency_desc(total_in_spent)}</div></div>
                    <div class="kpi-card" style="border-top:3px solid #10B981;"><div style="font-size:11px; color:#94A3B8;">총 방출 수익 (OUT · {len(team_out_df)}명)</div><div style="font-size:21px; font-weight:900; color:#10B981; margin-top:4px;">€{total_out_income:,.0f}만</div><div style="font-size:11px; color:#64748B;">{format_currency_desc(total_out_income)}</div></div>
                    <div class="kpi-card" style="border-top:3px solid #F59E0B;"><div style="font-size:11px; color:#94A3B8;">순지출 (Net Spend)</div><div style="font-size:21px; font-weight:900; color:#FBBF24; margin-top:4px;">€{net_spend:+,.0f}만</div><div style="font-size:11px; color:#64748B;">{format_currency_desc(abs(net_spend)).split(' | ')[0]} {net_type_txt}</div></div>
                </div>
                <div style="display:grid; grid-template-columns: 1.05fr 0.95fr; gap:14px; align-items:start;">
                    <div class="glass-panel" style="padding:14px;">
                        <div style="font-size:13px; font-weight:900; color:#34D399; margin-bottom:8px;">🏟️ 포지션별 영입생 전술판 배치도 (Tactical Pitch Map)</div>
                        {pitch_html}
                    </div>
                    <div style="display:flex; flex-direction:column; gap:12px;">
                        <div class="glass-panel" style="padding:14px;">
                            <div style="font-size:13px; font-weight:900; color:#38BDF8; margin-bottom:8px;">🔵 주요 영입 (IN) 명단</div>
                            {in_badges_html}
                        </div>
                        <div class="glass-panel" style="padding:14px;">
                            <div style="font-size:13px; font-weight:900; color:#F43F5E; margin-bottom:8px;">🔴 주요 방출 (OUT) 명단</div>
                            {out_badges_html}
                        </div>
                    </div>
                </div>
                """
                render_copyable_infographic(html_club_board, filename=f"club_report_{sel_team_name}", height=820)

        elif "리그별" in rank_mode:
            c_rk1, c_rk2 = st.columns(2)
            all_seasons_rk = list(history_df["이적시즌"].dropna().unique())
            with c_rk1: sel_season_rk = st.selectbox("조회할 이적 시즌", ["전체 시즌"] + all_seasons_rk, index=0, key="rk_season_sel")

            league_filtered_df = history_df if sel_season_rk == "전체 시즌" else history_df[history_df["이적시즌"] == sel_season_rk]
            auto_detected_leagues = [str(l).strip() for l in league_filtered_df["이적팀리그"].dropna().unique() if str(l).strip() not in ["", "nan"]] if "이적팀리그" in league_filtered_df.columns else []

            if auto_detected_leagues:
                league_options = ["🌐 [전체 10개 리그 통합 순위표 (All Leagues)]"] + sorted(auto_detected_leagues)
                with c_rk2: sel_league_name = st.selectbox("조회할 리그 범위 선택", league_options, key="rk_league_sel")

                is_all_leagues = "전체 10개 리그" in sel_league_name
                l_target_df = league_filtered_df if is_all_leagues else league_filtered_df[league_filtered_df["이적팀리그"] == sel_league_name]
                if "이적팀명" in l_target_df.columns:
                    l_target_df = l_target_df[l_target_df["이적팀명"].notnull() & (l_target_df["이적팀명"].astype(str).str.strip() != "")]

                if not l_target_df.empty:
                    unique_teams = sorted(list(l_target_df["이적팀명"].astype(str).str.strip().unique()))
                    team_stat_rows = []

                    def get_adj_score(r, is_buy):
                        rec = float(r.get("이적평점", 7.50))
                        orig = str(r.get("거래구분", "IN")).strip()
                        return round(max(1.0, min(10.0, 15.00 - rec)), 2) if (is_buy and orig == "OUT") or (not is_buy and orig == "IN") else rec

                    for t_name in unique_teams:
                        in_trades = l_target_df[l_target_df["이적팀명"].astype(str).str.strip() == t_name].copy()
                        out_trades = league_filtered_df[league_filtered_df["원소속팀명"].astype(str).str.strip() == t_name].copy() if "원소속팀명" in league_filtered_df.columns else pd.DataFrame()
                        in_spent = in_trades["실제이적료(만€)"].astype(float).sum() if not in_trades.empty and "실제이적료(만€)" in in_trades.columns else 0.0
                        out_income = out_trades["실제이적료(만€)"].astype(float).sum() if not out_trades.empty and "실제이적료(만€)" in out_trades.columns else 0.0
                        if not in_trades.empty: in_trades["이적평점"] = in_trades.apply(lambda r: get_adj_score(r, True), axis=1)
                        if not out_trades.empty: out_trades["이적평점"] = out_trades.apply(lambda r: get_adj_score(r, False), axis=1)

                        all_trades = pd.concat([in_trades, out_trades])
                        if not all_trades.empty and "이적평점" in all_trades.columns:
                            fees = all_trades["실제이적료(만€)"].astype(float)
                            scores = all_trades["이적평점"].astype(float)
                            weights = fees.apply(lambda x: max(x, 500.0))
                            w_score = (scores * weights).sum() / weights.sum() if fees.sum() > 0 else scores.mean()
                        else: w_score = 7.50

                        t_league_label = str(in_trades["이적팀리그"].iloc[0]).strip() if not in_trades.empty and "이적팀리그" in in_trades.columns else ""
                        team_stat_rows.append({"이적팀명": t_name, "소속리그": t_league_label, "가중이적평점": round(w_score, 2), "영입(IN)": len(in_trades), "방출(OUT)": len(out_trades), "총영입액(만€)": int(in_spent), "총방출액(만€)": int(out_income), "순지출(만€)": int(in_spent - out_income)})

                    ranked_df = pd.DataFrame(team_stat_rows).sort_values(by="가중이적평점", ascending=False).reset_index(drop=True)
                    ranked_df.index = ranked_df.index + 1
                    title_prefix = "유럽 전체 10개 리그 통합" if is_all_leagues else sel_league_name
                    best_deal_row = l_target_df.sort_values(by="이적평점", ascending=False).iloc[0]
                    worst_deal_row = l_target_df.sort_values(by="이적평점", ascending=True).iloc[0]

                    rk_rows_html = ""
                    for rk_i, (_, rk_r) in enumerate(ranked_df.head(10).iterrows(), start=1):
                        w_bar = int(min(100, max(20, rk_r["가중이적평점"] * 10)))
                        t_nm = rk_r["이적팀명"]
                        l_nm = rk_r["소속리그"]
                        in_c = rk_r["영입(IN)"]
                        out_c = rk_r["방출(OUT)"]
                        net_v = rk_r["순지출(만€)"]
                        w_sc = rk_r["가중이적평점"]
                        rk_logo = resolve_club_logo(t_nm)
                        rk_logo_img = f"<img src='{rk_logo}' style='width:20px; height:20px; object-fit:contain; vertical-align:middle; margin-right:6px; filter:drop-shadow(0 1px 2px rgba(0,0,0,0.6));'/>" if rk_logo else ""
                        rk_rows_html += (
                            f"<div style='background:#090D16; border:1px solid #1E293B; padding:9px 14px; border-radius:10px; margin-bottom:7px;'>"
                            f"<div style='display:flex; justify-content:space-between; align-items:center; font-size:13px; margin-bottom:4px;'>"
                            f"<span><b style='color:#38BDF8;'>{rk_i:02d}위.</b> {rk_logo_img}<b style='color:#FFFFFF;'>{t_nm}</b> <span style='font-size:11px; color:#94A3B8;'>({l_nm})</span></span>"
                            f"<span>IN {in_c} · OUT {out_c} &nbsp;|&nbsp; 순지출 €{net_v:+,.0f}만 &nbsp;|&nbsp; <b style='color:#10B981;'>★ {w_sc:.2f}</b></span></div>"
                            f"<div style='background:#1E293B; height:5px; border-radius:3px; overflow:hidden;'><div style='width:{w_bar}%; background:linear-gradient(90deg, #0284C7, #10B981); height:100%;'></div></div></div>"
                        )

                    rk_board_html = f"""
                    <div class="glass-panel" style="padding:14px 20px; display:flex; justify-content:space-between; align-items:center; margin-bottom:14px;">
                        <div style="font-size:19px; font-weight:900; color:#FFFFFF;">🏆 {title_prefix} 이적시장 파워 랭킹 ({sel_season_rk})</div>
                        <div style="font-size:12px; color:#38BDF8; font-weight:700;">이적료 가중 평균 평점 기준</div>
                    </div>
                    <div style="margin-bottom:14px;">{rk_rows_html}</div>
                    <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px;">
                        <div style="background:rgba(6,78,59,0.5); border:1px solid #10B981; border-radius:10px; padding:10px 14px; font-size:12px;">💎 <b>최고의 영입 (Best Deal):</b> {best_deal_row.get('선수명','-')} ({best_deal_row.get('이적팀명','-')}) · ★ {float(best_deal_row.get('이적평점',0)):.2f}</div>
                        <div style="background:rgba(69,10,10,0.5); border:1px solid #EF4444; border-radius:10px; padding:10px 14px; font-size:12px;">⚠️ <b>아쉬운 영입 (Worst Deal):</b> {worst_deal_row.get('선수명','-')} ({worst_deal_row.get('이적팀명','-')}) · ★ {float(worst_deal_row.get('이적평점',0)):.2f}</div>
                    </div>
                    """
                    render_copyable_infographic(rk_board_html, filename=f"power_ranking_{title_prefix}", height=680)

                    st.dataframe(ranked_df, use_container_width=True)

                    if len(ranked_df) >= 2:
                        st.markdown("---")
                        st.markdown("##### 📈 **구단별 이적시장 효율성 매트릭스 (순지출 vs 가중 평점 4분면)**")
                        scatter_fig = go.Figure()
                        scatter_fig.add_trace(go.Scatter(
                            x=ranked_df["순지출(만€)"],
                            y=ranked_df["가중이적평점"],
                            mode="markers+text",
                            text=ranked_df["이적팀명"],
                            textposition="top center",
                            textfont=dict(color="#F8FAFC", size=12),
                            marker=dict(
                                size=np.clip(ranked_df["총영입액(만€)"] / 1500 + 12, 12, 34),
                                color=ranked_df["가중이적평점"],
                                colorscale="RdYlGn",
                                showscale=True,
                                line=dict(color="#FFFFFF", width=1.5),
                                colorbar=dict(title="가중평점")
                            ),
                            hovertemplate="<b>%{text}</b><br>순지출: €%{x:,.0f}만<br>가중평점: ★%{y:.2f}<extra></extra>"
                        ))
                        scatter_fig.add_hline(y=7.50, line_dash="dash", line_color="#94A3B8", annotation_text="평점 기준선 (★7.50)", annotation_font_color="#38BDF8")
                        scatter_fig.add_vline(x=0, line_dash="dash", line_color="#94A3B8", annotation_text="손익분기 (Net Spend €0)", annotation_font_color="#10B981")
                        scatter_fig.update_layout(
                            title=dict(text=f"<b>🌍 {title_prefix} 구단별 순지출 vs 이적 평점 매트릭스 ({sel_season_rk})</b>", font=dict(size=17, color="#F8FAFC"), x=0.02),
                            paper_bgcolor="#0B0F19", plot_bgcolor="#0B0F19", font=dict(color="#F8FAFC"),
                            xaxis=dict(title="순지출 (Net Spend, 만 €) [음수(-) = 판매 흑자 / 양수(+) = 영입 지출]", gridcolor="#1E293B"),
                            yaxis=dict(title="가중 이적 평점 (★ 1~10)", gridcolor="#1E293B"),
                            height=460,
                            margin=dict(l=40, r=40, t=70, b=40)
                        )
                        st.plotly_chart(scatter_fig, use_container_width=True)

        else:
            del_c1, del_c2 = st.columns(2)
            del_seasons = list(history_df["이적시즌"].dropna().unique())
            with del_c1: sel_del_season = st.selectbox("삭제 대상 이적 시즌 선택", del_seasons, key="del_season_sel")
            del_season_df = history_df[history_df["이적시즌"] == sel_del_season]
            del_players = list(del_season_df["선수명"].dropna().unique()) if "선수명" in del_season_df.columns else []
            with del_c2: sel_del_player = st.selectbox("삭제할 선수 선택", del_players, key="del_player_sel") if del_players else None

            if sel_del_player:
                if st.button(f"🗑️ '{sel_del_player}' 데이터 구글 시트에서 영구 삭제하기", type="primary", use_container_width=True, key="del_exec_btn"):
                    res = requests.post(GOOGLE_SHEET_WEBAPP_URL, data=json.dumps({"action": "delete_row", "season": sel_del_season, "name": sel_del_player}), headers={"Content-Type": "text/plain;charset=utf-8"}, timeout=30, allow_redirects=True)
                    if res.json().get("status") == "success":
                        st.success("✅ 삭제되었습니다!")
                        st.cache_data.clear()
                        st.rerun()

            st.markdown("---")
            csv_backup = history_df.to_csv(index=False).encode("utf-8-sig")
            st.download_button("📥 전체 DB 엑셀(CSV) 백업 다운로드", data=csv_backup, file_name=f"transfer_scouting_db_{datetime.now().strftime('%Y%m%d_%H%M')}.csv", mime="text/csv", use_container_width=True)
            st.dataframe(history_df, use_container_width=True) 
