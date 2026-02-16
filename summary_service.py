from deviation_service import get_client, get_model_name

def build_conversation_text(chat: dict) -> str:
    text = ""
    for msg in chat["conversation"]:
        text += f"{msg['role'].upper()}:\n{msg['content']}\n\n"
    return text.strip()


def summarize_transcript(conversation_text: str, config=None) -> str:

    system_prompt = """
You are a strict transcript summarizer.

Rules:
- Analyze the *flow* of the conversation.
- Identify the User's core objective and any shifts in intent.
- Highlight where the Model's responses might have missed the mark.
- Concise: Maximum 300 words.
- Format: "User wanted X. Model provided Y. User corrected with Z..."
"""
    client = get_client(config)
    model = get_model_name(config)

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": conversation_text}
        ],
        temperature=0.1
    )

    return response.choices[0].message.content.strip()

