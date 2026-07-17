def build_summary_prompt(parsed_data: dict) -> str:
    return (
        "You are a medical report simplifier. Explain this report in plain, "
        "simple language for someone with no medical background. Flag any "
        "abnormal values clearly. Do not diagnose. Suggest they consult a doctor.\n\n"
        f"Report data: {parsed_data}"
    )