import sys
import os
import json
import unicodedata
from datetime import datetime, date
from pathlib import Path

# Add parent directory to path to ensure absolute imports work
sys.path.append(str(Path(__file__).resolve().parent))

# Import Config, Tools & Database
from core.config import DB_TYPE, REPORT_LANGUAGE
import core.db_manager as db
import core.tools.yahoo_finance as yf_tool

# Console Colors
GREEN = "\033[92m"
RED = "\033[91m"
BLUE = "\033[94m"
YELLOW = "\033[93m"
RESET = "\033[0m"
BOLD = "\033[1m"
UNDERLINE = "\033[4m"

def get_display_width(s):
    """Calculates terminal rendering width of a string containing CJK characters and emojis."""
    width = 0
    for c in s:
        val = unicodedata.east_asian_width(c)
        if val in ('W', 'F', 'A'):
            width += 2
        elif ord(c) >= 0x1F300:  # Emoji range
            width += 2
        else:
            width += 1
    return width

def pad_left(s, width):
    """Pads string with spaces on the left based on terminal display width."""
    disp_w = get_display_width(s)
    if disp_w >= width:
        return s
    return " " * (width - disp_w) + s

def pad_right(s, width):
    """Pads string with spaces on the right based on terminal display width."""
    disp_w = get_display_width(s)
    if disp_w >= width:
        return s
    return s + " " * (width - disp_w)

def pad_center(s, width):
    """Centers string inside a given width based on terminal display width."""
    disp_w = get_display_width(s)
    if disp_w >= width:
        return s
    pad_total = width - disp_w
    pad_left_cnt = pad_total // 2
    pad_right_cnt = pad_total - pad_left_cnt
    return " " * pad_left_cnt + s + " " * pad_right_cnt

def print_header(title):
    """Renders a beautifully aligned terminal box considering display width of emojis and CJK."""
    inside_width = 78
    padded_title = pad_center(title, inside_width)
    print(f"\n{BOLD}{BLUE}┌" + "─" * inside_width + "┐")
    print(f"│{padded_title}│")
    print(f"└" + "─" * inside_width + "┘" + RESET)

def format_roi_padded(roi, width):
    """Pads and colors ROI percentages considering display width before wrapping with ANSI codes."""
    if roi is None:
        return pad_left("N/A", width)
    percentage = roi * 100
    color = GREEN if percentage >= 0 else RED
    sign = "+" if percentage >= 0 else ""
    raw_str = f"{sign}{percentage:.2f}%"
    padded_raw = pad_left(raw_str, width)
    return padded_raw.replace(raw_str, f"{color}{raw_str}{RESET}")

def get_progress_bar(start_date_str, total_days=30):
    """Calculates progress days and renders a beautiful progress bar."""
    try:
        start_date = datetime.strptime(start_date_str.split(" ")[0], "%Y-%m-%d").date()
    except Exception:
        start_date = date.today()
        
    today = date.today()
    elapsed = (today - start_date).days + 1
    elapsed = max(1, elapsed)  # Day 1 start
    
    percent = min(1.0, elapsed / total_days)
    filled_length = int(40 * percent)
    bar = "█" * filled_length + "░" * (40 - filled_length)
    
    return elapsed, percent * 100, bar

def main():
    # 1. Gather stats from Database
    reports = db.list_all_reports()
    active_recs = db.get_active_recommendations()
    perf_data = db.get_historical_performance()
    closed_recs = perf_data.get("closed", [])
    
    # Define start date of 30-day sandbox
    if reports:
        sorted_reports = sorted(reports, key=lambda x: x["date"])
        start_date_str = sorted_reports[0]["date"]
        status_label = f"已啟動 (自 {start_date_str} 起)"
    else:
        start_date_str = datetime.now().strftime("%Y-%m-%d")
        status_label = "尚未正式啟動 (等待首航週報產出)"

    # Calculate 30-day progress
    elapsed_days, progress_percent, prog_bar = get_progress_bar(start_date_str)
    
    # 2. Render System Header & Status
    print_header("📊 投資研究多代理人系統 - 30天實戰觀測期監控看板 📊")
    
    print(f"  {BOLD}實戰觀測期進度：{RESET}")
    if reports:
        print(f"  [{prog_bar}] {BOLD}第 {elapsed_days} / 30 天{RESET} ({progress_percent:.1f}% 已完成)")
    else:
        print(f"  [░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░] {BOLD}第 0 / 30 天{RESET} (等待明早 10:00 週報產出)")
        
    print(f"\n  • 系統狀態　　: {BOLD}{status_label}{RESET}")
    print(f"  • 週報產出總數: {BOLD}{len(reports)} 份{RESET}")
    print(f"  • 在庫追蹤標的: {BOLD}{len(active_recs)} 檔{RESET}")
    print(f"  • 已平倉結案數: {BOLD}{len(closed_recs)} 檔{RESET}")
    print(f"  • 資料庫配置　: {BOLD}{DB_TYPE.upper()}{RESET}")
    
    # 3. Render Historical Performance (Closed Positions)
    print_header("🏆 歷史交易績效 (Realized Performance - Closed Positions)")
    
    if closed_recs:
        win_rate = perf_data["win_rate"] * 100
        avg_roi = perf_data["avg_roi"] * 100
        total_roi = sum(r["performance"] for r in closed_recs) * 100
        
        # Find best and worst trades
        best_trade = max(closed_recs, key=lambda x: x["performance"])
        worst_trade = min(closed_recs, key=lambda x: x["performance"])
        
        best_roi_formatted = format_roi_padded(best_trade['performance'], 0).strip()
        worst_roi_formatted = format_roi_padded(worst_trade['performance'], 0).strip()
        total_roi_formatted = format_roi_padded(sum(r['performance'] for r in closed_recs), 0).strip()
        avg_roi_formatted = format_roi_padded(perf_data['avg_roi'], 0).strip()
        
        print(f"  • 交易勝率 (Win Rate)  : {BOLD}{GREEN if win_rate >= 50 else RED}{win_rate:.1f}%{RESET} ({sum(1 for r in closed_recs if r['performance'] > 0)} 勝 / {len(closed_recs)} 敗)")
        print(f"  • 已實現累計投報率   : {BOLD}{total_roi_formatted}{RESET}")
        print(f"  • 每筆平均已實現回報 : {BOLD}{avg_roi_formatted}{RESET}")
        print(f"  • 最佳平倉黑馬標的   : {BOLD}{best_trade['ticker']} ({best_trade['company_name']}) {best_roi_formatted}{RESET}")
        print(f"  • 最差平倉風控標的   : {BOLD}{worst_trade['ticker']} ({worst_trade['company_name']}) {worst_roi_formatted}{RESET}")
    else:
        print(f"  {YELLOW}目前尚無歷史平倉紀錄。當持股達到止盈目標價或跌破止損點時，系統會自動平倉並計算績效。{RESET}")

    # 4. Render Active Portfolio Holdings (Unrealized Portfolio)
    print_header("📈 當前在庫追蹤標的 (Active Portfolio - Unrealized)")
    
    if active_recs:
        # Table Header aligned perfectly to exactly 80 cells
        header = (
            pad_right("市場", 4) + " | " +
            pad_right("代號", 7) + " | " +
            pad_right("企業名稱", 17) + " | " +
            pad_left("買入價", 7) + " | " +
            pad_left("當前價", 7) + " | " +
            pad_center("止盈 / 止損", 14) + " | " +
            pad_left("未實現損益", 9)
        )
        print(f"{BOLD}{UNDERLINE}{header}{RESET}")
        
        total_unrealized_roi = 0.0
        
        for rec in active_recs:
            ticker = rec["ticker"]
            region = "美股" if rec["region"] == "US" else "台股"
            recommend_price = rec["recommend_price"]
            target_price = rec["target_price"]
            stop_loss = rec["stop_loss"]
            company_name = rec["company_name"]
            
            # Shorten long company names safely to 17 cells
            comp_disp_w = get_display_width(company_name)
            if comp_disp_w > 17:
                truncated = ""
                current_w = 0
                for char in company_name:
                    char_w = 2 if unicodedata.east_asian_width(char) in ('W', 'F', 'A') or ord(char) >= 0x1F300 else 1
                    if current_w + char_w + 3 > 17:
                        truncated += "..."
                        break
                    truncated += char
                    current_w += char_w
                company_name = truncated
                
            # Fetch current live price
            current_price = yf_tool.get_stock_price(ticker)
            if current_price == 0.0:
                current_price = recommend_price  # Fallback to recommend price if market offline
                
            unrealized_roi = (current_price - recommend_price) / recommend_price
            total_unrealized_roi += unrealized_roi
            
            # Format ranges
            sl_tp_range = f"{stop_loss or 0.0:.1f} - {target_price or 0.0:.1f}"
            
            region_str = pad_right(region, 4)
            ticker_str = pad_right(ticker, 7)
            company_str = pad_right(company_name, 17)
            recommend_price_str = pad_left(f"{recommend_price:.2f}", 7)
            current_price_str = pad_left(f"{current_price:.2f}", 7)
            sl_tp_range_str = pad_center(sl_tp_range, 14)
            unrealized_roi_str = format_roi_padded(unrealized_roi, 9)
            
            print(f"{region_str} | {ticker_str} | {company_str} | {recommend_price_str} | {current_price_str} | {sl_tp_range_str} | {unrealized_roi_str}")
        
        avg_unrealized = total_unrealized_roi / len(active_recs)
        avg_unrealized_formatted = format_roi_padded(avg_unrealized, 0).strip()
        print("─" * 80)
        print(f"  • 在庫平均未實現回報率：{BOLD}{avg_unrealized_formatted}{RESET}")
    else:
        print(f"  {YELLOW}目前在庫無追蹤股票。週六早上系統會執行量化選股掃描並新增追蹤標的。{RESET}")

    # 5. Render Completed Transactions Ledger
    if closed_recs:
        print_header("📜 歷史已平倉結案明細 (Closed Trades Ledger)")
        header_closed = (
            pad_right("市場", 4) + " | " +
            pad_right("代號", 7) + " | " +
            pad_right("企業名稱", 17) + " | " +
            pad_left("買入", 7) + " | " +
            pad_left("平倉", 7) + " | " +
            pad_center("平倉日期", 14) + " | " +
            pad_left("最終損益", 9)
        )
        print(f"{BOLD}{UNDERLINE}{header_closed}{RESET}")
        
        # Sort closed by date descending
        for rec in sorted(closed_recs, key=lambda x: x.get("close_date", ""), reverse=True)[:10]:
            ticker = rec["ticker"]
            region = "美股" if rec["region"] == "US" else "台股"
            recommend_price = rec["recommend_price"]
            close_price = rec["close_price"] or 0.0
            company_name = rec["company_name"]
            
            comp_disp_w = get_display_width(company_name)
            if comp_disp_w > 17:
                truncated = ""
                current_w = 0
                for char in company_name:
                    char_w = 2 if unicodedata.east_asian_width(char) in ('W', 'F', 'A') or ord(char) >= 0x1F300 else 1
                    if current_w + char_w + 3 > 17:
                        truncated += "..."
                        break
                    truncated += char
                    current_w += char_w
                company_name = truncated
                
            close_date = rec.get("close_date", "N/A")
            performance = rec["performance"]
            
            region_str = pad_right(region, 4)
            ticker_str = pad_right(ticker, 7)
            company_str = pad_right(company_name, 17)
            recommend_price_str = pad_left(f"{recommend_price:.2f}", 7)
            close_price_str = pad_left(f"{close_price:.2f}", 7)
            close_date_str = pad_center(close_date, 14)
            performance_str = format_roi_padded(performance, 9)
            
            print(f"{region_str} | {ticker_str} | {company_str} | {recommend_price_str} | {close_price_str} | {close_date_str} | {performance_str}")
            
        if len(closed_recs) > 10:
            print(f"  * 僅顯示最近 10 筆平倉紀錄（共計 {len(closed_recs)} 筆）*")
            
    print("\n" + "=" * 80)
    print(f"💡 {BOLD}提示：{RESET}本看板資料與您的 {DB_TYPE.upper()} 資料庫完全同步。")
    print("   如需手動強制觸發日內持股對帳，請隨時執行：")
    print(f"   {GREEN}pipenv run python check_portfolio.py{RESET}")
    print("=" * 80 + "\n")

if __name__ == "__main__":
    main()
