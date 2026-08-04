from openai import OpenAI
import json

from config import OPENAI_API_KEY, MODEL


client = OpenAI(
    api_key=OPENAI_API_KEY
)


def analyze_post(text):

    prompt = f"""
You are an international security analyst.

Analyze this Donald Trump Truth Social post.

Determine whether it relates to international security.

International security topics include:
- NATO
- Ukraine
- Russia
- China
- Taiwan
- Iran
- Israel
- Middle East conflicts
- Military operations
- Nuclear weapons
- Defense policy
- Foreign alliances
- Sanctions
- Terrorism
- Cybersecurity
- Global diplomacy


Post:

{text}


Return ONLY valid JSON:

{{
"relevant": true or false,
"topic": "",
"countries": [],
"organizations": [],
"summary": "",
"importance": "Low, Medium, or High",
"security_reason": ""
}}

"""


    response = client.chat.completions.create(

        model=MODEL,

        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]

    )


    result = response.choices[0].message.content


    return json.loads(result)
