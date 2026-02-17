import streamlit as st
import yfinance as yf
import pandas as pd
import pyupbit
import requests
from datetime import datetime

# 1. 페이지 설정
st.set_page_config(page_title="원칙투자 가이드", layout="centered")

# 2. 커스텀 CSS
st.markdown("""
    <style>
    .fng-container { padding: 20px; border-radius: 15px; text-align: center; color: white; margin-bottom: 20px; }
    .extreme-fear { background-color: #dc3545; }
    .fear { background-color: #ffc107; color: black; }
    .neutral { background-color: #6c757d; }
    .greed { background-color: #28a745; }
    .extreme-greed { background-color: #007bff; }
    .guide-table { font-size: 0.9rem; width: 100%; border-collapse: collapse; }
    </style>
    """, unsafe_allow_html=True)

# 3. 데이터 로드 함수
@st.cache_data(ttl=3600)
def get_fng_index():
    """CNN Fear & Greed Index 스크래핑 (간이 구현)"""
    try:
        # 공식 API가 없으므로 유료/공공 데이터 대용으로 랜덤 샘플 혹은 간이 파싱 로직 사용
        # 실사용 시에는 정식 API 라이브러리(fear-and-greed) 권장
        url = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(url, headers=headers).json()
        val = int(r['market_indicator']['current_value'])
        desc = r['market_indicator']['rating']
        return val, desc
    except:
        return 50, "Neutral (Data Error)"

def get_stock_data(ticker):
    t = yf.Ticker(ticker)
    df = t.history(period="1y")
    curr = df['Close'].iloc[-1]
    high = df['High'].max()
    return curr, high, (curr - high) / high * 100

# --- 메인 대시보드 ---
st.title("🛡️ 원칙투자 가이드")
st.caption("Principle Invest: 정해진 매뉴얼에 의한 기계적 투자")

# [A] 공포탐욕지수 섹션
fng_val, fng_desc = get_fng_index()
fng_class = fng_desc.lower().replace(" ", "-")
st.markdown(f'### 📊 시장 심리 지수')
st.markdown(f'<div class="fng-container {fng_class}"><b>CNN Fear & Greed: {fng_val} ({fng_desc})</b></div>', unsafe_allow_html=True)

tab1, tab2 = st.tabs(["🇺🇸 미국 주식 ETF", "₿ 비트코인"])

# --- TAB 1: 미국 주식 (ETF 선택 가능) ---
with tab1:
    selected_ticker = st.selectbox("종목 선택", ["SMH", "FTEC", "QQQ", "SPY", "AAPL", "MSFT"])
    curr, high, dd = get_stock_data(selected_ticker)
    
    col1, col2 = st.columns(2)
    col1.metric(f"{selected_ticker} 현재가", f"${curr:.2f}")
    col2.metric("전고점 대비 하락률", f"{dd:.2f}%", delta=f"{dd:.2f}%")

    # [B] 10% 매도 구간표 (조던 리밸런싱 매뉴얼 기반)
    st.write("### 📝 리밸런싱 매도 구간표")
    guide_data = {
        "하락률 (전고점 대비)": ["-2.5%", "-5.0%", "-7.5%", "-10.0% (말뚝박기)"],
        "주식 보유 비중": ["90%", "80%", "70%", "현금 100% (매뉴얼 기준)"],
        "대응 액션": ["10% 매도", "추가 10% 매도", "추가 10% 매도", "전량 매도 후 관망"]
    }
    st.table(pd.DataFrame(guide_data))

    # 현재 상태 진단
    st.write("### 🚩 현재 대응 전략")
    if dd <= -10:
        st.error(f"**위험**: 전량 매도 후 -3% 룰(V자 반등) 확인 대기 구간입니다.")
    elif dd <= -2.5:
        st.warning(f"**주의**: 리밸런싱 매도 구간입니다. 위 표의 비중을 확인하세요.")
    else:
        st.success("**안전**: 정상 보유 구간입니다. 세계 1등주/우량 ETF를 유지하세요.")

# --- TAB 2: 비트코인 ---
with tab2:
    curr_c, high_c, dd_c = 0, 0, 0
    try:
        df_c = pyupbit.get_ohlcv("KRW-BTC", interval="day", count=100)
        curr_c = df_c['close'].iloc[-1]
        high_c = df_c['high'].max()
        dd_c = (curr_c - high_c) / high_c * 100
    except: pass

    st.metric("BTC 현재가", f"{int(curr_c):,} 원")
    st.metric("전고점 대비", f"{dd_c:.2f}%", delta=f"{dd_c:.2f}%")
    st.info("코인은 변동성이 크므로 주식 매뉴얼보다 더 엄격한 현금 비중 관리가 필요합니다.")

# 하단 나스닥 -3% 체크 (V자 반등 조건)
st.divider()
ndq = yf.download("^IXIC", period="1mo", progress=False)
m3_exists = not ndq[ndq['Close'].pct_change() <= -0.03].empty
if m3_exists:
    st.markdown("⚠️ **V자 반등 조건 미충족**: 최근 31일 내 나스닥 -3%가 발생했습니다. 보수적 접근 권장.")
else:
    st.markdown("✅ **V자 반등 조건 충족**: 최근 한 달간 나스닥 -3%가 없었습니다. 재진입 가능 구간.")
