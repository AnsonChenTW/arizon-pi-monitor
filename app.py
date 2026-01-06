import streamlit as st
import yfinance as yf
import requests
import pandas as pd
from datetime import datetime

# 設定頁面標題與寬度
st.set_page_config(page_title="永道 x PI 戰情室", page_icon="🦅", layout="centered")

# --- 核心函數 ---

def get_headers():
    return {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://tw.stock.yahoo.com/',
    }

def get_impinj_data():
    try:
        ticker = yf.Ticker("PI")
        hist = ticker.history(period="5d")
        if hist.empty: return None
        
        curr = hist['Close'].iloc[-1]
        prev = hist['Close'].iloc[-2]
        change = curr - prev
        pct = (change / prev) * 100
        return curr, change, pct
    except:
        return None

def get_arizon_revenue():
    # 使用 Yahoo API
    url = "https://tw.stock.yahoo.com/_td-stock/api/resource/StockServices.revenues;symbol=6863.TW;period=month"
    try:
        r = requests.get(url, headers=get_headers(), timeout=10)
        data = r.json()
        if 'result' in data and data['result']:
            latest = data['result'][0]
            date_str = latest['date'][:7] # 2024-12
            rev_亿 = float(latest['revenue']) / 100000
            mom = float(latest['monthOverMonth'])
            yoy = float(latest['yearOverYear'])
            return date_str, rev_亿, mom, yoy
    except Exception as e:
        return None

# --- UI 介面 ---

st.title("🦅 永道 (6863) x PI 監控站")
st.caption(f"最後更新: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if st.button("🔄 立即重新掃描", type="primary"):
    st.rerun()

st.divider()

# 1. PI 區塊
st.subheader("🇺🇸 Impinj (PI) 美股現況")
pi_data = get_impinj_data()

if pi_data:
    price, change, pct = pi_data
    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="現價 (USD)", value=f"${price:.2f}", delta=f"{change:.2f} ({pct:.2f}%)")
    with col2:
        if price < 170:
            st.warning("⚠️ 跌破 $170 警戒線")
        elif price > 180:
            st.success("🔥 站上 $180 強勢區")
        else:
            st.info("⚖️ $170-$180 區間盤整")
else:
    st.error("❌ 無法獲取 PI 數據")

st.divider()

# 2. 永道區塊
st.subheader("🇹🇼 永道-KY (6863) 營收")
az_data = get_arizon_revenue()

if az_data:
    date_str, rev, mom, yoy = az_data
    
    # 判斷是否為 12 月
    is_dec = "12" in date_str or "01" in date_str # 寬鬆判斷
    
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("月份", date_str, "🆕" if is_dec else "⏳ 舊數據")
    col_b.metric("單月營收", f"{rev:.2f} 億", f"{mom}% (月增)")
    col_c.metric("年增率", f"{yoy}%", delta_color="off")
    
    st.markdown("### 🤖 1/10 決策訊號")
    if rev >= 3.5:
        st.success("🟢 **強力買進 (Strong Buy)**：營收大爆發，PI 財報將優於預期。")
    elif rev >= 3.3:
        st.info("🟡 **偏多操作 (Buy)**：營收穩健，PI 回檔可接。")
    elif rev <= 3.0:
        st.error("🔴 **觀望/賣出 (Sell)**：營收不如預期，PI 恐補跌。")
    else:
        st.warning("⚪ **中性觀望**：數據平平，等待方向。")
        
    if not is_dec:
        st.caption("⚠️ 注意：目前顯示的仍是 11 月數據，12 月營收尚未公布。")
else:
    st.error("❌ 永道數據抓取失敗 (IP 被擋)")
    st.markdown("[點此手動前往 Yahoo 股市查看](https://tw.stock.yahoo.com/quote/6863/revenue)")
