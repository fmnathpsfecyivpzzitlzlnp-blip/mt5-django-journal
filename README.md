А, точно! Я в прошлом сообщении дал тебе только кусок с новыми фичами, и из-за этого потерялась вся пошаговая инструкция по установке. Извини за это!

Кстати, раз мы уже сделали Аналитику и Плейбук, я в разделе Roadmap (Планы) отметил их галочками [x] как выполненные. Это покажет всем на GitHub, что проект активно развивается!

Вот полный, финальный и объединенный файл README.md. Скопируй его целиком от первой до последней строчки, в нем идеальное форматирование со всеми блоками кода:

Markdown
# 📈 Quantum Trade Journal: MT5 Auto-Sync & ICT Analytics

A powerful, locally-hosted, and fully automated trading journal built with **Django** and **MQL5**. Designed specifically for traders utilizing Smart Money Concepts (SMC) and ICT methodologies.

Stop logging trades manually. Simply close your position in MetaTrader 5, and the Expert Advisor (EA) will automatically collect the trade data, capture multi-timeframe screenshots (M1, M5, M15, H1, H4, D1 + macro-zoom of the exit), and push them directly to your local journal via Webhook.

![Trade Journal Dashboard Screenshot](LINK_TO_YOUR_IMAGE_HERE)

## 🚀 What's Inside Quantum Trade Journal (v1.0)

We built the ultimate all-in-one platform from scratch for traders utilizing Smart Money Concepts (SMC / ICT). The platform covers 100% of your needs: from automated data collection to deep psychological analysis and prop-firm account management.

### 📊 1. Advanced Analytics & Prop-Tracker
Your statistics don't lie anymore. The Django backend intelligently distinguishes real trades from tests or mentor reviews.
* **Prop-Tracker:** Built-in tracker for passing challenges (FTMO, FundedNext, etc.). Automatically calculates Daily Drawdown, High Water Mark (Maximum Drawdown), and Profit Target.
* **Smart Math:** Calculates Winrate, Risk/Reward (R:R), as well as Maximum Win and Loss Streaks.
* **Heatmap:** A 30-day profitability calendar.
* **Performance Slices:** PnL charts by Entry Logic (Trend / Reversal), time of day (Asia, London, NY AM/PM sessions), and timeframes.

### 👽 2. Quantum Review (Mentor Mode)
You don't have to blow your account to learn.
* **Adding 3rd-Party Trades:** You can log a trade from your mentor or colleague to the database in two clicks. The backend automatically assigns it zero volume and zero PnL so it **does not ruin your personal performance stats**.
* **Side-by-Side Comparison:** In the review card, you can load your screenshots on the left and the mentor's screenshots (with comments and mistakes pointed out) on the right. Compare your logic step-by-step across all timeframes (D1, H4, H1, M15, M5, M1).
* **Smart Dropzone:** Paste screenshots directly from the clipboard (`Ctrl+V`) or via TradingView links.

### 📘 3. Setup Matrix (ICT Playbook)
The golden collection of your A+ setups, divided into 4 battle quadrants.
* **Long + Trend:** Trading within a bullish Order Flow (Discount zones).
* **Long + Reversal:** Catching the bottom via manipulation and Market Structure Shift (MSS).
* **Short + Trend:** Trading within a bearish Order Flow (Premium zones).
* **Short + Reversal:** Catching the top via manipulation and MSS.
* Before taking a trade, simply open the Playbook and compare the current live chart with your ideal templates.

### 🤖 4. Seamless MetaTrader 5 Integration
No more manual logging.
* **Auto-Screenshots:** Upon closing a trade, the custom MQL5 Expert Advisor (EA) seamlessly opens clean charts on 6 timeframes in the background, takes screenshots, captures a macro-zoom of the exit moment, and sends the entire package to your local server.
* **Instant Inbox:** Trades instantly land in your Inbox, where you can bulk-tag the macro-context (Trend, Logic, Psychology) before sending them to the main Journal.

## 🛠 Tech Stack
* **Backend:** Python, Django, Django REST Framework.
* **Frontend:** HTML, Bootstrap 5, JavaScript, Chart.js.
* **MetaTrader Integration:** MQL5 (Expert Advisor), MetaTrader5 Python Package.
* **Database:** SQLite (default, ready for PostgreSQL migration).

---

## 🚀 Installation & Setup (Local Environment)

### 1. Web Server Setup (Django)
1. Clone the repository:
   ```bash
   git clone [https://github.com/fmnathpsfecyivpzzitlzlnp-blip/mt5-django-journal.git](https://github.com/fmnathpsfecyivpzzitlzlnp-blip/mt5-django-journal.git)
   cd mt5-django-journal
Create and activate a virtual environment:

Bash
python -m venv .venv
source .venv/Scripts/activate  # For Windows
# source .venv/bin/activate    # For macOS/Linux
Install the dependencies:

Bash
pip install -r requirements.txt
Apply database migrations and create a superuser:

Bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
Run the development server:

Bash
python manage.py runserver
The application will be available at: http://127.0.0.1:8000

2. MetaTrader 5 Setup (Expert Advisor)
Open your MT5 terminal and go to Tools -> Options -> Expert Advisors.

Check "Allow WebRequest for listed URL" and add your local server address: http://127.0.0.1:8000

Copy the AutoJournal_Webhook.mq5 file (located in the mql5/ folder of this repo) into your terminal's MQL5/Experts/ directory.

Open the file in MetaEditor and compile it (F7).

Attach the compiled EA to any chart (e.g., EURUSD).

⚠️ CRITICAL STEP: In the EA settings (Inputs tab), you must enter the exact username and password of the Django superuser you created in Step 1.4. If you skip this, the EA will not be authorized to send trades to your journal!

That's it! Every time you close a trade, the data and screenshots will instantly appear in your Journal's Inbox.

3. Load Historical Data (Optional)
If you want to import your past trading history from MT5 into the journal:

Ensure the MT5 terminal is running and you are logged into your broker.

Open scripts/mt5_sync.py and update the credentials inside the code with your Django superuser login.

Run the script:

Bash
python scripts/mt5_sync.py
🗺 Roadmap
[x] Advanced Analytics Dashboard (Equity curve, Win Rate, R/R tracking, Tag performance).

[x] Playbook functionality to store A+ setup templates.

[ ] Migrate from SQLite to PostgreSQL for better scalability.

[ ] Dockerize the application (docker-compose) for one-click deployment.

[ ] AWS S3 / Cloud storage integration for handling gigabytes of screenshots.

🤝 Contributing
Pull requests are welcome! If you have ideas for improving the UI, optimizing the MQL5 EA, or adding new ICT concepts, feel free to open an Issue or submit a PR.