# backend/app.py
from flask import Flask, jsonify, request
from flask_cors import CORS
import hardcoded_data
# import mock_gemini # Remove or comment out old mock import
import gemini_interaction as gemini_api # Use the new Gemini interaction module
import logging # For logging from app.py as well

app = Flask(__name__)
CORS(app)

# Configure basic logging for Flask app
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(module)s - %(message)s')


@app.route('/api/subjects', methods=['GET'])
def api_get_subjects():
    app.logger.info("GET /api/subjects called")
    return jsonify(hardcoded_data.get_subjects())

@app.route('/api/topics', methods=['GET'])
def api_get_topics():
    subject = request.args.get('subject')
    app.logger.info(f"GET /api/topics called with subject: {subject}")
    if not subject:
        app.logger.warning("Subject parameter missing for /api/topics")
        return jsonify({"error": "Subject parameter is required"}), 400
    return jsonify(hardcoded_data.get_topics(subject))

@app.route('/api/initial-mcqs', methods=['POST'])
def api_initial_mcqs():
    data = request.json
    subject = data.get('subject')
    topic = data.get('topic')
    app.logger.info(f"POST /api/initial-mcqs for subject: {subject}, topic: {topic}")

    if not subject or not topic:
        app.logger.warning("Missing subject or topic for /api/initial-mcqs")
        return jsonify({"error": "Subject and topic are required"}), 400

    questions = gemini_api.generate_mcqs(topic, num_questions=3)
    if not questions: # Handles empty list or other failures from Gemini
        app.logger.error(f"Failed to generate initial MCQs for topic: {topic}")
        return jsonify({"error": "AI failed to generate initial quiz questions. Please try again later."}), 500
    
    app.logger.info(f"Successfully generated {len(questions)} initial MCQs for topic: {topic}")
    return jsonify({"questions": questions})


@app.route('/api/evaluate-initial-mcqs', methods=['POST'])
def api_evaluate_initial_mcqs():
    data = request.json
    user_answers = data.get('answers')
    original_questions = data.get('original_questions')
    subject = data.get('subject') # For fetching sections if needed
    topic = data.get('topic')     # For fetching sections if needed
    app.logger.info(f"POST /api/evaluate-initial-mcqs for topic: {topic}")


    if not user_answers or not original_questions:
        app.logger.warning("Missing answers or original_questions for MCQ evaluation")
        return jsonify({"error": "Answers and original questions are required"}), 400

    correct_count = 0
    for user_ans in user_answers:
        q_id = user_ans.get("question_id")
        selected_answer = user_ans.get("selected_answer")
        
        original_q = next((q for q in original_questions if q["id"] == q_id), None)
        if original_q and original_q["correct_answer"] == selected_answer:
            correct_count += 1
            
    all_correct = correct_count == len(original_questions)
    app.logger.info(f"MCQ Evaluation: {correct_count}/{len(original_questions)} correct. All correct: {all_correct}")
    
    if all_correct:
        return jsonify({"all_correct": True, "message": "Great job! All correct."})
    else:
        sections = hardcoded_data.get_sections(subject, topic)
        return jsonify({
            "all_correct": False,
            "message": f"You got {correct_count} out of {len(original_questions)} correct. Let's review the topic.",
            "sections": sections
        })

@app.route('/api/learning-content', methods=['POST'])
def api_learning_content():
    data = request.json
    subject = data.get('subject')
    topic = data.get('topic')
    section_title = data.get('section_title')
    content_type = data.get('content_type') # 'explanation', 'example', 'problem'
    app.logger.info(f"POST /api/learning-content for {topic} - {section_title}, type: {content_type}")


    if not all([subject, topic, section_title, content_type]):
        app.logger.warning("Missing parameters for /api/learning-content")
        return jsonify({"error": "Missing required parameters"}), 400

    content = ""
    if content_type == "explanation":
        content = gemini_api.generate_explanation(topic, section_title)
    elif content_type == "example":
        content = gemini_api.generate_solved_example(topic, section_title)
    elif content_type == "problem":
        problem_mcq = gemini_api.generate_problem(topic, section_title)
        if not problem_mcq: # Check if None or empty
            app.logger.error(f"AI failed to generate problem MCQ for {topic} - {section_title}")
            user_error_message = "Sorry, the AI tutor couldn't generate a practice problem for this section. Please try moving to the next step or try again later."
            # Return the raw_error if you want more details on frontend/logging for debugging
            return jsonify({"error": user_error_message, "raw_error": "Problem generation returned None from AI"}), 500
        content = problem_mcq # content is now the MCQ dict
    else:
        app.logger.warning(f"Invalid content_type: {content_type}")
        return jsonify({"error": "Invalid content_type"}), 400
    
    # Check for error strings from text generation, or if content is still None (e.g. invalid content_type not caught)
    if isinstance(content, str) and (content.startswith("[AI Error:") or content.startswith("[Error:") or content.startswith("[AI content generation blocked:")):
        app.logger.error(f"AI failed to generate content for {content_type} on {topic} - {section_title}: {content}")
        user_error_message = "Sorry, the AI tutor couldn't generate this part of the lesson. Please try moving to the next step or try again later."
        if "blocked" in content:
            user_error_message = "Sorry, the AI tutor couldn't generate this content due to safety filters. Please try a different section or topic."
        return jsonify({"error": user_error_message, "raw_error": content}), 500
    elif content is None and content_type not in ["explanation", "example", "problem"]: # Should be caught by invalid content_type earlier
        app.logger.error(f"Content remained None for an unknown reason, content_type: {content_type}")
        return jsonify({"error": "An unexpected error occurred generating content."}), 500
        
    app.logger.info(f"Successfully generated learning content for {content_type}")
    return jsonify({"content": content})


@app.route('/api/advanced-mcqs', methods=['POST'])
def api_advanced_mcqs():
    data = request.json
    topic = data.get('topic')
    app.logger.info(f"POST /api/advanced-mcqs for topic: {topic}")

    if not topic:
        app.logger.warning("Missing topic for /api/advanced-mcqs")
        return jsonify({"error": "Topic is required"}), 400
    
    questions = gemini_api.generate_mcqs(topic, num_questions=5)
    if not questions: # Handles empty list or other failures from Gemini
        app.logger.error(f"Failed to generate advanced MCQs for topic: {topic}")
        return jsonify({"error": "AI failed to generate advanced quiz questions. Please try again later."}), 500
    
    app.logger.info(f"Successfully generated {len(questions)} advanced MCQs for topic: {topic}")
    return jsonify({"questions": questions})

@app.route('/api/evaluate-problem-answer', methods=['POST'])
def api_evaluate_problem_answer():
    data = request.json
    user_answer = data.get('user_answer')
    problem = data.get('problem')  # Should be the MCQ dict as returned by generate_problem
    app.logger.info(f"POST /api/evaluate-problem-answer for problem id: {problem.get('id') if problem else None}")

    if not user_answer or not problem:
        app.logger.warning("Missing user_answer or problem for problem answer evaluation")
        return jsonify({"error": "User answer and problem are required"}), 400

    correct_answer = problem.get('correct_answer')
    is_correct = (user_answer.strip() == correct_answer.strip())

    if is_correct:
        return jsonify({"correct": True, "message": "Correct! Proceed to the next section."})
    else:
        return jsonify({"correct": False, "message": "Incorrect. Please review this section and try again."})

if __name__ == '__main__':
    # This part is for local development only.
    # Gunicorn will directly run the 'app' object in production.
    app.logger.info("Starting Flask app for local development...")
    app.run(debug=True, host='0.0.0.0', port=5001) # Added host='0.0.0.0' for broader accessibility if needed locally
