def process_survey_for_llm(survey_dict: dict) -> str:
    """
    Convert the questionnaire dictionary into a format that can be processed question by question by the LLM, using English prompts.
    """
    prompt = f"""Survey Title: {survey_dict['title']}
Survey Description: {survey_dict['description']}

Please answer each question in the following format:

"""

    question_count = 1
    for page in survey_dict["pages"]:
        for question in page["elements"]:
            prompt += f"Question {question_count}: {question['title']}\n"

            # Generate different prompts based on the types of questions
            if question["type"] == "radiogroup":
                prompt += "Options: " + ", ".join(question["choices"]) + "\n"
                prompt += "Please select ONE option\n"

            elif question["type"] == "checkbox":
                prompt += "Options: " + ", ".join(question["choices"]) + "\n"
                prompt += "You can select MULTIPLE options\n"

            elif question["type"] == "rating":
                prompt += f"Rating range: {question.get('min_rating', 1)} - {question.get('max_rating', 5)}\n"
                prompt += "Please provide a rating within the range\n"

            elif question["type"] == "matrix":
                prompt += "Rows: " + ", ".join(question["rows"]) + "\n"
                prompt += "Columns: " + ", ".join(question["columns"]) + "\n"
                prompt += "Please select ONE column option for EACH row\n"

            elif question["type"] == "text":
                prompt += "Please provide a text response\n"

            elif question["type"] == "boolean":
                prompt += "Options: Yes, No\n"
                prompt += "Please select either Yes or No\n"

            prompt += "\nAnswer: [Your response here]\n\n---\n\n"
            question_count += 1

    # Add a summary prompt
    prompt += """Please ensure:
1. All required questions are answered
2. Responses match the question type requirements
3. Answers are clear and specific

Format your responses exactly as requested above."""

    return prompt


SURVEY_SENDER_UUID = "none"
