import streamlit as st
import yfinance as yf
import pandas as pd
import pyupbit
from datetime import datetime

# 1. 페이지 설정 (모바일 대응을 위해 Wide 모드 해제 고려 가능하나, 여기선 가독성 위주 설정)
st.set_page_config(page_title="JD부자연구소 모바일", layout="centered")

# 2. 모바일용 커스텀 CSS (카드형 디자인 및 큰 폰트)
st.markdown("""
    <style>
    [data-testid="stMetricValue"] { font-size: 1.8rem !important; font-weight: bold; }
    .status-card {
        padding: 20px;
        border-radius: 15px;
        margin-bottom: 10px;
        text-align: center;
        color: white;
    }
    .safe { background-color: #28a745; }
    .warning { background-color: #ffc107; color: black; }
    .danger { background-color: #dc3545; }
    .info-box { background-color: #f1f3f5; padding: 15px; border-radius: 10px; border-left: 5px solid #339af0; margin: 10px 0; }
    </style>
    """, unsafe_allow_html=True)

def get_data(ticker, is_crypto=False):
    try:
        if is_crypto:
            df = pyupbit.get_ohlcv(ticker, interval="day", count=200)
            curr = df['close'].iloc[-1]
            high = df['high'].max()
        else:
            t = yf.Ticker(ticker)
            df = t.history(period="1y")
            curr = df['Close'].iloc[-1]
            high = df['High'].max()
        return curr, high, (curr - high) / high * 100
    except:
        return 0, 0, 0

# 나스닥 -3% 체크 로직 (최근 31일)
@st.cache_data(ttl=3600)
def check_nasdaq_signal():
    ndq = yf.download("^IXIC", period="2mo", progress=False)
    ndq['Change'] = ndq['Close'].pct_change() * 100
    m3_days = ndq[ndq['Change'] <= -3.0]
    if m3_days.empty:
        return "SAFE", None
    last_date = m3_days.index[-1]
    days_passed = (datetime.now() - last_date).days
    return ("WAIT", last_date) if days_passed < 31 else ("SAFE", last_date)

# --- 메인 화면 ---
st.title("🚀 JD 부자연구소")
signal, last_date = check_nasdaq_signal()

# 3. 신호등 시스템 (가장 먼저 보임)
if signal == "SAFE":
    st.markdown('<div class="status-card safe">✅ 매수 가능 (한 달간 -3% 없음)</div>', unsafe_allow_html=True)
else:
    st.markdown(f'<div class="status-card danger">🚨 대기 모드 (-3% 발생: {last_date.date()})</div>', unsafe_allow_html=True)

tab1, tab2 = st.tabs(["🇺🇸 미국 주식", "₿ 비트코인"])

# --- 주식 탭 ---
with tab1:
    ticker = st.text_input("종목 입력", value="AAPL").upper()
    curr, high, dd = get_data(ticker)
    
    # 모바일에서는 세로로 배치하는 것이 가독성이 좋음
    st.metric("현재가", f"${curr:.2f}")
    st.metric("전고점 대비 하락률", f"{dd:.2f}%", delta=f"{dd:.2f}%")
    
    st.markdown('<div class="info-box">', unsafe_allow_html=True)
    st.write("### 📝 대응 매뉴얼")
    if dd <= -10:
        st.error("말뚝박기 진행 중: 현금 비중 대폭 확대")
    elif dd <= -2.5:
        st.warning(f"리밸런싱 구간: 현재 하락률 {dd:.1f}%에 맞춰 비중 조절")
    else:
        st.success("보유 구간: 시총 1등 유지 시 홀딩")
    st.markdown('</div>', unsafe_allow_html=True)

# --- 코인 탭 ---
with tab2:
    coin = st.selectbox("코인 선택", ["KRW-BTC", "KRW-ETH", "KRW-SOL"])
    curr_c, high_c, dd_c = get_data(coin, is_crypto=True)
    
    st.metric("현재 시세", f"{int(curr_c):,} 원")
    st.metric("전고점 대비", f"{dd_c:.2f}%", delta=f"{dd_c:.2f}%")

    st.info("💡 코인은 변동성이 크므로 전체 자산의 10% 이내 운용을 권장합니다.")

# 하단 정보
st.caption(f"최근 업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
