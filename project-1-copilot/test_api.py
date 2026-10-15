from dotenv import load_dotenv
import os
from anthropic import Anthropic

load_dotenv()
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

response = client.messages.create(
    model="claude-sonnet-5",
    max_tokens=200,
    messages=[{"role": "user", "content": "Say hello and tell me one fact about revenue operations."}]
)

print(response.content[0].text)