import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from core.config import REGIONS

# Static mapping of sector ETFs to top representative stocks as a fail-safe / performance optimization
# This ensures robust execution without hitting complex HTML scraping limits for ETF holdings
ETF_TOP_HOLDINGS = {
    # US Sector ETFs
    "XLK": [
        {"ticker": "MSFT", "name": "Microsoft Corp."},
        {"ticker": "AAPL", "name": "Apple Inc."},
        {"ticker": "NVDA", "name": "NVIDIA Corp."},
        {"ticker": "AVGO", "name": "Broadcom Inc."},
        {"ticker": "ORCL", "name": "Oracle Corp."}
    ],
    "XLF": [
        {"ticker": "JPM", "name": "JPMorgan Chase & Co."},
        {"ticker": "BRK-B", "name": "Berkshire Hathaway Inc."},
        {"ticker": "V", "name": "Visa Inc."},
        {"ticker": "MA", "name": "Mastercard Inc."},
        {"ticker": "BAC", "name": "Bank of America Corp."}
    ],
    "XLE": [
        {"ticker": "XOM", "name": "Exxon Mobil Corp."},
        {"ticker": "CVX", "name": "Chevron Corp."},
        {"ticker": "COP", "name": "ConocoPhillips"},
        {"ticker": "SLB", "name": "Schlumberger NV"},
        {"ticker": "EOG", "name": "EOG Resources Inc."}
    ],
    "XLV": [
        {"ticker": "LLY", "name": "Eli Lilly & Co."},
        {"ticker": "UNH", "name": "UnitedHealth Group Inc."},
        {"ticker": "JNJ", "name": "Johnson & Johnson"},
        {"ticker": "ABBV", "name": "AbbVie Inc."},
        {"ticker": "MRK", "name": "Merck & Co. Inc."}
    ],
    "XLY": [
        {"ticker": "AMZN", "name": "Amazon.com Inc."},
        {"ticker": "TSLA", "name": "Tesla Inc."},
        {"ticker": "HD", "name": "Home Depot Inc."},
        {"ticker": "MCD", "name": "McDonald's Corp."},
        {"ticker": "LOW", "name": "Lowe's Companies Inc."}
    ],
    "XLI": [
        {"ticker": "GE", "name": "General Electric Co."},
        {"ticker": "CAT", "name": "Caterpillar Inc."},
        {"ticker": "RTX", "name": "RTX Corp."},
        {"ticker": "HON", "name": "Honeywell International Inc."},
        {"ticker": "UNP", "name": "Union Pacific Corp."}
    ],
    "XLP": [
        {"ticker": "PG", "name": "Procter & Gamble Co."},
        {"ticker": "COST", "name": "Costco Wholesale Corp."},
        {"ticker": "KO", "name": "Coca-Cola Co."},
        {"ticker": "PEP", "name": "PepsiCo Inc."},
        {"ticker": "PM", "name": "Philip Morris International Inc."}
    ],
    "XLB": [
        {"ticker": "LIN", "name": "Linde PLC"},
        {"ticker": "APD", "name": "Air Products and Chemicals Inc."},
        {"ticker": "SHW", "name": "Sherwin-Williams Co."},
        {"ticker": "FCX", "name": "Freeport-McMoRan Inc."}
    ],
    "XLU": [
        {"ticker": "NEE", "name": "NextEra Energy Inc."},
        {"ticker": "SO", "name": "Southern Co."},
        {"ticker": "DUK", "name": "Duke Energy Corp."},
        {"ticker": "CEG", "name": "Constellation Energy Corp."}
    ],
    # Taiwan Sector Proxies / Mega Caps
    "0050.TW": [
        {"ticker": "2330.TW", "name": "台積電 (TSMC)"},
        {"ticker": "2317.TW", "name": "鴻海 (Foxconn)"},
        {"ticker": "2454.TW", "name": "聯發科 (MediaTek)"},
        {"ticker": "2308.TW", "name": "台達電 (Delta Electronics)"},
        {"ticker": "2382.TW", "name": "廣達 (Quanta Computer)"}
    ],
    "0052.TW": [
        {"ticker": "2330.TW", "name": "台積電 (TSMC)"},
        {"ticker": "2454.TW", "name": "聯發科 (MediaTek)"},
        {"ticker": "2317.TW", "name": "鴻海 (Foxconn)"},
        {"ticker": "2382.TW", "name": "廣達 (Quanta Computer)"},
        {"ticker": "2308.TW", "name": "台達電 (Delta Electronics)"}
    ],
    "0056.TW": [
        {"ticker": "2382.TW", "name": "廣達 (Quanta Computer)"},
        {"ticker": "3231.TW", "name": "緯創 (Wistron)"},
        {"ticker": "2301.TW", "name": "光寶科 (Lite-On Tech)"},
        {"ticker": "2357.TW", "name": "華碩 (ASUS)"},
        {"ticker": "2603.TW", "name": "長榮 (Evergreen Marine)"}
    ],
    "2330.TW": [{"ticker": "2330.TW", "name": "台積電 (TSMC)"}],
    "2881.TW": [{"ticker": "2881.TW", "name": "富邦金 (Fubon Financial)"}],
    "1301.TW": [{"ticker": "1301.TW", "name": "台塑 (Formosa Plastics)"}]
}

def get_stock_price(ticker: str) -> float:
    """Fetches the current market price for a given stock ticker."""
    try:
        t = yf.Ticker(ticker)
        # Try fast lookup
        price = t.fast_info.get("lastPrice")
        if price is not None:
            return float(price)
        # Fallback to history
        hist = t.history(period="1d")
        if not hist.empty:
            return float(hist["Close"].iloc[-1])
        return 0.0
    except Exception:
        return 0.0

def get_benchmark_performance(region_code: str) -> dict:
    """Calculates weekly and monthly ROI for regional benchmarks."""
    region_info = REGIONS.get(region_code)
    if not region_info:
        return {}
        
    benchmark_ticker = region_info["benchmark"]
    try:
        t = yf.Ticker(benchmark_ticker)
        hist = t.history(period="3mo")
        if hist.empty or len(hist) < 22:
            return {"current_price": 0, "weekly_return": 0, "monthly_return": 0}
            
        current_price = hist["Close"].iloc[-1]
        
        # Weekly (exactly 5 trading days ago, comparing -1 to -6)
        weekly_prev = hist["Close"].iloc[-6] if len(hist) >= 6 else hist["Close"].iloc[0]
        weekly_return = (current_price - weekly_prev) / weekly_prev
        
        # Monthly (exactly 20 trading days ago, comparing -1 to -21)
        monthly_prev = hist["Close"].iloc[-21] if len(hist) >= 21 else hist["Close"].iloc[0]
        monthly_return = (current_price - monthly_prev) / monthly_prev
        
        # Retrieve precise trading dates for transparency
        start_date_str = hist.index[-6].strftime("%Y-%m-%d") if len(hist) >= 6 else hist.index[0].strftime("%Y-%m-%d")
        end_date_str = hist.index[-1].strftime("%Y-%m-%d")
        
        return {
            "ticker": benchmark_ticker,
            "name": region_info["name"] + "大盤",
            "current_price": float(current_price),
            "weekly_return": float(weekly_return),
            "monthly_return": float(monthly_return),
            "start_date": start_date_str,
            "end_date": end_date_str
        }
    except Exception as e:
        print(f"Error fetching benchmark performance for {region_code}: {e}")
        return {"current_price": 0, "weekly_return": 0, "monthly_return": 0}

def get_sector_rankings(region_code: str) -> list:
    """Fetches weekly returns for configured sector ETFs and ranks them by performance."""
    region_info = REGIONS.get(region_code)
    if not region_info:
        return []
        
    rankings = []
    sector_etfs = region_info["sector_etfs"]
    
    # Calculate performance for each sector ETF
    for etf_ticker, info_val in sector_etfs.items():
        try:
            # Extract sector label name safely from integrated config structure
            label_name = info_val["name"] if isinstance(info_val, dict) else info_val
            
            t = yf.Ticker(etf_ticker)
            hist = t.history(period="10d")  # Pull slightly more to ensure enough days
            if hist.empty or len(hist) < 6:
                continue
                
            close_now = hist["Close"].iloc[-1]
            close_5d_ago = hist["Close"].iloc[-6]  # Exactly 5 trading days difference
            
            weekly_return = (close_now - close_5d_ago) / close_5d_ago
            
            # Retrieve precise trading dates for calculations
            start_date_str = hist.index[-6].strftime("%Y-%m-%d")
            end_date_str = hist.index[-1].strftime("%Y-%m-%d")
            
            rankings.append({
                "ticker": etf_ticker,
                "label": label_name,
                "weekly_return": float(weekly_return),
                "current_price": float(close_now),
                "start_date": start_date_str,
                "end_date": end_date_str
            })
        except Exception as e:
            print(f"Error ranking sector {etf_ticker}: {e}")
            
    # Sort in descending order (highest return first)
    rankings.sort(key=lambda x: x["weekly_return"], reverse=True)
    return rankings

_global_screener = None

def get_screener_instance():
    """Returns a shared global instance of QuantScreener to maintain session-wide screening history."""
    global _global_screener
    if _global_screener is None:
        from core.tools.screener import QuantScreener
        _global_screener = QuantScreener()
    return _global_screener

def get_etf_holdings(etf_ticker: str) -> list:
    """Returns the top representative stock holdings for an ETF or sector proxy dynamically using QuantScreener."""
    # Detect region dynamically from ticker suffix
    region = "Taiwan" if (etf_ticker.endswith(".TW") or etf_ticker.endswith(".TWO")) else "US"
    try:
        screener = get_screener_instance()
        picks = screener.screen_stocks(etf_ticker, region=region, limit=5)
        if picks:
            return [{"ticker": p["ticker"], "name": p["name"]} for p in picks]
    except Exception as e:
        print(f"[!] Warning: QuantScreener failed, falling back to static holdings. Error: {e}")
        
    return ETF_TOP_HOLDINGS.get(etf_ticker, [])

def get_stock_financials(ticker: str) -> dict:
    """Retrieves extensive fundamental metrics for the target stock ticker."""
    try:
        t = yf.Ticker(ticker)
        info = t.info
        fast_info = t.fast_info
        
        current_price = fast_info.get("lastPrice") or info.get("currentPrice") or info.get("regularMarketPrice")
        if not current_price:
            # Fallback to daily history
            hist = t.history(period="1d")
            current_price = hist["Close"].iloc[-1] if not hist.empty else None
            
        if not current_price:
            return {}
            
        # Parse financials safely
        financials = {
            "ticker": ticker,
            "company_name": info.get("longName") or info.get("shortName") or ticker,
            "current_price": float(current_price),
            "market_cap": info.get("marketCap"),
            "pe_ratio": info.get("trailingPE"),
            "forward_pe": info.get("forwardPE"),
            "peg_ratio": info.get("pegRatio"),
            "price_to_book": info.get("priceToBook"),
            "profit_margin": info.get("profitMargins"),
            "operating_margin": info.get("operatingMargins"),
            "roe": info.get("returnOnEquity"),
            "debt_to_equity": info.get("debtToEquity"),
            "revenue_growth": info.get("revenueGrowth"),
            "eps_growth": info.get("earningsGrowth"),
            "free_cash_flow": info.get("freeCashflow"),
            "fifty_day_sma": fast_info.get("fiftyDayAverage") or info.get("fiftyDayAverage"),
            "two_hundred_day_sma": fast_info.get("twoHundredDayAverage") or info.get("twoHundredDayAverage"),
            "recommendation_consensus": info.get("recommendationKey")  # e.g., 'buy', 'strong_buy'
        }
        
        # Clean null values to standard Python None
        for k, v in financials.items():
            if pd.isna(v):
                financials[k] = None
                
        return financials
    except Exception as e:
        print(f"Error fetching stock financials for {ticker}: {e}")
        return {}

def calculate_roi_since(ticker: str, purchase_date_str: str) -> dict:
    """Calculates ROI from a specific historical date to today."""
    try:
        t = yf.Ticker(ticker)
        # Pull historical data from purchase date onwards
        start_date = datetime.strptime(purchase_date_str, "%Y-%m-%d")
        # Pull up to current date (end date is exclusive in yfinance, so add 3 days buffer)
        end_date = datetime.now() + timedelta(days=3)
        
        hist = t.history(start=start_date.strftime("%Y-%m-%d"), end=end_date.strftime("%Y-%m-%d"))
        if hist.empty:
            return {"purchase_price": 0.0, "current_price": 0.0, "roi": 0.0}
            
        purchase_price = hist["Close"].iloc[0]
        current_price = hist["Close"].iloc[-1]
        roi = (current_price - purchase_price) / purchase_price
        
        return {
            "purchase_price": float(purchase_price),
            "current_price": float(current_price),
            "roi": float(roi)
        }
    except Exception as e:
        print(f"Error calculating ROI for {ticker} since {purchase_date_str}: {e}")
        return {"purchase_price": 0.0, "current_price": 0.0, "roi": 0.0}
