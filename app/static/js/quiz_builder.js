/**
 * app/static/js/quiz_builder.js
 * Google Forms Assessment Engine: Visual Question Builder & Reordering
 */

document.addEventListener("DOMContentLoaded", () => {
    const builderForm = document.getElementById("quizBuilderForm");
    const container = document.getElementById("questionsContainer");
    const addQuestionBtn = document.getElementById("addQuestionBtn");
    const saveQuizBtn = document.getElementById("saveQuizBtn");

    if (!builderForm || !container) return;

    let questionIdSequence = 0;

    // Helper: Escape HTML strings
    function escapeHtml(string) {
        if (!string) return "";
        return String(string)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    // Helper: Create a Question Card DOM Element
    function createQuestionCard(data = null) {
        questionIdSequence++;
        const qId = questionIdSequence;
        const prompt = data ? (data.prompt || "") : "";
        const points = data ? (parseInt(data.points) || 1) : 1;
        const options = data && data.options && data.options.length >= 2 ? data.options : [
            { text: "Option 1", is_correct: true },
            { text: "Option 2", is_correct: false }
        ];

        const card = document.createElement("div");
        card.className = "gf-edit-card";
        card.id = `qCard_${qId}`;

        card.innerHTML = `
            <div class="d-flex justify-content-between align-items-center mb-3 flex-wrap gap-2">
                <div class="d-flex align-items-center gap-2">
                    <span class="fw-bold text-secondary fs-5">Question <span class="q-number"></span></span>
                    <span class="badge bg-light text-secondary border small">
                        <i class="bi bi-ui-radios me-1 text-purple" style="color: var(--gf-purple);"></i> Multiple Choice
                    </span>
                </div>
                <div class="d-flex align-items-center gap-2">
                    <label class="small text-muted mb-0 fw-semibold">Points:</label>
                    <input type="number" class="form-control form-control-sm q-points" style="width: 75px;" min="1" max="100" value="${points}">
                    
                    <div class="d-flex align-items-center gap-1 ms-2">
                        <button type="button" class="btn btn-sm btn-outline-secondary move-up-btn py-1 px-2" title="Move Question Up">
                            <i class="bi bi-arrow-up me-1"></i> Up
                        </button>
                        <button type="button" class="btn btn-sm btn-outline-secondary move-down-btn py-1 px-2" title="Move Question Down">
                            <i class="bi bi-arrow-down me-1"></i> Down
                        </button>
                    </div>
                </div>
            </div>

            <div class="mb-3">
                <input type="text" class="form-control form-control-lg q-prompt" 
                       placeholder="Enter question prompt..." value="${escapeHtml(prompt)}" required>
            </div>

            <div class="options-list mb-3" id="optsList_${qId}"></div>

            <div class="d-flex justify-content-between align-items-center pt-3 border-top flex-wrap gap-2">
                <button type="button" class="btn btn-sm btn-outline-primary rounded-pill add-opt-btn">
                    <i class="bi bi-plus-lg me-1"></i> Add Option
                </button>

                <div class="d-flex gap-2">
                    <button type="button" class="btn btn-sm btn-outline-secondary duplicate-q-btn" title="Duplicate Question">
                        <i class="bi bi-copy me-1"></i> Duplicate
                    </button>
                    <button type="button" class="btn btn-sm btn-outline-danger delete-q-btn" title="Delete Question">
                        <i class="bi bi-trash3-fill me-1"></i> Delete
                    </button>
                </div>
            </div>
        `;

        // Render Options
        const optsContainer = card.querySelector(`#optsList_${qId}`);
        options.forEach(opt => {
            addOptionRow(optsContainer, qId, opt.text, opt.is_correct);
        });

        // Event: Add Option Row
        card.querySelector(".add-opt-btn").addEventListener("click", () => {
            const count = optsContainer.querySelectorAll(".gf-builder-opt-row").length + 1;
            addOptionRow(optsContainer, qId, `Option ${count}`, false);
        });

        // Event: Move Question Up
        card.querySelector(".move-up-btn").addEventListener("click", () => {
            const prev = card.previousElementSibling;
            if (prev) {
                container.insertBefore(card, prev);
                renumberQuestions();
                card.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
        });

        // Event: Move Question Down
        card.querySelector(".move-down-btn").addEventListener("click", () => {
            const next = card.nextElementSibling;
            if (next) {
                container.insertBefore(next, card);
                renumberQuestions();
                card.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
        });

        // Event: Duplicate Question
        card.querySelector(".duplicate-q-btn").addEventListener("click", () => {
            const currentData = serializeSingleCard(card);
            const duplicatedCard = createQuestionCard(currentData);
            card.after(duplicatedCard);
            renumberQuestions();
            duplicatedCard.scrollIntoView({ behavior: 'smooth', block: 'center' });
            if (typeof showGfToast === "function") {
                showGfToast("Question duplicated successfully.", "success");
            }
        });

        // Event: Delete Question
        card.querySelector(".delete-q-btn").addEventListener("click", () => {
            if (document.querySelectorAll(".gf-edit-card").length <= 1) {
                if (typeof showGfToast === "function") {
                    showGfToast("A quiz must contain at least one question.", "warning");
                } else {
                    alert("A quiz must contain at least one question.");
                }
                return;
            }
            card.remove();
            renumberQuestions();
        });

        return card;
    }

    // Helper: Add Option Row to an Options Container
    function addOptionRow(container, qId, text = "", isCorrect = false) {
        const optRow = document.createElement("div");
        optRow.className = "gf-builder-opt-row";
        optRow.innerHTML = `
            <input type="radio" name="correct_opt_${qId}" title="Select as correct answer key" ${isCorrect ? 'checked' : ''}>
            <input type="text" class="form-control form-control-sm opt-text" placeholder="Option text..." value="${escapeHtml(text)}" required>
            <button type="button" class="btn btn-sm btn-link text-danger p-0 delete-opt-btn" title="Remove option">
                <i class="bi bi-x-lg"></i>
            </button>
        `;

        optRow.querySelector(".delete-opt-btn").addEventListener("click", () => {
            if (container.querySelectorAll(".gf-builder-opt-row").length <= 2) {
                if (typeof showGfToast === "function") {
                    showGfToast("Each question must contain at least 2 options.", "warning");
                } else {
                    alert("Each question must contain at least 2 options.");
                }
                return;
            }
            const wasChecked = optRow.querySelector('input[type="radio"]').checked;
            optRow.remove();
            // If the deleted option was the correct one, make the first option checked
            if (wasChecked) {
                const firstRadio = container.querySelector('input[type="radio"]');
                if (firstRadio) firstRadio.checked = true;
            }
        });

        container.appendChild(optRow);
    }

    // Helper: Extract data from a single card
    function serializeSingleCard(card) {
        const prompt = card.querySelector(".q-prompt").value.trim();
        const points = parseInt(card.querySelector(".q-points").value) || 1;
        const optionRows = card.querySelectorAll(".gf-builder-opt-row");
        const optionsData = [];

        optionRows.forEach(optRow => {
            optionsData.push({
                text: optRow.querySelector(".opt-text").value.trim(),
                is_correct: optRow.querySelector('input[type="radio"]').checked
            });
        });

        return {
            prompt: prompt,
            points: points,
            options: optionsData
        };
    }

    // Helper: Renumber Question Cards and update move buttons
    function renumberQuestions() {
        const cards = document.querySelectorAll(".gf-edit-card");
        cards.forEach((card, index) => {
            const numSpan = card.querySelector(".q-number");
            if (numSpan) numSpan.textContent = index + 1;

            const upBtn = card.querySelector(".move-up-btn");
            const downBtn = card.querySelector(".move-down-btn");
            if (upBtn) upBtn.disabled = index === 0;
            if (downBtn) downBtn.disabled = index === cards.length - 1;
        });
    }

    // Event: Add New Question Click
    if (addQuestionBtn) {
        addQuestionBtn.addEventListener("click", () => {
            const newCard = createQuestionCard();
            container.appendChild(newCard);
            renumberQuestions();
            newCard.scrollIntoView({ behavior: 'smooth', block: 'center' });
            newCard.querySelector(".q-prompt").focus();
        });
    }

    // Event: Save Quiz Submission
    if (saveQuizBtn) {
        saveQuizBtn.addEventListener("click", () => {
            const titleInput = document.getElementById("quizTitle");
            const title = titleInput ? titleInput.value.trim() : "";
            if (!title) {
                if (typeof showGfToast === "function") {
                    showGfToast("Please provide a Quiz Title.", "warning");
                } else {
                    alert("Please provide a Quiz Title.");
                }
                if (titleInput) titleInput.focus();
                return;
            }

            const passPercentage = parseFloat(document.getElementById("passPercentage").value) || 50.0;
            const timeLimitMinutes = parseInt(document.getElementById("timeLimitMinutes").value) || 0;
            const description = document.getElementById("quizDescription").value.trim();

            const questionCards = document.querySelectorAll(".gf-edit-card");
            if (questionCards.length === 0) {
                if (typeof showGfToast === "function") {
                    showGfToast("The quiz must contain at least one question.", "warning");
                } else {
                    alert("The quiz must contain at least one question.");
                }
                return;
            }

            const questionsData = [];

            for (let i = 0; i < questionCards.length; i++) {
                const card = questionCards[i];
                const prompt = card.querySelector(".q-prompt").value.trim();
                const points = parseInt(card.querySelector(".q-points").value) || 1;

                if (!prompt) {
                    if (typeof showGfToast === "function") {
                        showGfToast(`Question ${i + 1} prompt cannot be empty.`, "warning");
                    } else {
                        alert(`Question ${i + 1} prompt cannot be empty.`);
                    }
                    card.querySelector(".q-prompt").focus();
                    return;
                }

                const optionRows = card.querySelectorAll(".gf-builder-opt-row");
                if (optionRows.length < 2) {
                    if (typeof showGfToast === "function") {
                        showGfToast(`Question ${i + 1} must have at least 2 options.`, "warning");
                    } else {
                        alert(`Question ${i + 1} must have at least 2 options.`);
                    }
                    return;
                }

                const optionsData = [];
                let hasCorrect = false;

                for (let j = 0; j < optionRows.length; j++) {
                    const optRow = optionRows[j];
                    const optText = optRow.querySelector(".opt-text").value.trim();
                    const isCorrect = optRow.querySelector('input[type="radio"]').checked;

                    if (!optText) {
                        if (typeof showGfToast === "function") {
                            showGfToast(`Question ${i + 1}, Option ${j + 1} text cannot be empty.`, "warning");
                        } else {
                            alert(`Question ${i + 1}, Option ${j + 1} text cannot be empty.`);
                        }
                        optRow.querySelector(".opt-text").focus();
                        return;
                    }

                    if (isCorrect) hasCorrect = true;
                    optionsData.push({ text: optText, is_correct: isCorrect });
                }

                if (!hasCorrect) {
                    if (typeof showGfToast === "function") {
                        showGfToast(`Please select the correct answer for Question ${i + 1} using the radio button.`, "warning");
                    } else {
                        alert(`Please select the correct answer for Question ${i + 1} using the radio button.`);
                    }
                    return;
                }

                questionsData.push({
                    prompt: prompt,
                    points: points,
                    options: optionsData
                });
            }

            const payload = {
                title: title,
                description: description,
                pass_percentage: passPercentage,
                time_limit_minutes: timeLimitMinutes,
                questions: questionsData
            };

            document.getElementById("quiz_data").value = JSON.stringify(payload);
            builderForm.submit();
        });
    }

    // Initialize Questions: Read from JSON Data Island if present
    const dataIsland = document.getElementById("initialQuizData");
    let initialQuestions = [];
    if (dataIsland) {
        try {
            initialQuestions = JSON.parse(dataIsland.textContent);
        } catch (e) {
            initialQuestions = [];
        }
    }

    if (Array.isArray(initialQuestions) && initialQuestions.length > 0) {
        initialQuestions.forEach(q => {
            container.appendChild(createQuestionCard(q));
        });
    } else {
        // Starter Question for blank quiz
        container.appendChild(createQuestionCard());
    }

    renumberQuestions();
});
