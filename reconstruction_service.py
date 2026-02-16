import json
import re
from deviation_service import get_client, get_model_name


def clean_llm_json(raw_output: str):
    cleaned = re.sub(r"```json|```", "", raw_output).strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return {
            "expert_optimized_prompt": cleaned,
            "improvements_made": "Model did not return valid JSON."
        }


def generate_expert_prompt(summary_text: str, metrics_json: dict, deviation_insights: dict, config=None):
    
    system_instruction = f"""
Act as an expert in Conversation Analysis and Prompt Engineering.
Task: Analyze the provided conversation and generate a comprehensive report focusing on deviation, intent, and prompt optimization.

Context:
- The user is unhappy with the model's performance and wants to know *how* it deviated.
- You have access to a summary and specific deviation metrics (0-1 score, where 1 is highly deviated).

Output Structure (Must follow exactly):

## 1. Deviation Analysis
- Explain **how** the model response deviated from the user's prompt.
- Compare the User's Intent vs. the Model's Output.
- Highlight specific areas where the model failed to meet expectations (e.g., tone, format, content depth).

## 2. Vector Similarity Analysis
- Analyze the provided metrics.
- Interpret the 'Semantic Alignment' and 'Expectation Alignment' scores.
- Explain what these numbers mean for this specific conversation (e.g., "A low semantic score of X indicates...").

## 3. User Intent & Expectation
- **Actual Intent**: Clearly state what the user *actually* wanted.
- **Constraints**: explicit "Don't Deviate Into" points (what the model should avoid).

## 4. Reconstructed Prompt (For a New Session)
- Provide a single, comprehensive prompt that the user can copy-paste into a new chat to get the exact result they wanted.
- Include:
    - **Role**: Expert persona.
    - **Task**: Clear instruction.
    - **Context**: Background info.
    - **Constraints**: Negative constraints to prevent previous deviation.
    - **Output Format**: Precise requirements.

Rules:
- Be critical and analytical.
- Use the provided summary and metrics data.
- Do NOT just summarize the conversation again; analyze the *failure* or *success* of the interaction.
"""


    user_input = f"""
Conversation Summary:
{summary_text}

Deviation Metrics:
{json.dumps(metrics_json, indent=2)}
"""

    client = get_client(config)
    model = get_model_name(config)

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": user_input}
        ],
        temperature=0.1
    )

    return response.choices[0].message.content.strip()

