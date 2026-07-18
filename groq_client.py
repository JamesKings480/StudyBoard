# my automated tests for Studyboard, run from the project folder with:
#   python -m pytest test_studyboard.py -v
# it runs on an in memory database so it never touches my real studyboard.db,
# and the Groq call is swapped out with a fake so no test are ever outputted.

import json
from groq import Groq
from config import Config
# using the groq API 
GROQ_MODEL = 'openai/gpt-oss-120b'

# This is the format Groq has to answer in, it is strict on it literally cannot return anything else.
SUBTASK_SCHEMA = {
    'type': 'object',
    'properties': {
        'subtasks': {
            'type': 'array',
            'items': {
                'type': 'object',
                'properties': {
                    'title': {'type': 'string'},
                    'description': {'type': 'string'},
                    'days_before_due': {'type': 'integer'}
                },
                'required': ['title', 'description', 'days_before_due'],
                'additionalProperties': False
            }
        }
    },
    'required': ['subtasks'],
    'additionalProperties': False
}

# Builds the prompt, makes sure prompt is specific without it every
# assessment comes back with 'do some research'.
def build_subtask_prompt(assessment_type, days_available, task_text):
    prompt = 'You are a study planning assistant for HSC students. '
    prompt += 'Read the following assessment task notification and break it into '
    prompt += 'specific subtasks the student needs to complete. '
    prompt += 'Assessment type: ' + str(assessment_type) + ' '
    prompt += 'Days available: ' + str(days_available) + ' '
    prompt += 'Task notification: ' + str(task_text) + ' '
    prompt += 'Return JSON with a list of subtasks, each having a title, a description '
    prompt += 'and days_before_due. Give between 4 and 8 subtasks. days_before_due counts '
    prompt += 'backwards from the due date, so the first thing to do has the largest number. '
    prompt += 'The title is one short line naming the step, under 15 words. '
    prompt += 'The description is two or three sentences telling the student exactly how to '
    prompt += 'do that step for this particular task, referring to the actual requirements '
    prompt += 'and marking criteria in the notification above. '
    prompt += 'Every subtask must be specific to this task, not generic study advice.'
    return prompt


# Never trust the model even with a schema for security reasons. Drops blank titles, caps the length for
# the column, forces days to a non negative int.
def clean_subtasks(raw_subtasks):
    cleaned = []
    for item in raw_subtasks:
        title = str(item.get('title', '')).strip()
        if not title:
            continue
        try:
            days = int(item.get('days_before_due', 0))
        except (TypeError, ValueError):
            days = 0
        cleaned.append({
            'title': title[:200],
            'description': str(item.get('description', '')).strip(),
            'days_before_due': max(0, days)
        })
    return cleaned

# Asks Groq for a plan or returns None on any failure at all, which is the signal to
# app.py to use the fallback instead.
def generate_subtasks(assessment_type, days_available, task_text):
    if not Config.GROQ_API_KEY:
        print('GROQ ERROR: no API key loaded, check your .env')
        return None
    if not task_text or not task_text.strip():
        print('GROQ SKIPPED: no task notification text to work from')
        return None

    client = Groq(api_key=Config.GROQ_API_KEY)
    try:
        completion = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{
                'role': 'user',
                'content': build_subtask_prompt(assessment_type, days_available, task_text)
            }],
            reasoning_effort='low',
            max_completion_tokens=6000,
            response_format={
                'type': 'json_schema',
                'json_schema': {
                    'name': 'study_subtasks',
                    'strict': True,
                    'schema': SUBTASK_SCHEMA
                }
            }
        )
    except Exception as error:
        print('GROQ ERROR:', error)
        return None

    choice = completion.choices[0]
    if choice.finish_reason == 'length':
        print('GROQ ERROR: response was cut off, JSON will be incomplete')
        return None

    try:
        data = json.loads(choice.message.content)
    except (json.JSONDecodeError, TypeError) as error:
        print('GROQ PARSE ERROR:', error)
        return None

    return clean_subtasks(data.get('subtasks', [])) or None