/**
 * app/static/js/quiz_timer.js
 * Google Forms Assessment Engine: Live Timer, Progress Bar & Answered Tracker
 */

document.addEventListener("DOMContentLoaded", () => {
    const quizForm = document.getElementById("quizForm");
    if (!quizForm) return;

    // 1. Radio Selection Highlight Handler
    const radioInputs = document.querySelectorAll('.gf-option-label input[type="radio"]');
    radioInputs.forEach(radio => {
        radio.addEventListener("change", function () {
            const container = this.closest(".options-container");
            if (container) {
                container.querySelectorAll(".gf-option-label").forEach(lbl => lbl.classList.remove("active-opt"));
            }
            if (this.checked) {
                const parentLabel = this.closest(".gf-option-label");
                if (parentLabel) parentLabel.classList.add("active-opt");
            }
            updateAssessmentProgress();
        });
    });

    // 2. Live Assessment Progress Tracking
    const totalQuestions = document.querySelectorAll(".gf-question-card").length;
    const progressFill = document.getElementById("gfProgressFill");
    const progressText = document.getElementById("gfProgressText");

    function updateAssessmentProgress() {
        const answeredCount = document.querySelectorAll('.gf-question-card input[type="radio"]:checked').length;
        const percentage = totalQuestions > 0 ? Math.round((answeredCount / totalQuestions) * 100) : 0;

        if (progressFill) {
            progressFill.style.width = `${percentage}%`;
        }
        if (progressText) {
            progressText.textContent = `${answeredCount} of ${totalQuestions} Answered (${percentage}%)`;
        }
    }
    updateAssessmentProgress();

    // 3. Wall-Clock Drift-Proof Countdown Timer
    const timerBanner = document.getElementById("gfTimerBanner");
    if (timerBanner) {
        const timeLimitMinutes = parseFloat(timerBanner.dataset.timeLimitMinutes || "0");
        if (timeLimitMinutes > 0) {
            const timerDisplay = document.getElementById("timerDisplay");
            const durationMs = timeLimitMinutes * 60 * 1000;
            const targetEndTime = Date.now() + durationMs;
            let timerExpired = false;

            function tickCountdown() {
                if (timerExpired) return;

                const remainingMs = Math.max(0, targetEndTime - Date.now());
                const remainingSeconds = Math.ceil(remainingMs / 1000);

                const mins = Math.floor(remainingSeconds / 60);
                const secs = remainingSeconds % 60;

                if (timerDisplay) {
                    timerDisplay.textContent = `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
                }

                // Last 60 seconds warning
                if (remainingSeconds <= 60 && !timerBanner.classList.contains("timer-warning")) {
                    timerBanner.classList.add("timer-warning", "border-danger");
                    if (timerDisplay) timerDisplay.classList.add("fw-bolder");
                }

                // Time expired -> Auto-submit
                if (remainingSeconds <= 0) {
                    timerExpired = true;
                    clearInterval(timerInterval);

                    // Show a non-blocking toast alert
                    if (typeof showGfToast === "function") {
                        showGfToast("Time limit expired! Submitting your answers now...", "warning");
                    }

                    // Remove HTML5 required constraints so unanswered questions do not block submission
                    document.querySelectorAll('#quizForm input[required]').forEach(input => input.removeAttribute('required'));

                    // Submit after a brief tick to allow toast visibility
                    setTimeout(() => {
                        quizForm.submit();
                    }, 600);
                }
            }

            tickCountdown();
            const timerInterval = setInterval(tickCountdown, 1000);
        }
    }

    // 4. Pre-Submission Confirmation Modal for Unanswered Questions
    const submitBtn = document.getElementById("submitQuizBtn");
    const confirmModalEl = document.getElementById("unansweredModal");
    let confirmModal = null;
    if (confirmModalEl && typeof bootstrap !== "undefined") {
        confirmModal = new bootstrap.Modal(confirmModalEl);
    }

    if (submitBtn && confirmModalEl) {
        quizForm.addEventListener("submit", function (e) {
            const answeredCount = document.querySelectorAll('.gf-question-card input[type="radio"]:checked').length;
            const unanswered = totalQuestions - answeredCount;

            // If some questions are unanswered and submission was not already confirmed
            if (unanswered > 0 && !quizForm.dataset.confirmedSubmit) {
                e.preventDefault();
                const modalCountEl = document.getElementById("unansweredCount");
                if (modalCountEl) {
                    modalCountEl.textContent = unanswered;
                }
                confirmModal.show();
            }
        });

        const confirmSubmitBtn = document.getElementById("confirmSubmitAnywayBtn");
        if (confirmSubmitBtn) {
            confirmSubmitBtn.addEventListener("click", () => {
                quizForm.dataset.confirmedSubmit = "true";
                document.querySelectorAll('#quizForm input[required]').forEach(input => input.removeAttribute('required'));
                confirmModal.hide();
                quizForm.submit();
            });
        }
    }
});
