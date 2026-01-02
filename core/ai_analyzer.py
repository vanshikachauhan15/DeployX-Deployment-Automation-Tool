import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def ai_explain_repo(analysis, repo_name):
    prompt = f"""
You are a senior DevOps engineer.

Project: {repo_name}

Issues detected:
{analysis['issues']}

Explain clearly:
1. Why auto-run failed
2. What user must configure
3. Is database / Docker required?
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )

    return response.choices[0].message.content
