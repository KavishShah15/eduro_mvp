# backend/gemini_interaction.py

import google.generativeai as genai
import os
import json
import re
import logging
# from google.generativeai import types
# from google.generativeai.types import Tool, GenerateContentConfig, GoogleSearch

# Configure logging for better debugging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Configuration ---
try:
    API_KEY = os.environ["GOOGLE_API_KEY"]
    genai.configure(api_key=API_KEY)
    logging.info("Google API Key configured successfully.")
except KeyError:
    logging.error("CRITICAL: GOOGLE_API_KEY environment variable not set.")
    logging.error("Please set it before running the application. Example: export GOOGLE_API_KEY='your_api_key_here'")
    # In a real app, you might want to raise an exception or sys.exit() here
    # For this prototype, we'll let it proceed but API calls will fail.
    # Consider adding: raise SystemExit("GOOGLE_API_KEY not set.")

# --- Model Initialization ---
# Use the specific model you mentioned or a suitable alternative.
# "gemini-1.5-flash-latest" is a good general-purpose and fast model.
MODEL_NAME = "gemini-2.0-flash" # Adjusted from gemini-2.0-flash as 1.5-flash is widely available

# Safety settings can be adjusted. These are fairly standard.
SAFETY_SETTINGS = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
]

# Generation config for MCQs - aiming for JSON output
mcq_generation_config = genai.types.GenerationConfig(
    # response_mime_type="application/json", # Enable if your model version strongly supports it
    temperature=0.6, # Slightly lower for more structured output
    top_p=0.95,
    top_k=40
)

# Generation config for general text (explanations, etc.)
text_generation_config = genai.types.GenerationConfig(
    temperature=0.7,
    top_p=0.95,
    top_k=40
)

# URL_CONTEXT_TOOL = Tool(url_context = types.UrlContext)
# url_grounding_config=GenerateContentConfig(
#         tools=[URL_CONTEXT_TOOL],
#         response_modalities=["TEXT"],
#     )
# Initialize the model instance
# Check if API_KEY was actually found before creating the model
if 'API_KEY' in globals() and API_KEY:
    try:
        model = genai.GenerativeModel(
            MODEL_NAME,
            safety_settings=SAFETY_SETTINGS
            # Default generation_config can be set here if desired for all calls
        )
        logging.info(f"Gemini model '{MODEL_NAME}' initialized.")
    except Exception as e:
        logging.error(f"Failed to initialize Gemini model: {e}")
        model = None # Ensure model is None if initialization fails
else:
    model = None
    logging.error("Gemini model not initialized because API key is missing.")


def _clean_json_from_text(text_response):
    """
    Attempts to extract a JSON array string from a larger text response
    that might include markdown backticks.
    """
    match = re.search(r"```json\s*(\[.*\])\s*```", text_response, re.DOTALL)
    if match:
        return match.group(1)
    # Fallback: if no markdown, assume the whole string might be JSON (or part of it)
    # Try to find the start of a JSON array or object
    json_start_match = re.search(r"(\[|\{)", text_response)
    if json_start_match:
        return text_response[json_start_match.start():]
    return text_response # Return original if no clear JSON structure found

def generate_mcqs(topic, num_questions=3):
    if not model:
        logging.error("generate_mcqs: Model not initialized.")
        return []

    logging.info(f"[GEMINI API] Attempting to generate {num_questions} MCQs for topic: {topic}")
    prompt = f"""
    You are an AI assistant tasked with creating educational multiple-choice questions (MCQs).
    Generate exactly {num_questions} MCQs for the topic: "{topic}".

    For each question, you MUST provide:
    1.  A unique "id" string (e.g., "q1", "q2", ... "q{num_questions}").
    2.  The "question_text" (string).
    3.  A list of exactly 4 "options" (list of strings).
    4.  The "correct_answer" (string, which MUST be one of the provided options).

    Your entire response MUST be a single, valid JSON array of objects. Each object represents one MCQ.
    Do NOT include any explanatory text or markdown before or after the JSON array.

    Example of the required JSON format for ONE question:
    {{
        "id": "q1",
        "question_text": "What is 2 + 2?",
        "options": ["3", "4", "5", "6"],
        "correct_answer": "4"
    }}

    Ensure the JSON is well-formed and directly parsable.
    """
    try:
        # If your model reliably supports response_mime_type="application/json"
        # response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
        # Otherwise, generate text and parse
        response = model.generate_content(prompt, generation_config=mcq_generation_config,  ) #config=url_grounding_config

        logging.debug(f"[GEMINI RAW RESPONSE for MCQs]:\n{response.text}\n")

        # Attempt to clean and parse JSON
        json_text = _clean_json_from_text(response.text)
        questions_data = json.loads(json_text)

        # Basic validation
        if not isinstance(questions_data, list) or len(questions_data) != num_questions:
            logging.warning(f"MCQ generation: Expected {num_questions} questions in a list, got something else. Data: {questions_data}")
            # Attempt to filter or fix if possible, or return error
            if isinstance(questions_data, list): # If it's a list but wrong number
                 logging.warning(f"Returning only {len(questions_data)} questions if valid.")
            else: # Not a list at all
                raise ValueError(f"Response was not a JSON list as expected. Raw: {response.text}")


        valid_questions = []
        for i, q in enumerate(questions_data):
            if not all(key in q for key in ["id", "question_text", "options", "correct_answer"]):
                logging.warning(f"MCQ {i+1} is missing required keys: {q}")
                continue
            if not isinstance(q.get("options"), list) or len(q["options"]) != 4:
                logging.warning(f"MCQ {q.get('id', i+1)} has invalid options: {q.get('options')}")
                continue
            if q.get("correct_answer") not in q.get("options", []):
                logging.warning(f"MCQ {q.get('id', i+1)}: Correct answer '{q.get('correct_answer')}' not in options {q.get('options')}. Trying to fix or skipping.")
                # You might try to pick the first option as a default, or skip this question
                continue # Skip malformed question for now
            valid_questions.append(q)
        
        if not valid_questions:
            logging.error("No valid MCQs could be parsed from Gemini's response.")
            return []
            
        logging.info(f"Successfully generated and parsed {len(valid_questions)} MCQs.")
        return valid_questions

    except json.JSONDecodeError as e:
        logging.error(f"Failed to decode JSON from Gemini for MCQs: {e}. Response text: {response.text if 'response' in locals() else 'No response object'}")
        return []
    except (AttributeError, ValueError, TypeError) as e:
        logging.error(f"Error processing Gemini response for MCQs: {e}. Response text: {response.text if 'response' in locals() else 'No response object'}")
        return []
    except Exception as e: # Catch other Gemini API errors (rate limits, content filtering, etc.)
        logging.error(f"An unexpected error occurred with Gemini API for MCQs: {e}")
        if hasattr(response, 'prompt_feedback') and response.prompt_feedback:
             logging.error(f"Prompt Feedback: {response.prompt_feedback}")
        return []


def generate_text_content(prompt_template, topic, section_title, content_type_log_name):
    if not model:
        logging.error(f"generate_{content_type_log_name}: Model not initialized.")
        return f"[Error: AI Model not available for {content_type_log_name}]"

    logging.info(f"[GEMINI API] Generating {content_type_log_name} for: {topic} - {section_title}")
    prompt = prompt_template.format(topic=topic, section_title=section_title)

    try:
        response = model.generate_content(prompt, generation_config=text_generation_config) #config=url_grounding_config
        if response.text:
            logging.info(f"Successfully generated {content_type_log_name}.")
            return response.text.strip()
        else:
            # Check for blocking reasons if response.text is empty
            if hasattr(response, 'prompt_feedback') and response.prompt_feedback:
                logging.warning(f"{content_type_log_name} generation might be blocked. Feedback: {response.prompt_feedback}")
                if response.prompt_feedback.block_reason:
                    return f"[AI content generation blocked: {response.prompt_feedback.block_reason_message or response.prompt_feedback.block_reason}]"
            logging.warning(f"Gemini returned an empty response for {content_type_log_name}.")
            return f"[AI Error: No content generated for {content_type_log_name}]"

    except Exception as e:
        logging.error(f"An unexpected error occurred with Gemini API for {content_type_log_name}: {e}")
        if hasattr(response, 'prompt_feedback') and response.prompt_feedback:
             logging.error(f"Prompt Feedback: {response.prompt_feedback}")
        return f"[AI Error: Could not generate {content_type_log_name} - {e}]"

def generate_explanation(topic, section_title):
    topic_url = "https://ncert.nic.in/textbook/pdf/jemh104.pdf"
    prompt_template = """
    You are an AI Educational Tutor.
    Provide a clear and concise explanation for the section titled "{section_title}" within the broader topic of "{topic}".
    The explanation should be suitable for a beginner student.
    Focus on key concepts, definitions, and the importance of this section.
    Keep the language simple and engaging.
    Do not include any preamble like "Okay, here's an explanation..." or "Sure, I can help with that...".
    Just provide the explanation text directly.
    """
    return generate_text_content(prompt_template, topic, section_title, "explanation")

def generate_solved_example(topic, section_title):
    topic_url = "https://ncert.nic.in/textbook/pdf/jemh104.pdf"
    prompt_template = """
    You are an AI Educational Tutor.
    Create a relevant solved example for the section titled "{section_title}" within the topic of "{topic}".
    The example should clearly demonstrate the application of concepts from this section.
    Present the problem, then show the step-by-step solution.
    Make it easy to follow for a student learning this for the first time.
    Do not include any preamble like "Okay, here's a solved example..." or "Sure, I can help with that...".
    Begin the problem statement with "Problem:" and the solution with "Solution:".
    """#you can use the {topic_url} to get the context of the topic and the section title.
    return generate_text_content(prompt_template, topic, section_title, "solved example")

def generate_problem(topic, section_title):
    topic_url = "https://ncert.nic.in/textbook/pdf/jemh104.pdf"
    prompt_template = f"""
    You are an AI assistant tasked with creating educational multiple-choice questions (MCQs).
    Generate exactly 1 MCQ for the topic: "{topic}" and the section: "{section_title}".

    For each question, you MUST provide:
    1.  A unique "id" string (e.g., "q1").
    2.  The "question_text" (string).
    3.  A list of exactly 4 "options" (list of strings).
    4.  The "correct_answer" (string, which MUST be one of the provided options).

    Your entire response MUST be a single, valid JSON array of objects. Each object represents one MCQ.
    Do NOT include any explanatory text or markdown before or after the JSON array.

    Example of the required JSON format for ONE question:
    {{
        "id": "q1",
        "question_text": "What is 2 + 2?",
        "options": ["3", "4", "5", "6"],
        "correct_answer": "4"
    }}

    Ensure the JSON is well-formed and directly parsable.
    """
    try:
        response = model.generate_content(prompt_template, generation_config=text_generation_config)
        logging.debug(f"[GEMINI RAW RESPONSE for Problem]:\n{response.text}\n")
        json_text = _clean_json_from_text(response.text)
        questions_data = json.loads(json_text)
        # Should be a list with one MCQ
        if not isinstance(questions_data, list) or len(questions_data) != 1:
            logging.warning(f"Problem generation: Expected 1 question in a list, got: {questions_data}")
            return None
        q = questions_data[0]
        if not all(key in q for key in ["id", "question_text", "options", "correct_answer"]):
            logging.warning(f"Generated problem is missing required keys: {q}")
            return None
        if not isinstance(q.get("options"), list) or len(q["options"]) != 4:
            logging.warning(f"Generated problem has invalid options: {q.get('options')}")
            return None
        if q.get("correct_answer") not in q.get("options", []):
            logging.warning(f"Generated problem: Correct answer '{q.get('correct_answer')}' not in options {q.get('options')}")
            return None
        logging.info(f"Successfully generated and parsed MCQ problem for section.")

        return q
    except Exception as e:
        logging.error(f"Error generating or parsing MCQ problem: {e}")
        if 'response' in locals() and hasattr(response, 'prompt_feedback') and response.prompt_feedback:
            logging.error(f"Prompt Feedback: {response.prompt_feedback}")
        return None

# Optional: If you want to implement evaluation of free-text answers later
# def evaluate_user_problem_answer(topic, section_title, problem_statement, user_answer):
#     logging.info(f"[GEMINI API] Evaluating user answer for: {topic} - {section_title}")
#     prompt = f"""
#     You are an AI Educational Tutor.
#     A student was given the following problem related to the section "{section_title}" from the topic "{topic}":
#     Problem: "{problem_statement}"
#     The student's answer is: "{user_answer}"

#     Evaluate the student's answer.
#     Provide feedback:
#     1. State if the answer is correct, partially correct, or incorrect.
#     2. If incorrect or partially correct, briefly explain the mistake or guide them towards the correct solution.
#     Keep the feedback encouraging and constructive.
#     Do not include any preamble. Just provide the feedback.
#     """
#     # This would use generate_text_content or a similar structure
#     # return generate_text_content(prompt, topic, section_title, "answer evaluation") # Needs adjustment to fit template
#     pass