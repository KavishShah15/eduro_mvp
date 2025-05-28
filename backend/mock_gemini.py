import random
import google.generativeai as gemini



def generate_mcqs_mock(topic, num_questions=3):
    """Mocks Gemini generating MCQ questions."""
    print(f"[MOCK GEMINI] Generating {num_questions} MCQs for topic: {topic}")
    questions = []
    for i in range(num_questions):
        options = [f"Option {chr(65+j)} for Q{i+1}" for j in range(4)]
        correct_option_index = random.randint(0, 3)
        questions.append({
            "id": f"q{i+1}",
            "question_text": f"This is mock question {i+1} about {topic}. What is the answer?",
            "options": options,
            "correct_answer": options[correct_option_index] # Store correct answer text for easier checking
        })
    return questions

def generate_explanation_mock(topic, section_title):
    """Mocks Gemini generating an explanation for a section."""
    print(f"[MOCK GEMINI] Generating explanation for: {topic} - {section_title}")
    return (f"This is a detailed mock explanation about '{section_title}' within the topic of '{topic}'. "
            "It would cover key concepts, definitions, and importance. "
            "Lorem ipsum dolor sit amet, consectetur adipiscing elit.")

def generate_solved_example_mock(topic, section_title):
    """Mocks Gemini generating a solved example for a section."""
    print(f"[MOCK GEMINI] Generating solved example for: {topic} - {section_title}")
    return (f"Here's a mock solved example for '{section_title}' ({topic}):\n"
            "Problem: If x + 5 = 10, what is x?\n"
            "Solution: \n"
            "1. Subtract 5 from both sides: x + 5 - 5 = 10 - 5\n"
            "2. Simplify: x = 5\n"
            "This demonstrates how to solve the concept.")

def generate_problem_mock(topic, section_title):
    """Mocks Gemini generating a problem for the user to solve."""
    print(f"[MOCK GEMINI] Generating problem for: {topic} - {section_title}")
    return (f"Now, try this problem related to '{section_title}' ({topic}):\n"
            "Problem: If 2y - 3 = 7, what is y? Type your answer.")

# You might add a mock for evaluating user's free-text answer to a problem later
# def evaluate_user_problem_answer_mock(problem, user_answer):
#     print(f"[MOCK GEMINI] Evaluating user answer '{user_answer}' for problem '{problem}'")
#     return random.choice([
#         "That's correct! Well done.",
#         "Not quite, let's review the concept.",
#         "Good attempt! The correct answer is Y=5. Let's see why..."
#     ])