import json
from groq import Groq
from config import Config

GROQ_MODEL = 'openai/gpt-oss-120b'

SUBTASK_SCHEMA = {
    'type': 'object',
    'properties': {
        'subtasks': {
            'type': 'array',
            'items': {
                'type': 'object',
                'properties': {
                    'title': {'type': 'string'},
                    'days_before_due': {'type': 'integer'}
                },
                'required': ['title', 'days_before_due'],
                'additionalProperties': False
            }
        }
    },
    'required': ['subtasks'],
    'additionalProperties': False
}


def build_subtask_prompt(assessment_type, days_available, task_text):
    prompt = 'You are a study planning assistant for HSC students. '
    prompt += 'Read the following assessment task notification and break it into '
    prompt += 'specific subtasks the student needs to complete. '
    prompt += 'Assessment type: ' + str(assessment_type) + ' '
    prompt += 'Days available: ' + str(days_available) + ' '
    prompt += 'Task notification: ' + str(task_text) + ' '
    prompt += 'Return JSON with a list of subtasks, each having a title and days_before_due. '
    prompt += 'Give between 4 and 8 subtasks. days_before_due counts backwards from the '
    prompt += 'due date, so the first thing to do has the largest number. '
    prompt += 'Every title must be a specific action drawn from this task notification, '
    prompt += 'not generic study advice. Keep each title under 15 words.'
    return prompt


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
        cleaned.append({'title': title[:200], 'days_before_due': max(0, days)})
    return cleaned


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
            max_completion_tokens=4000,
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