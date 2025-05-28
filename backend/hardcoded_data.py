# In a real app, this might come from a database or a more complex config
SUBJECTS = {
    "Mathematics": {
        "Algebra Basics": {
            "sections": [
                "Variables and Expressions",
                "Solving Linear Equations",
                "Inequalities"
            ]
        },
        "Geometry": {
            "sections": [
                "Basic Shapes",
                "Area and Perimeter",
                "Pythagorean Theorem"
            ]
        },
        "Quadratic Equations": {
            "sections": [
                "Introduction",
                "Quadratic Equations",
                "Solution of a Quadratic Equation by Factorization",
                "Nature of Roots"
            ]
        }
    },
    "Science": {
        "Photosynthesis": {
            "sections": [
                "Introduction to Photosynthesis",
                "The Light-Dependent Reactions",
                "The Calvin Cycle (Light-Independent Reactions)"
            ]
        },
        "Newton's Laws of Motion": {
            "sections": [
                "First Law: Inertia",
                "Second Law: F = ma",
                "Third Law: Action-Reaction"
            ]
        }
    }
}

def get_subjects():
    return list(SUBJECTS.keys())

def get_topics(subject):
    return list(SUBJECTS.get(subject, {}).keys())

def get_sections(subject, topic):
    return SUBJECTS.get(subject, {}).get(topic, {}).get("sections", [])