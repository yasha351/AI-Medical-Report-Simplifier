from config.gemini import get_gemini_client
from services.llm.prompt_builder import build_summary_prompt

def summarize_report(parsed_data: dict) -> str:
    client = get_gemini_client()
    prompt = build_summary_prompt(parsed_data)
    response = client.models.generate_content(
        model="gemini-flash-latest",
        contents=prompt
    )
    return response.text


if __name__ == "__main__":
    fake_data = {"test": "LDL Cholesterol", "value": 165, "normal_range": "100-129"}
    print(summarize_report(fake_data))