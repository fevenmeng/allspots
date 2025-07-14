import pandas as pd
import psycopg
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
from wordcloud import WordCloud
from dotenv import load_dotenv
from nltk.corpus import stopwords
import nltk
import os

nltk.download('stopwords', quiet=True)

load_dotenv()

<<<<<<< HEAD
conn_str = os.environ['CONNECTION_STRING']



conn = psycopg2.connect(conn_str)
=======
import streamlit as st

conn_str = st.secrets["CONNECTION_STRING"]

conn = psycopg.connect(conn_str)
>>>>>>> 883bde2 (this)
query = "SELECT * FROM articles;"
data = pd.read_sql(query, conn)
conn.close()

data.columns = ['_'.join(word.capitalize() for word in col.split('_')) for col in data.columns]
df = data
df['Time_Uploaded'] = pd.to_datetime(df['Time_Uploaded'], errors='coerce')

st.set_page_config(page_title="Dev.to Dashboard", layout="wide")

st.title("🚀 Article Dashboard ")

# KPIs
col1, col2, col3 = st.columns(3)
col1.metric("Total Articles", len(df))
col2.metric("Avg. Word Count", f"{df['Word_Count'].mean():.0f}")
col3.metric("Positive Sentiment %", f"{(df['Sentiment'] == 'Positive').mean()*100:.1f}%")

# Articles Over Time & Reading Time Distribution side by side
articles_per_day = df.groupby(df['Time_Uploaded'].dt.date).size()

fig, axs = plt.subplots(1, 2, figsize=(12, 3))

axs[0].plot(articles_per_day.index, articles_per_day.values, marker='o')
axs[0].set_title("Articles Over Time", fontsize=10)
axs[0].set_xlabel("Date", fontsize=8)
axs[0].set_ylabel("Count", fontsize=8)
axs[0].tick_params(axis='x', rotation=45, labelsize=7)
axs[0].tick_params(axis='y', labelsize=7)

axs[1].hist(df['Reading_Time'].dropna(), bins=10, color='purple', alpha=0.7)
axs[1].set_title("Reading Time Distribution (minutes)", fontsize=10)
axs[1].set_xlabel("Reading Time (min)", fontsize=8)
axs[1].set_ylabel("Number of Articles", fontsize=8)
axs[1].tick_params(axis='both', labelsize=7)

plt.tight_layout()
st.pyplot(fig)

# Sentiment and Word Count section
sentiment_counts = df['Sentiment'].value_counts()

fig2, axs2 = plt.subplots(1, 2, figsize=(12, 3))

colors = ['green', 'gray', 'red']
axs2[0].pie(sentiment_counts.values, labels=sentiment_counts.index,
            autopct='%1.1f%%', startangle=140, colors=colors, textprops={'fontsize':7})
axs2[0].set_title("Sentiment Breakdown", fontsize=10)

sns.boxplot(data=df, x='Sentiment', y='Word_Count',
            palette={'Positive':'green', 'Negative':'red', 'Neutral':'gray'}, ax=axs2[1])
axs2[1].set_title("Word Count by Sentiment", fontsize=10)
axs2[1].tick_params(axis='both', labelsize=7)

plt.tight_layout()
st.pyplot(fig2)

# Word cloud full width
st.subheader("🏷️ Common Tags Word Cloud")
text = ' '.join(df['Tags'].dropna())
wordcloud = WordCloud(width=800, height=300, background_color='white').generate(text)
fig_wc, ax_wc = plt.subplots(figsize=(8, 3))
ax_wc.imshow(wordcloud, interpolation='bilinear')
ax_wc.axis('off')
st.pyplot(fig_wc)



#on the terminal run - stramlit run app.py  ->it will open default browser at http://localhost:8501/
