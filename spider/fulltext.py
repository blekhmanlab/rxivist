import pickle
import re
import time

import nltk
from nltk.stem.snowball import SnowballStemmer
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import linear_kernel

cats = ['animal-behavior-and-cognition','biochemistry','bioengineering','bioinformatics','biophysics','cancer-biology','cell-biology','clinical-trials','developmental-biology','ecology','epidemiology','evolutionary-biology','genetics','genomics','immunology','microbiology','molecular-biology','neuroscience','paleontology','pathology','pharmacology-and-toxicology','physiology','plant-biology','scientific-communication-and-education','synthetic-biology','systems-biology','zoology']

def get_more_fulltext(spider):
  with spider.connection.db.cursor() as cursor:
    cursor.execute("""
      SELECT id
      FROM prod.fulltext
    """)
    skip = [x[0] for x in cursor]
  to_eval = {}
  with spider.connection.db.cursor() as cursor:
    cursor.execute("""
      SELECT id, url
      FROM prod.articles
      WHERE new_url IS NULL
      OR new_url='1'
      ORDER BY posted
    """)
    for x in cursor:
      if x[0] not in skip:
        to_eval[x[0]] = x[1]
  done = 0
  for id, url in to_eval.items():
    time.sleep(1)
    get_article_fulltext(spider, id, url)
    done += 1
    if done >= 500:
      break

def get_article_fulltext(spider, id, url):
  try:
    resp = spider.session.get(f"{url}.full.txt")
  except Exception as e:
    spider.log.record(f"  Error requesting article text for {id}. Moving on: {e}", "error")
    return None
  content = resp.content.decode('utf-8')

  if len(content) < 6500 or resp.status_code != 200:
    spider.log.record(f"{url}.full.txt")
    # spider.log.record(f'    Fulltext is only {len(content)} characters; assuming it\'s not processed yet.', 'info')
    content = None
    # return
  else:
    print(f'{id} !!!!\n   It is {len(content)} long')
    content = clean_text(content)

  with spider.connection.db.cursor() as cursor:
    cursor.execute("INSERT INTO prod.fulltext VALUES (%s, %s);", (id, content))

def clean_text(content):
  # Chop off the extraneous stuff at the end (references, etc.)
  cutoff = content.find('## Footnotes')
  if cutoff > -1:
    content = content[0:cutoff]
  content = re.sub(r'[\*\+\=\.\,\?\#]', '', content)
  content = re.sub(r'[\n\s]+', ' ', content)

  # create stems of all the words
  # TODO: Look into lemmatizing instead?
  stemmer = SnowballStemmer('english', ignore_stopwords=True)
  content = ' '.join([stemmer.stem(x) for x in content.split(' ')])
  return content

def get_abstracts(spider):
  entries = []
  print("Getting abstracts")
  for cat in cats:
    print(f"Fetching abstracts for {cat}")
    with spider.connection.db.cursor() as cursor:
      cursor.execute("""
        SELECT collection, abstract
        FROM prod.articles
        WHERE collection=%s
          AND abstract IS NOT NULL
        LIMIT 100;
      """, (cat,))
      for result in cursor:
        entries.append((result[0], clean_text(result[1])))
  return entries

def analyze(spider, modelfile=None, save=False):
  # create the transform
  vectorizer = CountVectorizer(
    ngram_range=(1,2), # include two-word phrases
    min_df = 3 # throw away phrases that show up in < 3 papers
  )
  if modelfile is None:
    nltk.download('stopwords')
    content = get_abstracts(spider)
    print("ANALYZING ABSTRACTS!")

    print("Encoding...")
    X = vectorizer.fit_transform([x[1] for x in content]).toarray() # just the text
    Y = np.array([cats.index(x[0]) for x in content]) # just the labels

    clf = RandomForestClassifier()
    print("Fitting...")
    clf.fit(X, Y)
    if save:
      print("Saving model...")
      with open('model.pickle', 'wb') as f:
        pickle.dump(clf, f, pickle.HIGHEST_PROTOCOL)
      with open('modelx.pickle', 'wb') as f:
        pickle.dump(vectorizer, f, pickle.HIGHEST_PROTOCOL) # just the text
  else:
    print(f"Loading model from {modelfile}")
    with open(f'{modelfile}.pickle', 'rb') as f:
      clf = pickle.load(f)
    with open(f'{modelfile}x.pickle', 'rb') as f:
      vectorizer = pickle.load(f)

  print('Building kernel...')
  kernel = linear_kernel(X)
  print('Saving kernel...')
  save_matrix(kernel, Y)
  print(f'k is {len(kernel)} AND {len(kernel[0])}')

  print("Ready.")
  while True:
    q = input('Enter abstract: ')
    if q == 'x':
      break
    answer = clf.predict_proba(vectorizer.transform([q]).toarray())
    for i in range(len(answer[0])):
      if answer[0][i] > 0:
        print(f'{cats[i]}: {answer[0][i]}')

def save_matrix(matrix,labels):
  print(labels)
  print(len(labels))
  print('------\n\n\n')
  with open('matrix.csv', 'w') as f:
    toprow = 'category'
    for x in labels:
      toprow += f',{str(x)}'
    toprow += '\n'
    f.write(toprow)
    for i, row in enumerate(matrix):
      print(i)
      towrite = cats[labels[i]]
      for entry in row:
        towrite += f',{entry}'
      towrite += '\n'
      f.write(towrite)