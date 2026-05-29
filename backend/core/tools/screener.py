import yfinance as yf
import pandas as pd
import requests
from bs4 import BeautifulSoup
from core.config import DATA_DIR

# Rich and high-quality cache of top constituents for major sector ETFs
# Used as a robust fallback if dynamic HTML parsing is blocked
ETF_CONSTITUENTS_CACHE = {
    # US Sector ETFs
    "XLK": [
        "MSFT", "AAPL", "NVDA", "AVGO", "ORCL", "CRM", "AMD", "QCOM", "NOW", "ADBE", 
        "INTU", "TXN", "AMAT", "MU", "IBM", "LRCX", "PANW", "ADI", "KLAC", "SNPS"
    ],
    "XLF": [
        "JPM", "BRK-B", "V", "MA", "BAC", "WFC", "MS", "GS", "SCHW", "C", 
        "BLK", "AXP", "BX", "CB", "SPGI", "MMC", "PGR", "MET", "AON", "USB"
    ],
    "XLE": [
        "XOM", "CVX", "COP", "SLB", "EOG", "MPC", "PSX", "VLO", "OXY", "WMB", 
        "HAL", "BKR", "HES", "KMI", "ONEOK", "DVN", "CTRA", "APA", "FANG", "MRO"
    ],
    "XLV": [
        "LLY", "UNH", "JNJ", "ABBV", "MRK", "AMGN", "HCA", "PFE", "ISRG", "SYK", 
        "BSX", "MDT", "ABT", "GILD", "VRTX", "BMY", "REGN", "CI", "CVS", "ELV"
    ],
    "XLY": [
        "AMZN", "TSLA", "HD", "MCD", "NKE", "LOW", "TJX", "SBUX", "BKNG", "CMG", 
        "MAR", "F", "GM", "ORLY", "AZO", "HLT", "LVS", "YUM", "DHI", "PHM"
    ],
    "XLI": [
        "GE", "CAT", "RTX", "HON", "UNP", "LMT", "ETN", "DE", "WM", "BA", 
        "CSX", "NSC", "ITW", "GD", "NOC", "EMR", "PH", "FDX", "UPS", "CPRT"
    ],
    "XLP": [
        "PG", "COST", "KO", "PEP", "PM", "MO", "WMT", "EL", "MDLZ", "CL", 
        "SYY", "KDP", "KR", "K", "GIS", "STZ", "HSY", "CHD", "ADM", "TSN"
    ],
    "XLB": [
        "LIN", "SHW", "APD", "FCX", "ECL", "NEM", "CTVA", "DOW", "DD", "PPG", 
        "VMC", "MLM", "IFF", "ALB", "CF", "NUE", "MOS", "FMC"
    ],
    "XLU": [
        "NEE", "SO", "DUK", "CEG", "WEC", "D", "AEP", "PEG", "EXC", "PCG", 
        "SRE", "ED", "XEL", "EIX", "FE", "AWK", "ES", "CNP", "ETR", "ATO"
    ],
    # Taiwan Sector Proxies
    "0050.TW": [
        "2330.TW", "2317.TW", "2454.TW", "2382.TW", "2308.TW", "2881.TW", "2882.TW", "2303.TW", 
        "2891.TW", "3711.TW", "2412.TW", "1216.TW", "2886.TW", "5871.TW", "2603.TW", "2884.TW", 
        "2892.TW", "3231.TW", "2357.TW", "2324.TW", "2885.TW", "2880.TW", "2912.TW", "3045.TW"
    ],
    "0052.TW": [
        "2330.TW", "2454.TW", "2317.TW", "2382.TW", "2308.TW", "2303.TW", "3711.TW", "2379.TW", 
        "3231.TW", "2345.TW", "2408.TW", "3034.TW", "2357.TW", "2449.TW", "3044.TW", "2376.TW", 
        "2301.TW", "6239.TW", "3008.TW", "2409.TW", "3481.TW", "8046.TW", "3532.TW", "2439.TW"
    ],
    "0056.TW": [
        "2382.TW", "3231.TW", "2301.TW", "2357.TW", "2603.TW", "3034.TW", "2454.TW", "2324.TW", 
        "3711.TW", "2379.TW", "3044.TW", "2409.TW", "3481.TW", "2891.TW", "2886.TW", "2408.TW", 
        "2303.TW", "2882.TW", "2881.TW", "1101.TW", "2002.TW", "2885.TW", "2892.TW", "2890.TW"
    ],
    # Custom Proxy Stock Sets to mock other region categories dynamically
    "2330.TW": ["2330.TW", "2449.TW", "3711.TW", "2408.TW", "2344.TW", "3231.TW", "2303.TW", "2454.TW", "3034.TW", "3532.TW", "6271.TW", "8046.TW", "3008.TW", "3653.TW"],
    "2881.TW": ["2881.TW", "2882.TW", "2891.TW", "2886.TW", "2884.TW", "2880.TW", "2885.TW", "2892.TW", "2890.TW", "5880.TW", "5876.TW", "2834.TW", "2883.TW", "2887.TW"],
    "1301.TW": ["1301.TW", "1303.TW", "1326.TW", "6505.TW", "2002.TW", "1101.TW", "1402.TW", "2603.TW", "2609.TW", "2615.TW", "1102.TW", "2105.TW", "1304.TW", "1314.TW"]
}

class QuantScreener:
    def __init__(self):
        self.session_history = []

    def fetch_etf_constituents(self, etf_ticker: str) -> list:
        """
        Dynamically fetches constituents of the given ETF from Yahoo Finance.
        Falls back to a high-quality pre-seeded cache if scraping fails or gets blocked.
        """
        etf_ticker = etf_ticker.strip().upper()
        
        try:
            url = f"https://finance.yahoo.com/quote/{etf_ticker}/holdings/"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            resp = requests.get(url, headers=headers, timeout=8)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.content, "html.parser")
                tickers = []
                
                # Scan all links containing "/quote/" which represents tickers
                for a in soup.find_all("a", href=True):
                    href = a["href"]
                    if "/quote/" in href:
                        parts = href.split("/quote/")
                        if len(parts) > 1:
                            # Strip out parameters like ?p=MSFT or sub-paths
                            sym = parts[1].split("?")[0].split("/")[0].strip().upper()
                            # Clean symbols and filter out the parent ETF symbol
                            if sym and sym != etf_ticker and all(c.isalnum() or c in ".-" for c in sym) and len(sym) <= 10:
                                if sym not in tickers:
                                    tickers.append(sym)
                                    
                if len(tickers) >= 5:
                    print(f"[*] [Screener] 動態成功抓取 {etf_ticker} 的 {len(tickers)} 檔成分股代號。")
                    return tickers
        except Exception as e:
            print(f"[!] [Screener] 動態抓取 {etf_ticker} 成分股失敗 ({e})。將切換至靜態高品質快取。")
            
        # Fallback to local cache
        cache_list = ETF_CONSTITUENTS_CACHE.get(etf_ticker, [])
        print(f"[*] [Screener] 載入 {etf_ticker} 成分股快取清單 (共 {len(cache_list)} 檔標的)。")
        return cache_list

    def _get_projected_volume(self, hist: pd.DataFrame, region: str) -> float:
        """
        Dynamically projects intraday volume to full-day volume if the market is open.
        Provides a stable fallback to previous close volume during pre-market or early trading.
        """
        try:
            from datetime import datetime, time
            import pytz
            
            last_row = hist.iloc[-1]
            last_volume = float(last_row["Volume"])
            
            # Retrieve the timestamp of the last data row
            # If yfinance history has a timezone-aware DatetimeIndex, use its timezone
            last_date = hist.index[-1]
            
            # Setup timezone and trading hours
            if region == "US":
                tz = pytz.timezone("America/New_York")
                market_open_time = time(9, 30)
                market_close_time = time(16, 0)
                total_minutes = 390.0
            else:  # Taiwan
                tz = pytz.timezone("Asia/Taipei")
                market_open_time = time(9, 0)
                market_close_time = time(13, 30)
                total_minutes = 270.0
                
            # Get current time in the local timezone of the market
            now = datetime.now(tz)
            
            # Check if the last row's date matches today (meaning it is a live trading day)
            if last_date.strftime("%Y-%m-%d") == now.strftime("%Y-%m-%d"):
                # Market is today. Check if trading hours have started
                market_open = tz.localize(datetime.combine(now.date(), market_open_time))
                market_close = tz.localize(datetime.combine(now.date(), market_close_time))
                
                if now < market_open:
                    # Pre-market: use previous day's completed volume (iloc[-2]) as a stable indicator
                    if len(hist) >= 2:
                        return float(hist["Volume"].iloc[-2])
                    return last_volume
                elif now >= market_close:
                    # Post-market or market closed: use today's actual volume
                    return last_volume
                else:
                    # Market is currently trading: project volume based on elapsed minutes
                    elapsed = (now - market_open).total_seconds() / 60.0
                    
                    # If it's the first 15 minutes of trading, projection can be extremely noisy.
                    # Fallback to previous day's completed volume to maintain stability!
                    if elapsed < 15.0:
                        if len(hist) >= 2:
                            return float(hist["Volume"].iloc[-2])
                        return last_volume
                        
                    projected = last_volume * (total_minutes / elapsed)
                    return float(projected)
        except Exception as e:
            print(f"[!] [Screener] Volume projection error: {e}")
            
        # Standard fallback on any error: return today's volume as-is
        return float(hist["Volume"].iloc[-1])

    def screen_stocks(self, etf_ticker: str, region: str, limit: int = 5) -> list:
        """
        Calculates 5-day return momentum, volume surge factor, and applies liquidity/trend filters
        to dynamically select the top 'limit' candidates from the ETF's constituents.
        """
        tickers = self.fetch_etf_constituents(etf_ticker)
        if not tickers:
            return []
            
        print(f"[*] [Screener] 開始對 {etf_ticker} 的成分股進行量化因子計算與篩選...")
        screened_results = []
        
        # Configure regional liquidity limits
        # US: min market cap $2B, min avg volume 200,000 shares
        # Taiwan: min market cap NT$8B, min avg volume 300,000 shares (300張)
        min_mcap = 2 * 10**9 if region == "US" else 8 * 10**9
        min_vol = 200000 if region == "US" else 300000
        
        for ticker in tickers:
            try:
                t = yf.Ticker(ticker)
                
                # Fetch historical price data (1 month history is perfect to calculate 20-day averages)
                hist = t.history(period="1mo")
                if hist.empty or len(hist) < 20:
                    continue
                
                # Retrieve fast_info indicators (fast & robust)
                fast = t.fast_info
                market_cap = fast.get("marketCap", 0.0)
                # Fallback to calculated market cap if fast_info fails
                if not market_cap:
                    market_cap = hist["Close"].iloc[-1] * fast.get("shares", 0.0)
                    
                # 1. Liquidity filter
                avg_volume = hist["Volume"].iloc[-20:].mean()
                if market_cap < min_mcap or avg_volume < min_vol:
                    # Skip highly illiquid small caps
                    continue
                    
                # 2. Trend filter (Price must be above 20-day MA to avoid catching falling knives)
                close_now = hist["Close"].iloc[-1]
                ma20 = hist["Close"].iloc[-20:].mean()
                if close_now < ma20:
                    # Stock is in a downtrend, skip
                    continue
                    
                # 3. Momentum Factor (5-day return)
                close_5d_ago = hist["Close"].iloc[-6] if len(hist) >= 6 else hist["Close"].iloc[0]
                weekly_return = (close_now - close_5d_ago) / close_5d_ago
                
                # 4. Volume Spike Factor (current volume vs 20-day average) with Dynamic Intraday Projection!
                volume_now = self._get_projected_volume(hist, region)
                volume_spike = volume_now / avg_volume if avg_volume > 0 else 1.0
                
                # Get the company name
                name = ticker
                # Try to retrieve name from yfinance fast info or ticker info
                try:
                    name = t.info.get("longName", ticker)
                except Exception:
                    pass
                
                # 5. Combined Score
                # Return score is weekly return in % (e.g. 8.5% is 8.5)
                return_score = weekly_return * 100
                # Volume spike is capped at 3x for scoring stability
                volume_score = min(volume_spike, 3.0) / 3.0 * 10.0
                
                # Formula: 70% Momentum (Alpha) + 30% Volume Spike (Institutional footprint)
                combined_score = (return_score * 0.7) + (volume_score * 0.3)
                
                screened_results.append({
                    "ticker": ticker,
                    "name": name,
                    "weekly_return": float(weekly_return),
                    "volume_spike": float(volume_spike),
                    "current_price": float(close_now),
                    "market_cap": float(market_cap),
                    "score": float(combined_score)
                })
                
            except Exception as e:
                # Silently catch and proceed for individual stock failures to ensure pipeline robustness
                continue
                
        # Sort by combined score in descending order (highest score first)
        screened_results.sort(key=lambda x: x["score"], reverse=True)
        
        final_picks = screened_results[:limit]
        print(f"[✓] [Screener] {etf_ticker} 動態量化篩選完成！挑選出前 {len(final_picks)} 強勢飆股：")
        for i, pick in enumerate(final_picks, 1):
            print(f"    {i}. {pick['name']} ({pick['ticker']}) - 5日漲幅: {pick['weekly_return']*100:.2f}%, 量能增幅: {pick['volume_spike']:.2f}x, 評分: {pick['score']:.2f}")
            
        self.session_history.append({
            "etf": etf_ticker,
            "region": region,
            "picks": final_picks
        })
        return final_picks

    def generate_report(self, report_date: str) -> tuple:
        """
        Generates a beautiful Markdown and HTML report from the session screening history.
        """
        if not self.session_history:
            return "", ""
            
        from core.config import REPORT_LANGUAGE
        import markdown
        
        is_zh = (REPORT_LANGUAGE == "ZH")
        
        if is_zh:
            title = f"# 📈 量化動態選股掃描決策報告 ({report_date})"
            note_content = "本報告由「量化動態掃描選股引擎」自動生成。系統分析了當週資金流入最強的行業 ETF 成分股，依據 **5日動能因子（70% 權重）** 與 **20日成交量爆發因子（30% 權重）** 進行綜合評分篩選，排除流動性不足與空頭排列個股，精選出最具主力大單進駐與爆發潛力的個股。"
            sec_title = "🎯 各板塊強勢個股動態篩選明細"
        else:
            title = f"# 📈 Quantamental Dynamic Stock Selection Report ({report_date})"
            note_content = "This report is automatically generated by the Quantamental Dynamic Stock Scanner Engine. The system analyzes the constituents of the strongest performing sector ETFs of the week, screening them using a combined quantitative score of **5-day momentum (70% weight)** and **20-day volume spike (30% weight)**, filtering out low-liquidity assets and downtrend stocks, selecting targets with robust institutional buying footprints."
            sec_title = "🎯 Selected Sector Strong Stock Screening Details"
            
        lines = []
        lines.append(title)
        lines.append("\n---")
        lines.append(f"\n> [!NOTE]\n> {note_content}\n")
        lines.append("\n---")
        lines.append(f"\n## {sec_title}\n")
        
        for item in self.session_history:
            etf = item["etf"]
            region = item["region"]
            picks = item["picks"]
            
            if not picks:
                continue
                
            region_lbl = "美股" if region == "US" else "台股"
            if not is_zh:
                region_lbl = "US Market" if region == "US" else "Taiwan Market"
                
            lines.append(f"\n### 🔍 焦點行業板塊 ETF：{etf} ({region_lbl})\n")
            
            # Draw Table
            if is_zh:
                lines.append("| 排名 | 標的代碼 | 企業名稱 | 當前價格 | 5日漲跌幅 | 成交量增幅 | 量化評分 | 市值 |")
                lines.append("| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |")
            else:
                lines.append("| Rank | Ticker | Company Name | Price | 5-Day Return | Vol Spike | Quant Score | Market Cap |")
                lines.append("| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |")
                
            for idx, pick in enumerate(picks, 1):
                ticker = pick["ticker"]
                name = pick["name"]
                price = pick["current_price"]
                ret = pick["weekly_return"] * 100
                spike = pick["volume_spike"]
                score = pick["score"]
                mcap = pick["market_cap"]
                
                # Format Market Cap
                if mcap >= 10**12:
                    mcap_str = f"{mcap / 10**12:.2f}T"
                elif mcap >= 10**9:
                    mcap_str = f"{mcap / 10**9:.2f}B"
                else:
                    mcap_str = f"{mcap / 10**6:.2f}M"
                    
                price_symbol = "$" if region == "US" else "NT$"
                
                lines.append(f"| {idx} | `{ticker}` | {name} | {price_symbol}{price:.2f} | {ret:+.2f}% | {spike:.2f}x | {score:.2f} | {mcap_str} |")
                
            lines.append("\n---")
            
        lines.append("\n## ⚠️ 免責聲明 (Disclaimer)")
        if is_zh:
            lines.append("本報告僅供參考，不構成任何投資建議。投資人應獨立評估市場風險，並承擔交易之最終盈虧。")
        else:
            lines.append("This report is for informational purposes only and does not constitute investment advice. Investors should evaluate market risks independently and bear full responsibility for their trades.")
            
        final_markdown = "\n".join(lines)
        final_html = markdown.markdown(final_markdown, extensions=['fenced_code', 'tables'])
        return final_markdown, final_html
