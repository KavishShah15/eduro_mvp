// const API_BASE_URL = 'http://localhost:5001/api'; // Backend URL
const API_BASE_URL = '/api';
// DOM Elements
const subjectSelect = document.getElementById('subject-select');
const topicSelect = document.getElementById('topic-select');
const startLearningBtn = document.getElementById('start-learning-btn');

const selectionArea = document.getElementById('selection-area');
const mcqArea = document.getElementById('mcq-area');
const mcqQuestionsDiv = document.getElementById('mcq-questions');
const submitMcqBtn = document.getElementById('submit-mcq-btn');

const learningFlowArea = document.getElementById('learning-flow-area');
const chatLog = document.getElementById('chat-log');
const problemOptionsDiv = document.getElementById('problem-options-area');
const userInputArea = document.getElementById('user-input-area');
const userChatInput = document.getElementById('user-chat-input');
const sendChatBtn = document.getElementById('send-chat-btn');
const nextStepBtn = document.getElementById('next-step-btn');

const advancedMcqArea = document.getElementById('advanced-mcq-area');
const advancedMcqQuestionsDiv = document.getElementById('advanced-mcq-questions');
const submitAdvancedMcqBtn = document.getElementById('submit-advanced-mcq-btn');

const statusMessageDiv = document.getElementById('status-message');

const appContainer = document.querySelector('.app-container');
const mainContent = document.querySelector('.main-content');


// App State
let currentSubject = '';
let currentTopic = '';
let initialMcqQuestions = [];
let learningSections = [];
let currentSectionIndex = 0;
let currentSectionPhase = '';
let currentLearningProblem = null;
let statusTimeout = null; // To manage auto-hiding status

// --- Helper Functions ---
function showStatus(message, isError = false) {
    clearTimeout(statusTimeout); // Clear existing timeout

    if (!message) {
        statusMessageDiv.classList.remove('show');
        statusMessageDiv.classList.remove('error');
        statusMessageDiv.classList.remove('info');
        return;
    }
    statusMessageDiv.textContent = message;
    statusMessageDiv.classList.remove('error', 'info'); // Clear previous types

    if (isError) {
        statusMessageDiv.classList.add('error');
        console.error("ERROR:", message);
    } else {
        statusMessageDiv.classList.add('info');
        console.log("STATUS:", message);
    }
    statusMessageDiv.classList.add('show');
    
    statusTimeout = setTimeout(() => {
        statusMessageDiv.classList.remove('show');
    }, 4000); // Hide after 4 seconds
}

function toggleVisibility(element, show) {
    if (show) {
        element.classList.remove('hidden');
    } else {
        element.classList.add('hidden');
    }
}

function addChatMessage(message, sender = 'tutor') {
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('chat-message', sender);
    let formattedMessage = message.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    formattedMessage = formattedMessage.replace(/\n/g, '<br>');
    messageDiv.innerHTML = formattedMessage;
    chatLog.appendChild(messageDiv);
    chatLog.scrollTop = chatLog.scrollHeight;
}

function toggleMainInterface(showLearningFlow) {
    if (showLearningFlow) {
        toggleVisibility(selectionArea, false);
        toggleVisibility(mcqArea, false);
        toggleVisibility(advancedMcqArea, false);
        toggleVisibility(learningFlowArea, true);
        mainContent.classList.add('learning-active');
    } else {
        toggleVisibility(learningFlowArea, false);
        mainContent.classList.remove('learning-active');
        // Specific views (selection, mcq) will be shown by their respective functions
    }
}

// --- API Call Functions ---
async function fetchSubjects() {
    try {
        showStatus("Fetching subjects...");
        const response = await fetch(`${API_BASE_URL}/subjects`);
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        const subjects = await response.json();
        subjects.forEach(subject => {
            const option = new Option(subject, subject);
            subjectSelect.add(option);
        });
        showStatus("Subjects loaded. Please select one.");
    } catch (error) {
        showStatus(`Error fetching subjects: ${error.message}`, true);
    }
}

async function fetchTopics(subject) {
    topicSelect.innerHTML = '<option value="">--Select Topic--</option>';
    topicSelect.disabled = true;
    startLearningBtn.disabled = true;
    if (!subject) return;

    try {
        showStatus(`Fetching topics for ${subject}...`);
        const response = await fetch(`${API_BASE_URL}/topics?subject=${encodeURIComponent(subject)}`);
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        const topics = await response.json();
        topics.forEach(topic => {
            const option = new Option(topic, topic);
            topicSelect.add(option);
        });
        topicSelect.disabled = false;
        showStatus(`Topics for ${subject} loaded. Please select one.`);
    } catch (error) {
        showStatus(`Error fetching topics for ${subject}: ${error.message}`, true);
    }
}

async function startInitialMcq() {
    showStatus('Fetching initial quiz...');
    toggleMainInterface(false);
    toggleVisibility(selectionArea, false);
    toggleVisibility(mcqArea, true);

    try {
        const response = await fetch(`${API_BASE_URL}/initial-mcqs`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ subject: currentSubject, topic: currentTopic })
        });
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.error || `HTTP error! status: ${response.status}`);
        }
        if (!data.questions || data.questions.length === 0) {
            showStatus("No questions received for the initial quiz. Try another topic?", true)
            initialMcqQuestions = []; // ensure it's empty
            // Potentially go back to selection:
            // toggleVisibility(mcqArea, false);
            // toggleVisibility(selectionArea, true);
            return;
        }
        initialMcqQuestions = data.questions;
        renderMcqs(data.questions, mcqQuestionsDiv);
        showStatus('Initial quiz loaded. Please answer the questions.');
    } catch (error) {
        showStatus(`Error fetching initial MCQs: ${error.message}`, true);
        toggleVisibility(selectionArea, true);
        toggleVisibility(mcqArea, false);
    }
}

function renderMcqs(questions, container) {
    container.innerHTML = '';
    questions.forEach((q, index) => {
        const qDiv = document.createElement('div');
        qDiv.classList.add('mcq-question');
        const questionText = document.createElement('p');
        questionText.innerHTML = `${index + 1}. ${q.question_text}`;
        qDiv.appendChild(questionText);
        
        q.options.forEach(option => {
            const label = document.createElement('label');
            const input = document.createElement('input');
            input.type = 'radio';
            input.name = `question-${q.id}`;
            input.value = option;
            label.appendChild(input);
            label.append(` ${option}`);
            qDiv.appendChild(label);
        });
        container.appendChild(qDiv);
    });
}

async function submitInitialMcqs() {
    const userAnswers = [];
    initialMcqQuestions.forEach(q => {
        const selectedOption = document.querySelector(`input[name="question-${q.id}"]:checked`);
        if (selectedOption) {
            userAnswers.push({ question_id: q.id, selected_answer: selectedOption.value });
        }
    });

    if (userAnswers.length !== initialMcqQuestions.length) {
        showStatus('Please answer all questions.', true);
        return;
    }

    showStatus('Submitting answers...');
    try {
        const response = await fetch(`${API_BASE_URL}/evaluate-initial-mcqs`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                answers: userAnswers, 
                original_questions: initialMcqQuestions,
                subject: currentSubject,
                topic: currentTopic
            })
        });
        const result = await response.json();
        if (!response.ok) {
            throw new Error(result.error || `HTTP error! status: ${response.status}`);
        }
        showStatus(result.message);
        // toggleVisibility(mcqArea, false); // This will be handled by next step

        if (result.all_correct) {
            // toggleMainInterface(false); // Will be handled by startAdvancedMcq
            startAdvancedMcq();
        } else {
            learningSections = result.sections || [];
            currentSectionIndex = 0;
            startLearningFlow(); // This will call toggleMainInterface(true)
        }
    } catch (error) {
        showStatus(`Error submitting MCQs: ${error.message}`, true);
        // Optionally, re-enable mcqArea if submission failed without navigating
        // toggleVisibility(mcqArea, true); 
    }
}

async function startAdvancedMcq() {
    showStatus('Fetching advanced quiz...');
    toggleMainInterface(false);
    toggleVisibility(selectionArea, false); // Ensure others are hidden
    toggleVisibility(mcqArea, false);
    toggleVisibility(learningFlowArea, false);
    toggleVisibility(advancedMcqArea, true);
    try {
        const response = await fetch(`${API_BASE_URL}/advanced-mcqs`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ topic: currentTopic })
        });
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.error || `HTTP error! status: ${response.status}`);
        }
        if (!data.questions || data.questions.length === 0) {
            showStatus("No questions received for the advanced quiz. You can try another topic.", true);
            // Optionally, navigate back to selection or end session.
            toggleVisibility(advancedMcqArea, false);
            toggleVisibility(selectionArea, true);
            return;
        }
        renderMcqs(data.questions, advancedMcqQuestionsDiv);
        showStatus('Advanced quiz loaded.');
    } catch (error) {
        showStatus(`Error fetching advanced MCQs: ${error.message}`, true);
        toggleVisibility(advancedMcqArea, false);
        toggleVisibility(selectionArea, true);
    }
}

function submitAdvancedMcqsHandler() {
    showStatus("Advanced quiz submitted! (Evaluation not implemented). You can restart to learn another topic.");
    toggleMainInterface(false);
    toggleVisibility(advancedMcqArea, false);
    toggleVisibility(selectionArea, true);
    resetState(false); // Reset state but don't show initial welcome
}


// --- Learning Flow Logic ---
function startLearningFlow() {
    toggleMainInterface(true);
    chatLog.innerHTML = '';
    if (learningSections.length > 0) {
        currentSectionIndex = 0;
        currentSectionPhase = '';
        handleNextLearningStep();
    } else {
        addChatMessage("No learning sections defined for this topic. Let's go to the advanced quiz or pick another topic.");
        startAdvancedMcq();
    }
}

async function handleNextLearningStep() {
    toggleVisibility(userInputArea, false);
    toggleVisibility(nextStepBtn, false);
    toggleVisibility(problemOptionsDiv, false);
    problemOptionsDiv.innerHTML = '';

    if (currentSectionIndex >= learningSections.length) {
        addChatMessage("🎉 You've completed all learning sections for this topic! Well done. Let's try an advanced quiz.");
        startAdvancedMcq();
        return;
    }

    const sectionTitle = learningSections[currentSectionIndex];

    try {
        if (!currentSectionPhase) {
            currentSectionPhase = 'explanation';
            addChatMessage(`Let's start with the section: **${sectionTitle}**.`);
            addChatMessage("Ready for an explanation? (Click 'Next' or type 'next')");
            toggleVisibility(nextStepBtn, true);
            toggleVisibility(userInputArea, true);
            userChatInput.placeholder = "Type 'next' or click the button";
            userChatInput.value = '';
        } else if (currentSectionPhase === 'get_explanation') {
            showStatus(`Fetching explanation for "${sectionTitle}"...`);
            const content = await fetchLearningContent(sectionTitle, 'explanation');
            showStatus(""); // Clear status after fetch
            addChatMessage(content);
            addChatMessage("Understood? Ready for a solved example? (Click 'Next' or type 'next')");
            currentSectionPhase = 'example';
            toggleVisibility(nextStepBtn, true);
            toggleVisibility(userInputArea, true);
            userChatInput.placeholder = "Type 'next' or click the button";
        } else if (currentSectionPhase === 'get_example') {
            showStatus(`Fetching solved example for "${sectionTitle}"...`);
            const content = await fetchLearningContent(sectionTitle, 'example');
            showStatus("");
            addChatMessage(content);
            addChatMessage("Got it? Now, ready for a problem to solve on your own? (Click 'Next' or type 'next')");
            currentSectionPhase = 'problem';
            toggleVisibility(nextStepBtn, true);
            toggleVisibility(userInputArea, true);
            userChatInput.placeholder = "Type 'next' or click the button";
        } else if (currentSectionPhase === 'get_problem') {
            showStatus(`Fetching a problem for "${sectionTitle}"...`);
            const problemData = await fetchLearningContent(sectionTitle, 'problem');
            showStatus("");

            if (typeof problemData === 'object' && problemData.question_text && problemData.options) {
                currentLearningProblem = problemData;
                addChatMessage(`**Problem:**\n${problemData.question_text}`);
                renderProblemOptions(problemData.options);
                currentSectionPhase = 'awaiting_problem_selection';
            } else {
                throw new Error(problemData.error || "Failed to load problem content correctly.");
            }
        }
    } catch (error) {
        const userMessage = `Sorry, an error occurred: ${error.message}. You can click 'Next' to try this step again or move to the next part.`;
        showStatus(error.message, true);
        addChatMessage(userMessage, 'tutor');
        
        if (currentSectionPhase === 'get_explanation') currentSectionPhase = 'explanation';
        else if (currentSectionPhase === 'get_example') currentSectionPhase = 'example';
        else if (currentSectionPhase === 'get_problem') currentSectionPhase = 'problem';
        
        toggleVisibility(nextStepBtn, true);
        toggleVisibility(userInputArea, false);
    }
}

function renderProblemOptions(optionsArray) {
    problemOptionsDiv.innerHTML = '';
    optionsArray.forEach(optionText => {
        const button = document.createElement('button');
        button.textContent = optionText;
        button.classList.add('problem-option-btn');
        button.addEventListener('click', () => handleProblemOptionClick(optionText));
        problemOptionsDiv.appendChild(button);
    });
    toggleVisibility(problemOptionsDiv, true);
}

async function handleProblemOptionClick(selectedOption) {
    addChatMessage(selectedOption, 'user');
    toggleVisibility(problemOptionsDiv, false);
    problemOptionsDiv.innerHTML = '';

    if (!currentLearningProblem) {
        addChatMessage("Error: No problem context found. Please try again.", 'tutor');
        showStatus("Error: Missing currentLearningProblem context.", true);
        currentSectionPhase = 'problem';
        toggleVisibility(nextStepBtn, true);
        return;
    }

    showStatus('Evaluating your answer...');
    try {
        const response = await fetch(`${API_BASE_URL}/evaluate-problem-answer`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_answer: selectedOption,
                problem: currentLearningProblem
            })
        });
        const result = await response.json();
        if (!response.ok) {
            throw new Error(result.error || `HTTP error! status: ${response.status}`);
        }
        
        showStatus(result.message); // Show evaluation message (correct/incorrect)
        addChatMessage(result.message, 'tutor');

        if (result.correct) {
            currentSectionIndex++;
            currentSectionPhase = '';
            currentLearningProblem = null;
            handleNextLearningStep();
        } else {
            addChatMessage("Let's try another problem on this section, or review the material. Click 'Next' to get a new problem.", 'tutor');
            currentSectionPhase = 'problem';
            currentLearningProblem = null;
            toggleVisibility(nextStepBtn, true);
        }
    } catch (error) {
        const msg = `Error evaluating answer: ${error.message}`;
        showStatus(msg, true);
        addChatMessage(msg + " Click 'Next' to try again.", 'tutor');
        currentSectionPhase = 'problem';
        currentLearningProblem = null;
        toggleVisibility(nextStepBtn, true);
    }
}

async function fetchLearningContent(sectionTitle, contentType) {
    try {
        const response = await fetch(`${API_BASE_URL}/learning-content`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                subject: currentSubject,
                topic: currentTopic,
                section_title: sectionTitle,
                content_type: contentType
            })
        });
        const data = await response.json(); 
        if (!response.ok) {
            const errorMsg = data.error || `Server error while fetching ${contentType}`;
            if (data.raw_error) console.error("Raw backend error:", data.raw_error);
            throw new Error(errorMsg);
        }
        if(data.error){ 
            if (data.raw_error) console.error("Raw backend error:", data.raw_error);
            throw new Error(data.error);
        }
        if (data.content === undefined) {
             throw new Error("Received OK response but no 'content' from backend.");
        }
        return data.content; 
    } catch (error) {
        throw error;
    }
}

function handleUserChatInput() {
    const userInput = userChatInput.value.trim();
    if (!userInput) return;

    addChatMessage(userInput, 'user');
    userChatInput.value = '';

    if (userInput.toLowerCase() === 'next') {
        if (currentSectionPhase === 'explanation') currentSectionPhase = 'get_explanation';
        else if (currentSectionPhase === 'example') currentSectionPhase = 'get_example';
        else if (currentSectionPhase === 'problem') currentSectionPhase = 'get_problem';
        handleNextLearningStep();
    } else if (currentSectionPhase === 'awaiting_problem_selection') {
        addChatMessage("Please select an answer from the buttons above.", 'tutor');
    } else {
        addChatMessage("I'm waiting for you to type 'next' to continue, or if there's a problem, please select an option.", 'tutor');
    }
}

// --- Event Listeners ---
subjectSelect.addEventListener('change', (e) => {
    currentSubject = e.target.value;
    currentTopic = '';
    fetchTopics(currentSubject);
    startLearningBtn.disabled = true;
});

topicSelect.addEventListener('change', (e) => {
    currentTopic = e.target.value;
    startLearningBtn.disabled = !currentTopic;
});

startLearningBtn.addEventListener('click', () => {
    if (currentSubject && currentTopic) {
        startInitialMcq();
    } else {
        showStatus('Please select both subject and topic.', true);
    }
});

submitMcqBtn.addEventListener('click', submitInitialMcqs);
submitAdvancedMcqBtn.addEventListener('click', submitAdvancedMcqsHandler);

sendChatBtn.addEventListener('click', handleUserChatInput);
userChatInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        handleUserChatInput();
    }
});

nextStepBtn.addEventListener('click', () => {
    if (currentSectionPhase === 'explanation') currentSectionPhase = 'get_explanation';
    else if (currentSectionPhase === 'example') currentSectionPhase = 'get_example';
    else if (currentSectionPhase === 'problem') currentSectionPhase = 'get_problem';
    handleNextLearningStep();
});

// --- Initialization ---
function resetState(showWelcome = true) { // Added parameter
    currentSubject = '';
    currentTopic = '';
    subjectSelect.value = '';
    topicSelect.innerHTML = '<option value="">--Select Topic--</option>';
    topicSelect.disabled = true;
    startLearningBtn.disabled = true;
    
    initialMcqQuestions = [];
    learningSections = [];
    currentSectionIndex = 0;
    currentSectionPhase = '';
    currentLearningProblem = null;
    
    mcqQuestionsDiv.innerHTML = '';
    advancedMcqQuestionsDiv.innerHTML = '';
    chatLog.innerHTML = '';
    problemOptionsDiv.innerHTML = '';
    toggleVisibility(problemOptionsDiv, false);

    toggleMainInterface(false);
    toggleVisibility(selectionArea, true);
    toggleVisibility(mcqArea, false);
    toggleVisibility(advancedMcqArea, false);
    toggleVisibility(learningFlowArea, false);
    
    if (showWelcome) {
        showStatus("Welcome! Please select a subject and topic to begin.");
    } else {
        showStatus(""); // Clear status if not showing welcome
    }
}

// Initial load
fetchSubjects();
resetState(); // This will call showStatus with the welcome message.
