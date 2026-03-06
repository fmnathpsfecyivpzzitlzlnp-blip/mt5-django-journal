# 📈 Quantum Trade Journal: MT5 Auto-Sync & ICT Analytics

A powerful, locally-hosted, and fully automated trading journal built with **Django** and **MQL5**. Designed specifically for traders utilizing Smart Money Concepts (SMC) and ICT methodologies.

Stop logging trades manually. Simply close your position in MetaTrader 5, and the Expert Advisor (EA) will automatically collect the trade data, capture multi-timeframe screenshots (M1, M5, M15, H1, H4, D1 + macro-zoom of the exit), and push them directly to your local journal via Webhook.

![Trade Journal Dashboard Screenshot](LINK_TO_YOUR_IMAGE_HERE)

## 🔥 Key Features
* **Absolute Automation (MQL5 Webhook):** Upon closing a trade, the EA seamlessly navigates through required timeframes in the background, takes screenshots, converts them to Base64, and sends them to the Django backend.
* **Mass Tagging (Inbox):** Quickly assign macro-context tags (Trend, Entry Logic, Psychology) to dozens of trades with just a few clicks before sending them to the main journal.
* **Quantum Review (Mentor Mode):** A dedicated interface for deep trade analysis. Compare your initial expectations side-by-side with a mentor's review (RS) across every timeframe.
* **ICT Confluence Factors:** Built-in support for tagging SMC/ICT concepts such as FVG, Order Blocks (OB), Liquidity Sweeps, MSS, and Breaker Blocks.

## 🛠 Tech Stack
* **Backend:** Python, Django, Django REST Framework.
* **Frontend:** HTML, Bootstrap 5, JavaScript (Fetch API).
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
[ ] Migrate from SQLite to PostgreSQL for better scalability.

[ ] Dockerize the application (docker-compose) for one-click deployment.

[ ] AWS S3 / Cloud storage integration for handling gigabytes of screenshots.

[ ] Advanced Analytics Dashboard (Equity curve, Win Rate, R/R tracking, Tag performance).

[ ] Playbook functionality to store A+ setup templates.

🤝 Contributing
Pull requests are welcome! If you have ideas for improving the UI, optimizing the MQL5 EA, or adding new ICT concepts, feel free to open an Issue or submit a PR.