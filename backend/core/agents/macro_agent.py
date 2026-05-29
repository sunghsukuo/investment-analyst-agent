from core.agents.base_agent import BaseAgent

SYSTEM_INSTRUCTION = """
你是一位資深的「總體經濟分析師 (Macroeconomic Analyst)」。你的職責是深入分析特定國家/區域當前所處的宏觀經濟週期與金融政策環境。

你需要評估以下面向：
1. 利率政策與通膨趨勢（例如：美聯儲/台灣央行的利率態度、CPI/PCE 數據）。
2. 重要經濟指標（如出口訂單、景氣對策信號、就業市場或製造業 PMI）。
3. 匯率變動（如美元指數 DXY、美金對台幣匯率 TWD）對進出口板塊與外資動向的潛在影響。
4. 大盤指數週與月漲幅呈現出的資金心理學與大局動能。

請根據提供的大盤表現與最新總經新聞進行深度整合分析，產出一份結構清晰、論理嚴密、具高度專業可讀性的「區域總體經濟分析報告」。
請務必使用「繁體中文（台灣習慣財經用語）」撰寫，避免大陸財經用語（例如：將「板塊」翻譯為「板塊」或「產業分類」，「回測」代替「回溯」，「指標」而非「指標」，並使用台灣股市慣用語，如「外資」、「美聯儲」或「聯準會」、「央行」等）。

輸出格式請依照以下 Markdown 結構：
### 🌐 [國家名稱] 總體經濟環境分析
* **當前宏觀形勢與政策風向**：[簡明分析央行利率決策、通膨發展與當前景氣週期]
* **資金動能與大盤表現評估**：[分析大盤 benchmark 近期表現、外資動能與匯率影響]
* **關鍵宏觀新聞事件解讀**：[挑選 2-3 個最關鍵的最新總經新聞，解析其對市場短中期的影響]
* **宏觀環境對產業配置的啟示**：[總結當前總經環境最有利於哪些板塊，最不利於哪些板塊]
"""

class MacroAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="MacroAgent",
            role="Macroeconomic Analyst",
            system_instruction=SYSTEM_INSTRUCTION
        )

    def analyze(self, region_name: str, benchmark_data: dict, news_data: list) -> str:
        """Executes the macro analysis for a given region."""
        # Format the input prompt with tools data
        formatted_news = ""
        for i, art in enumerate(news_data):
            formatted_news += f"新聞 {i+1}: {art['title']}\n   發布時間: {art['pub_date']}\n   摘要: {art['summary']}\n\n"
            
        prompt = f"""
請針對【{region_name}】進行總體經濟環境深度分析。

【數據資料】：
* 大盤基準 Ticker: {benchmark_data.get('ticker')}
* 大盤名稱: {benchmark_data.get('name')}
* 當前價格/指數點數: {benchmark_data.get('current_price'):,.2f}
* 週報酬率: {benchmark_data.get('weekly_return', 0)*100:.2f}%
* 月報酬率: {benchmark_data.get('monthly_return', 0)*100:.2f}%

【當週最新相關總經新聞摘要】：
{formatted_news if formatted_news else "（暫無相關最新總經新聞）"}

請依據你的專業知識與上述客觀數據，產出專屬的總經分析報告。
"""
        return self.run(prompt)
