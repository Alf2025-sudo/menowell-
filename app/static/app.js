
const assessmentForm = document.getElementById("assessmentForm");
const assessmentResult = document.getElementById("assessmentResult");

const companionForm = document.getElementById("companionForm");
const companionResult = document.getElementById("companionResult");


// --------------------------------------------------
// 1. ASSESSMENT FORM
// --------------------------------------------------

if (assessmentForm) {
    assessmentForm.addEventListener("submit", async (event) => {
        event.preventDefault();

        const submitButton = assessmentForm.querySelector(
            'button[type="submit"]'
        );

        const originalButtonText = submitButton.textContent;

        submitButton.disabled = true;
        submitButton.textContent = "Reviewing your responses...";

        assessmentResult.innerHTML = `
            <p>Reviewing your responses. Please wait...</p>
        `;

        const checkboxFields = [
            "sudden_severe_testicular_pain",
            "significant_genital_swelling",
            "fever_with_genital_or_urinary_symptoms",
            "persistent_discomfort",
            "urinary_or_genital_symptoms",
            "previous_reproductive_condition",
            "medication_concern",
            "lifestyle_or_metabolic_concern",
            "trying_to_conceive_without_success",
            "wants_human_support"
        ];

        const data = {
            age_group: document.getElementById("age_group").value,
            main_goal: document.getElementById("main_goal").value
        };

        checkboxFields.forEach((field) => {
            data[field] = document.getElementById(field).checked;
        });

        try {
            const response = await fetch("/api/assess", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(data)
            });

            const result = await response.json();

            if (!response.ok) {
                throw new Error(
                    result.detail || "Assessment could not be completed."
                );
            }

            displayAssessmentResult(result);

        } catch (error) {
            assessmentResult.innerHTML = `
                <div class="error-message">
                    <strong>We couldn't complete your assessment.</strong>
                    <p>${escapeHTML(error.message)}</p>
                    <p>Please try again.</p>
                </div>
            `;

        } finally {
            submitButton.disabled = false;
            submitButton.textContent = originalButtonText;
        }
    });
}


// --------------------------------------------------
// 2. DISPLAY ASSESSMENT RESULT
// --------------------------------------------------


function displayAssessmentResult(result) {
    const reasons = Array.isArray(result.reasons)
        ? result.reasons
        : [];

    const nextSteps = Array.isArray(result.next_steps)
        ? result.next_steps
        : [];

    const levelLabels = {
        urgent: "Urgent attention",
        prompt_clinical_review: "Prompt clinical review",
        routine_discussion: "Routine professional discussion",
        general_information: "General health information"
    };

    const levelLabel =
        levelLabels[result.level] || "Guidance information";

    assessmentResult.innerHTML = `
        <div class="assessment-output">

            <p class="eyebrow">YOUR MENOWELL HEALTH SUMMARY</p>

            <h3>${escapeHTML(result.title || "Your assessment summary")}</h3>

            <div class="result-level">
                <span>Recommended guidance:</span>
                <strong>${escapeHTML(levelLabel)}</strong>
            </div>

            <p>
                ${escapeHTML(result.explanation || "")}
            </p>

            ${
                reasons.length
                    ? `
                        <h4>What informed this guidance?</h4>
                        <ul>
                            ${reasons.map(item =>
                                `<li>${escapeHTML(item)}</li>`
                            ).join("")}
                        </ul>
                    `
                    : ""
            }

            ${
                nextSteps.length
                    ? `
                        <h4>Your suggested next steps</h4>
                        <ul>
                            ${nextSteps.map(item =>
                                `<li>${escapeHTML(item)}</li>`
                            ).join("")}
                        </ul>
                    `
                    : ""
            }

            <p class="small-note">
                ${escapeHTML(result.prototype_notice || "")}
            </p>

            <div class="assessment-footer">
                <span>MenoWell · Private health guidance</span>
                <span>Not a medical diagnosis</span>
            </div>

        </div>
    `;

    assessmentResult.scrollIntoView({
        behavior: "smooth",
        block: "start"
    });
}
// --------------------------------------------------
// 3. AI COMPANION FORM
// --------------------------------------------------

if (companionForm) {
    companionForm.addEventListener("submit", async (event) => {
        event.preventDefault();

        const messageInput = document.getElementById("companionMessage");

        const submitButton = companionForm.querySelector(
            'button[type="submit"]'
        );

        const question = messageInput.value.trim();

        if (!question) {
            companionResult.textContent = "Please enter a question.";
            return;
        }

        const originalButtonText = submitButton.textContent;

        submitButton.disabled = true;
        submitButton.textContent = "Thinking...";

        companionResult.textContent =
            "MenoWell Companion is preparing a response. Please wait...";

        try {
            const response = await fetch("/api/companion", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    question: question
                })
            });

            const result = await response.json();

            if (!response.ok) {
                throw new Error(
                    result.detail || "The AI Companion could not respond."
                );
            }

            const answer =
                result.answer ||
                result.response ||
                result.message ||
                "No response was returned.";

            companionResult.innerHTML = `
                <div class="companion-answer">
                    <strong>MenoWell Companion</strong>
                    <p>${escapeHTML(answer).replace(/\n/g, "<br>")}</p>
                </div>
            `;

        } catch (error) {
            companionResult.innerHTML = `
                <div class="error-message">
                    <strong>Unable to get a response.</strong>
                    <p>${escapeHTML(error.message)}</p>
                    <p>Please try again.</p>
                </div>
            `;

        } finally {
            submitButton.disabled = false;
            submitButton.textContent = originalButtonText;
        }
    });
}


// --------------------------------------------------
// 4. SAFE TEXT DISPLAY
// --------------------------------------------------

function escapeHTML(value) {
    return String(value).replace(/[&<>"']/g, (character) => {
        const entities = {
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            '"': "&quot;",
            "'": "&#039;"
        };

        return entities[character];
    });
}


/* =========================================
   MENOWELL TALKREADY
========================================= */

const talkreadyForm = document.getElementById("talkreadyForm");
const talkreadyResult = document.getElementById("talkreadyResult");

if (talkreadyForm && talkreadyResult) {
    talkreadyForm.addEventListener("submit", async (event) => {
        event.preventDefault();

        const submitButton = talkreadyForm.querySelector(
            'button[type="submit"]'
        );

        const concern = document.getElementById(
            "talkreadyConcern"
        ).value.trim();

        const consultationGoal = document.getElementById(
            "talkreadyGoal"
        ).value.trim();

        const additionalContext = document.getElementById(
            "talkreadyContext"
        ).value.trim();

        submitButton.disabled = true;
        submitButton.textContent = "Preparing your consultation...";

        talkreadyResult.classList.add("visible");
        talkreadyResult.innerHTML = "<p>TalkReady is preparing your consultation guidance. Please wait...</p>";

        try {
            const response = await fetch("/api/talkready", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    concern: concern,
                    consultation_goal: consultationGoal,
                    additional_context: additionalContext
                })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(
                    data.detail || "Unable to prepare your consultation."
                );
            }

            const questionsHTML = data.questions_to_ask
                .map(question => `<li>${escapeHTML(question)}</li>`)
                .join("");

            talkreadyResult.innerHTML = `
                <h3>Your consultation preparation</h3>

                <h4>How to begin your conversation</h4>
                <p>${escapeHTML(data.opening_statement)}</p>

                <h4>Questions you may want to ask</h4>
                <ul>${questionsHTML}</ul>

                <h4>Your private consultation summary</h4>
                <p>You can edit this summary before using it.</p>
                <textarea id="editableTalkReadySummary">${escapeHTML(data.consultation_summary)}</textarea>

                <h4>Practise your conversation</h4>
                <p>${escapeHTML(data.practice_prompt)}</p>

                <p class="privacy-note">${escapeHTML(data.prototype_notice)}</p>
            `;

        } catch (error) {
            talkreadyResult.innerHTML = `
                <p class="error-message">
                    ${escapeHTML(error.message)}
                </p>
            `;
        } finally {
            submitButton.disabled = false;
            submitButton.textContent = "Prepare My Consultation";
        }
    });
}


// ==========================================
// MENOWELL PRIVATE CONNECT
// ==========================================

const providerList = document.getElementById("providerList");
const appointmentForm = document.getElementById("appointmentForm");
const appointmentProvider = document.getElementById("appointmentProvider");
const appointmentSpecialty = document.getElementById("appointmentSpecialty");
const consultationMode = document.getElementById("consultationMode");
const preferredLanguage = document.getElementById("preferredLanguage");
const appointmentResult = document.getElementById("appointmentResult");

let menowellProviders = [];

function privateConnectEscape(value) {
    return String(value ?? "").replace(/[&<>"']/g, character => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;"
    })[character]);
}

async function loadMenowellProviders() {
    try {
        const response = await fetch("/api/providers");

        if (!response.ok) {
            throw new Error("Could not retrieve providers.");
        }

        const data = await response.json();
        menowellProviders = data.providers || [];

        providerList.innerHTML = "";

        appointmentProvider.innerHTML =
            '<option value="">Select a facility</option>';

        menowellProviders.forEach(provider => {
            const card = document.createElement("div");
            card.className = "provider-card";

            card.innerHTML = `
                <span class="provider-tag">DEMO PROVIDER</span>
                <h3>${privateConnectEscape(provider.facility_name)}</h3>
                <p><strong>Location:</strong> ${privateConnectEscape(provider.area)}</p>
                <p><strong>Specialties:</strong> ${privateConnectEscape(provider.specialties.join(", "))}</p>
                <p><strong>Consultation:</strong> ${privateConnectEscape(provider.consultation_modes.join(", "))}</p>
                <p><strong>Languages:</strong> ${privateConnectEscape(provider.languages.join(", "))}</p>
                <p class="provider-fee">Indicative fee: AED ${privateConnectEscape(provider.indicative_fee_aed)}</p>
                <p>${privateConnectEscape(provider.description)}</p>
            `;

            providerList.appendChild(card);

            const option = document.createElement("option");
            option.value = provider.provider_id;
            option.textContent = provider.facility_name;

            appointmentProvider.appendChild(option);
        });

        if (menowellProviders.length === 0) {
            providerList.textContent = "No demonstration providers are currently available.";
        }

    } catch (error) {
        providerList.textContent =
            "We could not load the demonstration providers. Please refresh the page and try again.";
        console.error("Private Connect provider loading error:", error);
    }
}

function updateAppointmentOptions() {
    const selectedProvider = menowellProviders.find(
        provider => provider.provider_id === appointmentProvider.value
    );

    appointmentSpecialty.innerHTML =
        '<option value="">Select a specialty</option>';

    if (!selectedProvider) {
        consultationMode.value = "";
        preferredLanguage.value = "";
        return;
    }

    selectedProvider.specialties.forEach(specialty => {
        const option = document.createElement("option");
        option.value = specialty;
        option.textContent = specialty;
        appointmentSpecialty.appendChild(option);
    });

    consultationMode.innerHTML = '<option value="">Select mode</option>';

    selectedProvider.consultation_modes.forEach(mode => {
        const option = document.createElement("option");
        option.value = mode;
        option.textContent = mode;
        consultationMode.appendChild(option);
    });

    preferredLanguage.innerHTML = '<option value="">Select language</option>';

    selectedProvider.languages.forEach(language => {
        const option = document.createElement("option");
        option.value = language;
        option.textContent = language;
        preferredLanguage.appendChild(option);
    });
}

appointmentProvider.addEventListener("change", updateAppointmentOptions);

appointmentForm.addEventListener("submit", async function(event) {
    event.preventDefault();

    appointmentResult.className = "appointment-result";
    appointmentResult.textContent = "Submitting your demonstration request...";

    const requestData = {
        provider_id: appointmentProvider.value,
        specialty: appointmentSpecialty.value,
        consultation_mode: consultationMode.value,
        preferred_date: document.getElementById("preferredDate").value,
        preferred_time: document.getElementById("preferredTime").value,
        preferred_language: preferredLanguage.value,
        communication_preference:
            document.getElementById("communicationPreference").value
    };

    try {
        const response = await fetch("/api/appointment-requests", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(requestData)
        });

        const result = await response.json();

        if (!response.ok) {
            const detail = typeof result.detail === "string"
                ? result.detail
                : "Please check your selections and try again.";

            throw new Error(detail);
        }

        appointmentResult.className = "appointment-result success";

        
        appointmentResult.innerHTML = `
            <div class="confirmation-header">
                <div class="confirmation-icon">✓</div>
                <div>
                    <h3>Request submitted successfully</h3>
                    <p>Your consultation request has been recorded.</p>
                </div>
            </div>

            <div class="reference-highlight">
                <span>YOUR REFERENCE NUMBER</span>
                <strong>${privateConnectEscape(result.reference_number)}</strong>
            </div>

            <div class="confirmation-details">
                <div>
                    <span>Facility</span>
                    <strong>${privateConnectEscape(result.provider_name)}</strong>
                </div>
                <div>
                    <span>Specialty</span>
                    <strong>${privateConnectEscape(result.specialty)}</strong>
                </div>
                <div>
                    <span>Preferred date</span>
                    <strong>${privateConnectEscape(result.preferred_date)}</strong>
                </div>
                <div>
                    <span>Preferred time</span>
                    <strong>${privateConnectEscape(result.preferred_time)}</strong>
                </div>
            </div>

            <div class="confirmation-status">
                <span>Request status</span>
                <strong>${privateConnectEscape(result.request_status.toUpperCase())}</strong>
            </div>

            <div class="confirmation-disclaimer">
                ${privateConnectEscape(result.notice)}
            </div>
        `;

        appointmentForm.reset();
        updateAppointmentOptions();

    } catch (error) {
        appointmentResult.className = "appointment-result error";
        appointmentResult.textContent = error.message;
    }
});

// Set the earliest selectable appointment date to today.
const preferredDateInput = document.getElementById("preferredDate");

if (preferredDateInput) {
    const today = new Date();
    const localToday = [
        today.getFullYear(),
        String(today.getMonth() + 1).padStart(2, "0"),
        String(today.getDate()).padStart(2, "0")
    ].join("-");

    preferredDateInput.min = localToday;
}

// Load providers when the page opens.
loadMenowellProviders();


