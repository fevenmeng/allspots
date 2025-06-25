import  requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent #used to create fake user inorder for requests
import pandas as pd
import os

url = 'https://dev.to/latest'

ua=UserAgent()
userAgent= ua.random
headers= {'User_Agent': userAgent}
page = requests.get(url, headers = headers)
soup= BeautifulSoup(page.content,'html.parser')

blog_box = soup.find_all('div' ,'crayons-story')

links = [] 
titles = [] 
time_uploaded = []  
authors = []
tags = []
reading_times = []


for box in blog_box:
    #links
    if box.find('h2', class_ = 'crayons-story__title') is not None:
        link =  box.find('h2', class_ = 'crayons-story__title').a
        link = link['href']
        links.append(link)
    else:
        links.append('None')  
        
    #titles    
    if box.find('h2', class_ = 'crayons-story__title') is not None:
        title =  box.find('h2', class_ = 'crayons-story__title')
        titles.append(title.text.replace('\n','').strip())
    else:
        titles.append('None')          

    #time_uploaded 
    if box.find('time', attrs={'datetime': True}) is not None:
        time_upload =  box.find('time', attrs={'datetime': True})
        time_upload= time_upload['datetime']
        time_uploaded.append (time_upload)
    else:
        time_uploaded.append('None') 

    #authors 
    if box.find('a', class_ = 'crayons-story__secondary fw-medium m:hidden') is not None:
        author =  box.find('a', class_ = 'crayons-story__secondary fw-medium m:hidden')
        authors.append(author.text.replace('\n','').strip())
    else:
        authors.append('None')  


    #tags  
    if box.find('div', class_ = 'crayons-story__tags') is not None:
        tag =  box.find('div', class_ = 'crayons-story__tags')
        tags.append(tag.text.replace('\n',' ').strip())
    else:
        tags.append('None')
        
 #reading_time  
    if box.find('div', class_ = 'crayons-story__save') is not None:
        reading_time  =  box.find('div', class_ = 'crayons-story__save')
        reading_times.append(reading_time.text.replace('\n',' ').strip())
    else:
        reading_times.append('None')  
  
  
df = pd.DataFrame(
    {
    'Link' : links,
    'Title' : titles,
    'Time_Uploaded' : time_uploaded ,
    'Authors' : authors,
    'Tags' : tags,
    'Reading_Time' : reading_times
    }
) 

df= df[ df['Link'] != 'None']


##Second_url = 'https://dev.to/sejdi_gashi/live-and-online-our-food-waste-reduction-platform-is-almost-ready-5dfi'
article = []
article_link = []

def get_full_content (Second_url):
    ua=UserAgent()
    userAgent= ua.random
    headers= {'User_Agent': userAgent}
    page = requests.get(Second_url, headers = headers)
    soup= BeautifulSoup(page.content,'html.parser')
    print(Second_url)

    content = soup.find ('div',class_='crayons-article__main')
    paragrphs = content.find_all('p')

    contents = []
    for i in paragrphs:
        contents.append(i.text.replace('\n',' '))
    
    string  = ' '.join(contents)
    article.append (string)
    article_link.append(Second_url)

for i in df.Link:
    get_full_content(i)
article_df = pd.DataFrame(
      {
      'Article_Content' : article,
      'Link' : article_link
      }
    )

#merge 2 dataframe
merge_df = pd.merge(df, article_df, on = 'Link', how='inner')

from nltk.corpus import stopwords
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer



# Download required datasets (without 'punket_tab')
nltk.download('stopwords')
nltk.download('punkt')
nltk.download('wordnet')
nltk.download('vader_lexicon')
#nltk.download('punket_tab')

for resource in ['punkt', 'stopwords', 'wordnet', 'vader_lexicon']:
    try:
        nltk.data.find(f'tokenizers/{resource}' if resource == 'punkt' else f'corpora/{resource}')
    except LookupError:
        nltk.download(resource)

def count_words_without_stopwords(text):
    if isinstance(text,(str,bytes)):
        words = nltk.word_tokenize(str(text))
        stop_words = set(stopwords.words('english'))
        filtered_words = [word for word in words if word.lower() not in stop_words ]
        return  len(filtered_words)  
    else:
        0
        
merge_df ['Word_Count']  = merge_df ['Article_Content'].apply(count_words_without_stopwords)  

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import pandas as pd
sid = SentimentIntensityAnalyzer()

def get_sentiment(row):
    
    sentiment_scores = sid.polarity_scores(merge_df.Article_Content[20])
    compound_score = sentiment_scores['compound']

    if compound_score >= 0.05:
      sentiment = 'Positive'
    elif compound_score <=  -0.05:
      sentiment = 'Negative'
    else:
      sentiment = 'Neutral' 
     
    return sentiment , compound_score   
         
#df[['Sentiment' , 'Compound_Score']] = df['Article_Content'].astype(str).apply(lambda x: pd.Series(get_sentiment(x)))
merge_df[['Sentiment', 'Compound_Score']] = merge_df['Article_Content'].astype(str).apply( lambda x: pd.Series(get_sentiment(x)))   

import pandas as pd 
import langid
import pycountry

def detect_language(text) :
    # conver NAN to an empty string
    text = str(text) if pd.notna(text) else ''
    
    # use langid to detect the language
    lang, confidence = langid.classify(text)
    return lang
merge_df['Language'] =merge_df['Article_Content'].apply(detect_language)
merge_df['Language']=merge_df['Language'].map(lambda code: pycountry.languages.get(alpha_2=code).name if pycountry.languages.get(alpha_2=code) else code)

#merge_df = merge_df[merge_df['Language'] == 'English']
merge_df['Reading_Time'] = merge_df['Reading_Time'].astype(str).str.replace(' min read', '', regex=False).str.strip().replace('', '0').astype(int)

    
import psycopg2

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
                                                
