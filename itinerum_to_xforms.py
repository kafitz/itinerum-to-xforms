#!/usr/bin/eny python
# Kyle Fitzsimmons, 2020
import psycopg2
import psycopg2.extras

import config


## Fetch Itinerum survey from Postgres database
conn = psycopg2.connect(**config.DB)
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
survey_id = 261

# get survey metadata record for display language attribute
query = f'SELECT language FROM surveys WHERE id={survey_id};'
cur.execute(query)
survey_language = cur.fetchone()['language']
survey_language

# retrieve all questions for a survey from Itinerum database
query = f'SELECT * FROM survey_questions WHERE survey_id={survey_id} ORDER BY question_num ASC;'
cur.execute(query)
questions = [dict(q) for q in cur.fetchall()]
len(questions)

# retrieve all question choices for a list of questions from Itinerum database
question_ids = tuple([q['id'] for q in questions])
cur.execute('SELECT * FROM survey_question_choices WHERE question_id IN %s;', (question_ids,))
choices = [dict(c) for c in cur.fetchall()]
len(choices)

# merge questions and choices into list of dicts object

for q in questions:
    for c in choices:
        if c['question_id'] == q['id']:
            q.setdefault('choices', []).append(c)


### PART 2
