from core.agents.base_agent import BaseAgent

SYSTEM_INSTRUCTION = """
你是一位頂尖的「標的篩選與基本面分析師 (Target Selection & Fundamental Analyst)」。你的職責是深入解讀企業的財務報表與基本面經營數據，融合市場估值（如本益比 P/E、本益成長比 PEG、股價淨值比 P/B）與安全邊際，篩選出具備高勝率投資價值的優秀標的。

你需要深入剖析以下指標：
1. 獲利能力與利潤率：毛利率、營業利益率、淨利率、股東權益報酬率 (ROE)。
2. 成長性指標：營收年增率 (Revenue Growth)、每股盈餘年增率 (EPS Growth)。
3. 估值水位與合理性：目前本益比 P/E、預估本益比 Forward P/E、本益成長比 PEG（低於 1.0 是否具備低估優勢？）。
4. 財務健康度：負債權益比 (Debt to Equity Ratio)、自由現金流狀況 (Free Cash Flow)。
5. 技術位階：股價相對於 50-day SMA 與 200-day SMA 的位階（多頭排列還是超跌？）。

融合提供的「總體經濟狀況」與「最新新聞催化分析」，請產出一份極具含金量的「標的基本面深度估值分析報告」，並給予非常具體的推薦買入價格區間、目標價與防守停損點。

請務必使用「繁體中文（台灣習慣財經用語）」撰寫。

輸出格式請依照以下 Markdown 結構：
### 📊 [標的名/代碼] 基本面估值與投資價值評估
* **投資評級與核心論點**：[強烈買入 Strong Buy / 買入 Buy / 持有 Hold] (請附帶一句話最核心的核心投資亮點)
* **基本面關鍵指標深度剖析**：
  * *成長與獲利能力*：[分析營收、EPS 增速與利潤率表現]
  * *估值與安全邊際評估*：[分析 P/E、PEG 與歷史水平，判斷目前是否被低估]
  * *財務結構與風控防線*：[分析負債率與自由現金流，評估暴雷風險]
* **結合總經與消息面的綜合評語**：[結合當前宏觀政策與新聞重大消息，說明該公司有何天時地利]
* **具體投資操作指南**：
  * **當前價格**：[現價]
  * **推薦買入區間**：[給出合理的買入區間，如 140 - 145 元]
  * **中線目標價**：[根據估值算出的合理中線期望價]
  * **防禦停損點**：[根據技術均線或前波低點設定的停損位]
  * **建議持倉權重**：[例如：適中佔比 10%、加碼配置 15% 等]
"""

class FundamentalAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="FundamentalAgent",
            role="Fundamental Analyst",
            system_instruction=SYSTEM_INSTRUCTION
        )

    def analyze(self, ticker: str, company_name: str, financials: dict, news_analysis: str, macro_context: str) -> str:
        """Executes the fundamental valuation and investment recommendation for an asset."""
        
        # Build prompt formatting key metrics safely
        def safe_fmt(val, prefix="", suffix="", placeholder="N/A"):
            if val is None:
                return placeholder
            if isinstance(val, (int, float)):
                if suffix == "%":
                    return f"{prefix}{val*100:.2f}%"
                if val > 1_000_000_000:
                    return f"{prefix}{val/1_000_000_000:.2f} B"
                return f"{prefix}{val:,.2f}"
            return f"{prefix}{val}{suffix}"

        prompt = f"""
請為標的【{company_name} ({ticker})】進行深度基本面財務估值與投資價值評估。

【標的財務基本面數據】：
* 股票代碼: {ticker}
* 企業全名: {company_name}
* 當前股價: {safe_fmt(financials.get('current_price'))}
* 市值: {safe_fmt(financials.get('market_cap'))}
* 過去本益比 (PE): {safe_fmt(financials.get('pe_ratio'))}
* 未來本益比 (Forward PE): {safe_fmt(financials.get('forward_pe'))}
* 本益成長比 (PEG): {safe_fmt(financials.get('peg_ratio'))}
* 股價淨值比 (PB): {safe_fmt(financials.get('price_to_book'))}
* 淨利潤率: {safe_fmt(financials.get('profit_margin'), suffix="%")}
* 營業利益率: {safe_fmt(financials.get('operating_margin'), suffix="%")}
* 股東權益報酬率 (ROE): {safe_fmt(financials.get('roe'), suffix="%")}
* 負債權益比 (Debt/Equity): {safe_fmt(financials.get('debt_to_equity'), suffix="%")}
* 營收年增率 (Revenue Growth): {safe_fmt(financials.get('revenue_growth'), suffix="%")}
* EPS年增率 (EPS Growth): {safe_fmt(financials.get('eps_growth'), suffix="%")}
* 自由現金流: {safe_fmt(financials.get('free_cash_flow'))}
* 50天均線 (50-day SMA): {safe_fmt(financials.get('fifty_day_sma'))}
* 200天均線 (200-day SMA): {safe_fmt(financials.get('two_hundred_day_sma'))}
* 分析師共識建議: {safe_fmt(financials.get('recommendation_consensus'))}

【該標的最新的新聞與重大消息面分析】：
{news_analysis}

【當前大市場總體經濟環境脈絡】：
{macro_context}

請綜合上述的所有量化數據與定性脈絡，撰寫出一份極致專業的「基本面財務估值報告」與「明確操作指引」。
"""
        return self.run(prompt)
