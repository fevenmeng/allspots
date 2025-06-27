Dev.to Article Scraper with Supabase, NLP & GitHub Actions
This project scrapes the latest articles from Dev.to, analyzes their content using natural language processing (NLP), and stores the processed data into a Supabase PostgreSQL database. It is fully automated using GitHub Actions to run every 3 hours.

🛠 Built with Python, BeautifulSoup, NLTK, Supabase, GitHub Actions, and Power BI.

📌 Features
Scrapes latest article metadata (title, link, author, tags, publish time, etc.)

Extracts and cleans full article content

Analyzes sentiment using VADER

Counts meaningful words (excluding stopwords)

Detects article language

Stores data in a Supabase PostgreSQL database

Automates execution every 3 hours using GitHub Actions

Visualized using Power BI dashboard

📂 Project Structure
graphql
Copy
Edit
.
├── .github/
│   └── workflows/
│       └── scraper.yml     # GitHub Actions automation script
├── main.py                 # Main Python script
├── requirements.txt        # Python dependencies
├── README.md               # Documentation
🚀 Getting Started
1. Clone the Repository
bash
Copy
Edit
git clone https://github.com/your-username/devto-scraper.git
cd devto-scraper
2. Install Dependencies
bash
Copy
Edit
pip install -r requirements.txt
3. Configure Environment Variables
Create three secrets in your GitHub repo under:

GitHub → Settings → Secrets and variables → Actions → New repository secret

Add the following:

Name	Description
DB_USER	Your Supabase database username
DB_PASSWORD	Your Supabase database password
DB_HOST	Your Supabase host URL (e.g. xyz.supabase.co)

These will be used by GitHub Actions to connect to your Supabase instance securely.

⚙️ GitHub Actions: Automated Workflow
This project includes a GitHub Actions workflow (scraper.yml) that:

Runs every 3 hours using a cron schedule

Installs Python dependencies

Executes the scraping and analysis script

.github/workflows/scraper.yml
yaml
Copy
Edit
name: DEV TO Automation

on:
  schedule:
    - cron:  "0 */3 * * *"  # Every 3 hours
  workflow_dispatch:

jobs:
  run_script:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout Repository
        uses: actions/checkout@v4

      - name: Set Up Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.x"

      - name: Install Dependencies
        run: pip install -r requirements.txt

      - name: Run main.py with Environment Variables
        env:
          DB_USER: ${{ secrets.DB_USER }}
          DB_PASSWORD: ${{ secrets.DB_PASSWORD }}
          DB_HOST: ${{ secrets.DB_HOST }}
        run: python main.py
📊 Power BI Dashboard
The data stored in Supabase can be visualized using Power BI Desktop. Connect your Power BI to the Supabase PostgreSQL database using your credentials, and build dashboards showing:

Sentiment distribution

Word counts

Article language

Trends over time

🧠 Tech Stack
Python 3.x

BeautifulSoup – for HTML parsing

Fake UserAgent – to mimic real user requests

NLTK – stopwords & sentiment analysis

LangID & PyCountry – language detection

PostgreSQL (hosted on Supabase)

GitHub Actions – automation

Power BI – visualization

📬 Contributing
Feel free to fork this repo, improve the script, or add more NLP features! Pull requests are welcome.

📃 License
MIT License © 2025
