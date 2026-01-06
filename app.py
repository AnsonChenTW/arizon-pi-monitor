import streamlit as st
import yfinance as yf
import requests
import pandas as pd
from datetime import datetime, timedelta

# ==========================================
# 1. 頁面設定 (必須放在第一行)
# ==========================================
st.set_page_config(
    page_title="永道 x PI 戰情室 (FinMind版)",
    page_icon="🦅",
    layout="centered"
)

# ==========================================
# 2. 核心數據函數
# ==========================================

def get_impinj_data():
    """抓取美股 PI 股價 (yfinance)"""
    try:
        ticker = yf.Ticker("PI")
        # 抓取 5 天數據以防假日無市
        hist = ticker.history(period="5d")
        
        if hist.empty:
            return None
        
        # 取得最新收盤價與前一日收盤價
        curr_price = hist['Close'].iloc[-1]
        prev_price = hist['Close'].iloc[-2]
        
        change = curr_price - prev_price
        pct = (change / prev_price) * 100
        
        return curr_price, change, pct
    except Exception as e:
        st.error(f"美股數據錯誤: {e}")
        return None

def get_arizon_revenue_finmind():
    """
    抓取台股 6863 營收 (FinMind API)
    優點: 開源數據庫，較不容易被雲端 IP 封鎖
    """
    try:
        url = "https://api.finmindtrade.com/api/v4/data"
        
        # 設定抓取範圍：過去 3 個月 (確保能算 MoM)
        start_date = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
        
        parameter = {
            "dataset": "TaiwanStockMonthRevenue",
            "data_id": "6863",
            "start_date": start_date,
            "token": "" # FinMind 免費版不需 token
        }
        
        # 發送請求
        r = requests.get(url, params=parameter, timeout=10)
        data = r.json()
        
        if data['msg'] == 'success' and data['data']:
            df = pd.DataFrame(data['data'])
            
            # 確保按照日期排序
            df = df.sort_values('date')
            
            # 取得最新一個月數據
            latest = df.iloc[-1]
            prev = df.iloc[-2] if len(df) > 1 else None
            
            # 1. 處理月份 (格式 2024-11-01 -> 2024-11)
            date_str = latest['date'][:7]
            
            # 2. 處理營收 (FinMind 單位是元，轉成億)
            revenue_raw = latest['revenue']
            revenue_亿 = float(revenue_raw) / 100000000
            
            # 3. 自行計算月增率 (MoM) - 因為免費版 API有時不給 YoY/MoM
            mom_str = "N/A"
            if prev is not None:
                rev_prev = float(prev['revenue'])
                if rev_prev > 0:
                    mom_val = ((revenue_raw - rev_prev) / rev_prev) * 100
                    mom_str = f"{mom_val:.2f}%"
            
            # 4. 回傳數據
            return {
                "date": date_str,
                "revenue": revenue_亿,
                "mom": mom_str
            }
            
        return None
    except Exception as e:
        print(f"FinMind Error: {e}") # 僅在後台印出錯誤
        return None

# ==========================================
# 3. UI 介面顯示邏輯
# ==========================================

st.title("🦅 永道 (6863) x PI 監控站")
st.caption("數據來源: Yahoo Finance (美股) + FinMind (台股)")

# 更新時間與按鈕
col_top1, col_top2 = st.columns([3, 1])
with col_top1:
    st.write(f"*最後更新 (台灣時間): {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
with col_top2:
    if st.button("🔄 重新整理"):
        st.rerun()

st.divider()

# --- 區塊 A: 美股 PI ---
st.subheader("🇺🇸 Impinj (PI) 美股現況")
pi_result = get_impinj_data()

if pi_result:
    price, change, pct = pi_result
    
    # 顯示大字指標
    col1, col2 = st.columns(2)
    with col1:
        st.metric(
            label="現價 (USD)", 
            value=f"${price:.2f}", 
            delta=f"{change:.2f} ({pct:.2f}%)"
        )
    with col2:
        # 簡單技術評語
        if price < 170:
            st.error("⚠️ 跌破 $170 警戒線")
            st.caption("支撐轉弱，留意永道營收是否不如預期。")
        elif price > 180:
            st.success("🔥 站上 $180 強勢區")
            st.caption("多頭強勢，若永道營收好將噴出。")
        else:
            st.info("⚖️ $170-$180 區間盤整")
            st.caption("市場觀望中，等待 1/10 營收開牌。")
else:
    st.warning("❌ 無法連線至美股伺服器")

st.divider()

# --- 區塊 B: 台股 永道-KY ---
st.subheader("🇹🇼 永道-KY (6863) 營收")

# 呼叫 FinMind 數據
az_data = get_arizon_revenue_finmind()

if az_data:
    rev = az_data['revenue']
    date_str = az_data['date']
    mom = az_data['mom']
    
    # 判斷是否為 12 月新數據
    is_new = "12" in date_str or "01" in date_str
    
    # 顯示數據
    c1, c2, c3 = st.columns(3)
    c1.metric("月份", date_str, "🆕 Latest" if is_new else "⏳ 舊數據")
    c2.metric("單月營收", f"{rev:.2f} 億")
    c3.metric("月增率 (MoM)", mom)
    
    st.markdown("---")
    
    # 策略訊號判讀
    st.markdown("### 🤖 1/10 決策建議")
    
    if rev >= 3.5:
        st.success("🟢 **[強力買進] 訊號**\n\n營收 > 3.5億。PI 財報將優於預期，建議 **市價進場 PI**。")
    elif rev >= 3.3:
        st.info("🟡 **[偏多操作] 訊號**\n\n營收 > 3.3億。復甦確認，PI 回檔至 $175 附近可 **分批佈局**。")
    elif rev <= 3.0:
        st.error("🔴 **[賣出/觀望] 訊號**\n\n營收 < 3.0億。基本面未跟上股價，PI 恐補跌，建議 **空手**。")
    else:
        st.warning("⚪ **[中性觀望] 訊號**\n\n營收在 3.0~3.3億 之間。方向不明，建議等待 PI 突破或回測再動作。")
        
    if not is_new:
        st.warning(f"⚠️ **注意：目前 FinMind 資料庫最新的數據仍是 {date_str} (尚未更新到 12月)。**")
        st.markdown("""
        **若 1/10 當天此處未更新，請直接點擊下方官方連結確認：**
        
        👉 [證交所官方營收查詢 (絕對準確)](https://mops.twse.com.tw/mops/web/t05st10_ifrs)
        *(輸入代號 6863 查詢)*
        """)

else:
    st.error("❌ 永道數據抓取失敗")
    st.markdown("FinMind 資料庫暫時無法連線，或是 IP 仍被限制。")
    st.markdown("### 🚑 備用方案 (手動查詢)")
    st.markdown("[👉 點此前往 Yahoo 股市營收頁](https://tw.stock.yahoo.com/quote/6863/revenue)")
    st.markdown("[👉 點此前往 證交所官方查詢](https://mops.twse.com.tw/mops/web/t05st10_ifrs)")
