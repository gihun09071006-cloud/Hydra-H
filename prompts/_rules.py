"""Shared JSON-output rules for HYDRA prompt builders (pure data, no logic)."""

JSON_OUTPUT_RULES = (
    "Output requirements:\n"
    "- Respond with a single JSON object and nothing else.\n"
    "- Do NOT wrap the JSON in Markdown code fences (no ``` fences).\n"
    "- Do NOT include any commentary, explanation, or text before or after the JSON.\n"
    "- Use null or empty values for anything you cannot determine from the input; "
    "never invent facts.\n"
    "- Output only the final structured result. Do not include your reasoning."
)
