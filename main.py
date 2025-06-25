import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import pandas as pd
import os
import re
import nltk
from nltk.corpus import stopwords
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import langid
import pycountry
import psycopg2

# ------------------------------
# NLTK setup
# ------------------------------
nltk.download('stopwords')
nltk.download('vader_lexicon')

# ------------------------------
# Scrape Latest DEV.to Articles
# ------------------------------
url = 'https://dev.to/latest'
ua = UserAgent()
headers = {'User-Agent': ua.random}
page = requests.get(url, headers=headers)
soup = BeautifulSoup(page.content, 'html.parser')
blog_box = soup.find_all('div', class_='crayons-story')

links, titles, time_uploaded, authors, tags, reading_times = [], [], [], [], [], []

for box in blog_box:
    # Links and Titles
    title_elem = box.find('h2', class_='crayons-story__title')
    if title_elem and title_elem.a:
        links.append(title_elem.a['href'])
        titles.append(title_elem.text.replace('\n', '').strip())
    else:
        links.append('None')
        titles.append('None')

    # Time Uploaded
    time_elem = box.find('time', attrs={'datetime': True})
    time_uploaded.append(time_elem['datetime'] if time_elem else 'None')

    # Author
    author_elem = box.find('a', class_='crayons-story__secondary fw-medium m:hidden')
    authors.append(author_elem.text.strip() if author_elem else 'None')

    # Tags
    tag_elem = box.find('div', class_='crayons-story__tags')
    tags.append(tag_elem.text.replace('\n', ' ').strip() if tag_elem else 'None')

    # Reading Time
    rt_elem = box.find('div', class_='crayons-story__save')
    reading_times.append(rt_elem.text.replace('\n', ' ').strip() if rt_elem else 'None')

# Create initial DataFrame
df = pd.DataFrame({
    'Link': links,
    'Title': titles,
    'Time_Uploaded': time_uploaded,
    'Authors': authors,
    'Tags': tags,
    'Reading_Time': reading_times
})
df = df[df['Link'] != 'None']

# ------------------------------
# Scrape Full Article Content
# ------------------------------
article = []
article_link = []

def get_full_content(second_url):
    try:
        ua = UserAgent()
        headers = {'User-Agent': ua.random}
        page = requests.get(second_url, headers=headers)
        soup = BeautifulSoup(page.content, 'html.parser')

        content = soup.find('div', class_='crayons-article__main')
        if not content:
            article.append("None")
            article_link.append(second_url)
            return

        paragraphs = content.find_all('p')
        text = ' '.join([p.text.strip() for p in paragraphs])
        article.append(text)
        article_link.append(second_url)

    except Exception as e:
        article.append("Error fetching article")
        article_link.append(second_url)

for link in df.Link:
    full_url = 'https://dev.to' + link if link.startswith('/') else link
    get_full_content(full_url)

article_df = pd.DataFrame({
    'Article_Content': article,
    'Link': article_link
})

# Merge both DataFrames
merge_df = pd.merge(df, article_df, on='Link', how='inner')

# ------------------------------
# Word Count (Regex-based, no punkt)
# ------------------------------
def count_words_without_stopwords(text):
    if isinstance(text, str):
        words = re.findall(r'\b\w+\b', text.lower())
        stop_words = set(stopwords.words('english'))
        return len([w for w in words if w not in stop_words])
    return 0

merge_df['Word_Count'] = merge_df['Article_Content'].apply(count_words_without_stopwords)

# ------------------------------
# Sentiment Analysis
# ------------------------------
sid = SentimentIntensityAnalyzer()

def get_sentiment(text):
    scores = sid.polarity_scores(text)
    compound = scores['compound']
    if compound >= 0.05:
        return 'Positive', compound
    elif compound <= -0.05:
        return 'Negative', compound
    else:
        return 'Neutral', compound

merge_df[['Sentiment', 'Compound_Score']] = merge_df['Article_Content'].astype(str).apply(
    lambda x: pd.Series(get_sentiment(x))
)

# ------------------------------
# Language Detection
# ------------------------------
def detect_language(text):
    text = str(text) if pd.notna(text) else ''
    lang, _ = langid.classify(text)
    return lang

merge_df['Language'] = merge_df['Article_Content'].apply(detect_language)
merge_df['Language'] = merge_df['Language'].map(
    lambda code: pycountry.languages.get(alpha_2=code).name if pycountry.languages.get(alpha_2=code) else code
)

# ------------------------------
# Clean Reading Time
# ------------------------------
merge_df['Reading_Time'] = (
    merge_df['Reading_Time']
    .astype(str)
    .str.replace(' min read', '', regex=False)
    .str.strip()
    .replace('', '0')
    .astype(int)
)

# ------------------------------
# Insert into PostgreSQL
# ------------------------------
db_parms = {
    "dbname": "postgres",
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST"),
    "port": "5432"
}

try:
    conn = psycopg2.connect(**db_parms)
    cursor = conn.cursor()

    insert_query = """
        INSERT INTO articles 
        (Link, Title, Time_Uploaded, Authors, Tags, Reading_Time, Article_Content, Word_Count, Sentiment, Compound_Score, Language)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT (Link) DO NOTHING
    """

    for _, row in merge_df.iterrows():
        cursor.execute(insert_query, (
            row['Link'], row['Title'], row['Time_Uploaded'], row['Authors'], row['Tags'],
            row['Reading_Time'], row['Article_Content'], row['Word_Count'],
            row['Sentiment'], row['Compound_Score'], row['Language']
        ))

    conn.commit()
    print("Data inserted successfully!")

except Exception as e:
    print(" Error inserting data:", e)

finally:
    if conn:
        cursor.close()
        conn.close()
