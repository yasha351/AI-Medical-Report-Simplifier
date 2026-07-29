def build_summary_prompt(parsed_data: dict) -> str:
    return (
        "You are a medical report simplifier. Explain this prescription in plain, "
        "simple language for someone with no medical background. "
        "Do not diagnose. Suggest they consult a doctor. "
        "Return plain text only. Do not use markdown symbols like #, *, or bullet formatting.\n\n"
        f"Prescription data: {parsed_data}"
    )