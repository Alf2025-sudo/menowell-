
import os
import json
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from app.database import initialise_database, get_connection
from datetime import datetime
from uuid import uuid4
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from openai import OpenAI
from pydantic import BaseModel, Field


# --------------------------------------------------
# 1. APPLICATION CONFIGURATION
# --------------------------------------------------

APP_DIR = Path(__file__).resolve().parent
PROJECT_DIR = APP_DIR.parent
STATIC_DIR = APP_DIR / "static"

load_dotenv(PROJECT_DIR / ".env")

AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "").strip().rstrip("/")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY", "").strip()
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT", "").strip()

app = FastAPI(
    title="Male Reproductive Health Early-Assessment Prototype",
    description="A privacy-conscious male reproductive health education and early-assessment prototype.",
    version="0.1.0",
)

@app.on_event("startup")
async def startup_event():
    initialise_database()


# --------------------------------------------------
# 2. REQUEST AND RESPONSE MODELS
# --------------------------------------------------

class AssessmentInput(BaseModel):
    age_group: Literal[
        "under_18",
        "18_29",
        "30_39",
        "40_49",
        "50_plus",
    ]

    main_goal: Literal[
        "general_prevention",
        "planning_pregnancy",
        "concerned_about_symptoms",
        "understand_test_results",
    ]

    sudden_severe_testicular_pain: bool = False
    significant_genital_swelling: bool = False
    fever_with_genital_or_urinary_symptoms: bool = False
    persistent_discomfort: bool = False
    urinary_or_genital_symptoms: bool = False
    previous_reproductive_condition: bool = False
    medication_concern: bool = False
    lifestyle_or_metabolic_concern: bool = False
    trying_to_conceive_without_success: bool = False
    wants_human_support: bool = False


class AssessmentResult(BaseModel):
    level: str
    title: str
    explanation: str
    next_steps: list[str]
    reasons: list[str]
    prototype_notice: str


class CompanionInput(BaseModel):
    question: str = Field(min_length=3, max_length=1500)


class CompanionResult(BaseModel):
    answer: str
    prototype_notice: str


class TalkReadyInput(BaseModel):
    concern: str = Field(
        min_length=5,
        max_length=1500,
        description="The health concern the user wants to discuss with a clinician.",
    )
    consultation_goal: str = Field(
        min_length=3,
        max_length=500,
        description="What the user hopes to achieve during the consultation.",
    )
    additional_context: str = Field(
        default="",
        max_length=1000,
        description="Optional non-identifying context relevant to the consultation.",
    )


class TalkReadyResult(BaseModel):
    opening_statement: str
    questions_to_ask: list[str]
    consultation_summary: str
    practice_prompt: str
    prototype_notice: str


class AppointmentRequestInput(BaseModel):
    provider_id: str = Field(min_length=3, max_length=20)
    specialty: str = Field(min_length=3, max_length=100)

    consultation_mode: str = Field(
        description="In-person or Online"
    )

    preferred_date: str = Field(
        description="Preferred appointment date in YYYY-MM-DD format"
    )

    preferred_time: str = Field(
        description="Preferred appointment time in HH:MM format"
    )

    preferred_language: str = Field(
        description="Preferred consultation language"
    )

    communication_preference: str = Field(
        description="Preferred response channel"
    )


class AppointmentRequestResult(BaseModel):
    reference_number: str
    provider_name: str
    specialty: str
    preferred_date: str
    preferred_time: str
    request_status: str
    notice: str

# =========================================
# MENOWELL PRIVATE CONNECT - DEMO PROVIDERS
# =========================================

DEMO_PROVIDERS = [
    {
        "provider_id": "MW001",
        "facility_name": "MenoWell Health Centre",
        "area": "Abu Dhabi City",
        "specialties": [
            "Urology",
            "Preventive Reproductive Health",
            "Men's Health"
        ],
        "consultation_modes": ["In-person", "Online"],
        "languages": ["English", "Arabic"],
        "indicative_fee_aed": 350,
        "description": (
            "A fictional demonstration facility for general "
            "men's reproductive health and urology consultations."
        ),
        "demo_only": True
    },
    {
        "provider_id": "MW002",
        "facility_name": "Horizon Men's Wellness Clinic",
        "area": "Al Reem Island",
        "specialties": [
            "Andrology",
            "Men's Health",
            "Preventive Health"
        ],
        "consultation_modes": ["In-person", "Online"],
        "languages": ["English", "Arabic"],
        "indicative_fee_aed": 400,
        "description": (
            "A fictional demonstration facility focused on "
            "men's wellness and andrology consultations."
        ),
        "demo_only": True
    },
    {
        "provider_id": "MW003",
        "facility_name": "Pearl Fertility Support Centre",
        "area": "Khalifa City",
        "specialties": [
            "Reproductive Medicine",
            "Preconception Support",
            "Fertility Assessment"
        ],
        "consultation_modes": ["In-person", "Online"],
        "languages": ["English", "Arabic"],
        "indicative_fee_aed": 450,
        "description": (
            "A fictional demonstration facility for reproductive "
            "health and preconception support."
        ),
        "demo_only": True
    },
    {
        "provider_id": "MW004",
        "facility_name": "Oasis Health and Counselling Centre",
        "area": "Al Reem Island",
        "specialties": [
            "Preconception Counselling",
            "Health Education",
            "Wellness Counselling"
        ],
        "consultation_modes": ["In-person", "Online"],
        "languages": ["English", "Arabic"],
        "indicative_fee_aed": 250,
        "description": (
            "A fictional demonstration facility for confidential "
            "health education and preconception counselling."
        ),
        "demo_only": True
    }
]


# =========================================
# PRIVATE CONNECT - PROVIDER DIRECTORY API
# =========================================

@app.get("/api/providers")
async def get_demo_providers():
    return {
        "network_type": "demonstration",
        "notice": (
            "All providers shown are fictional demonstration "
            "records. They are not real healthcare facilities."
        ),
        "providers": DEMO_PROVIDERS
    }


# =========================================
# PRIVATE CONNECT - APPOINTMENT REQUEST API
# =========================================

@app.post(
    "/api/appointment-requests",
    response_model=AppointmentRequestResult
)
async def create_appointment_request(data: AppointmentRequestInput):

    # 1. Find the selected demonstration provider
    provider = next(
        (
            item for item in DEMO_PROVIDERS
            if item["provider_id"] == data.provider_id
        ),
        None
    )

    if provider is None:
        raise HTTPException(
            status_code=404,
            detail="Selected demonstration provider was not found."
        )

    # 2. Validate the selected specialty
    if data.specialty not in provider["specialties"]:
        raise HTTPException(
            status_code=400,
            detail="The selected specialty is not offered by this provider."
        )

    # 3. Validate consultation mode
    if data.consultation_mode not in provider["consultation_modes"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid consultation mode."
        )

    # 4. Validate preferred language
    if data.preferred_language not in provider["languages"]:
        raise HTTPException(
            status_code=400,
            detail="The selected language is not available."
        )

    # 5. Validate date and time formats
    try:
        appointment_date = datetime.strptime(
            data.preferred_date, "%Y-%m-%d"
        ).date()

        datetime.strptime(
            data.preferred_time, "%H:%M"
        )

    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Enter a valid date (YYYY-MM-DD) and time (HH:MM)."
        )

    if appointment_date < datetime.now().date():
        raise HTTPException(
            status_code=400,
            detail="The preferred appointment date cannot be in the past."
        )

    # 6. Validate communication preference
    allowed_preferences = [
        "Email",
        "Phone call",
        "SMS",
        "In-app notification"
    ]

    if data.communication_preference not in allowed_preferences:
        raise HTTPException(
            status_code=400,
            detail="Invalid communication preference."
        )

    # 7. Generate a unique demonstration reference
    reference_number = f"MW-{uuid4().hex[:8].upper()}"

    # 8. Save the request in SQLite
    connection = get_connection()

    try:
        connection.execute(
            """
            INSERT INTO appointment_requests (
                reference_number,
                provider_id,
                provider_name,
                specialty,
                consultation_mode,
                preferred_date,
                preferred_time,
                preferred_language,
                communication_preference,
                request_status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                reference_number,
                provider["provider_id"],
                provider["facility_name"],
                data.specialty,
                data.consultation_mode,
                data.preferred_date,
                data.preferred_time,
                data.preferred_language,
                data.communication_preference,
                "pending"
            )
        )

        connection.commit()

    except Exception:
        connection.rollback()

        raise HTTPException(
            status_code=500,
            detail="Unable to save the appointment request."
        )

    finally:
        connection.close()

    # 9. Return confirmation to the user
    return AppointmentRequestResult(
        reference_number=reference_number,
        provider_name=provider["facility_name"],
        specialty=data.specialty,
        preferred_date=data.preferred_date,
        preferred_time=data.preferred_time,
        request_status="pending",
        notice=(
            "This is a demonstration appointment request. "
            "No real healthcare provider has received this request, "
            "and no appointment has been booked or confirmed."
        )
    )


@app.get("/api/admin/appointment-requests")
async def get_all_appointment_requests():
    """
    Demonstration admin endpoint.
    Retrieves appointment requests stored in the local SQLite database.
    """

    connection = get_connection()

    try:
        rows = connection.execute("""
            SELECT
                id,
                reference_number,
                provider_id,
                provider_name,
                specialty,
                consultation_mode,
                preferred_date,
                preferred_time,
                preferred_language,
                communication_preference,
                request_status,
                created_at
            FROM appointment_requests
            ORDER BY created_at DESC
        """).fetchall()

        requests = [dict(row) for row in rows]

        return {
            "total_requests": len(requests),
            "requests": requests,
            "notice": "Demonstration administrative data. This endpoint is not protected by administrator authentication."
        }

    finally:
        connection.close()


class AppointmentStatusUpdate(BaseModel):
    status: str


@app.patch("/api/admin/appointment-requests/{reference_number}")
async def update_appointment_status(
    reference_number: str,
    update: AppointmentStatusUpdate
):
    """
    Updates the status of a demonstration appointment request.
    """

    allowed_statuses = {
        "pending",
        "reviewed",
        "completed",
        "cancelled"
    }

    new_status = update.status.lower().strip()

    if new_status not in allowed_statuses:
        raise HTTPException(
            status_code=400,
            detail="Invalid status. Choose pending, reviewed, completed or cancelled."
        )

    connection = get_connection()

    try:
        cursor = connection.execute(
            """
            UPDATE appointment_requests
            SET request_status = ?
            WHERE reference_number = ?
            """,
            (new_status, reference_number)
        )

        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=404,
                detail="Appointment request not found."
            )

        connection.commit()

        return {
            "success": True,
            "reference_number": reference_number,
            "request_status": new_status,
            "message": "Appointment request status updated successfully."
        }

    finally:
        connection.close()



# --------------------------------------------------
# 3. GENERAL CONFIGURATION ENDPOINTS
# --------------------------------------------------

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "application": "Male Reproductive Health Early-Assessment Prototype",
    }


@app.get("/api/azure-status")
def azure_configuration_status():
    return {
        "endpoint_configured": bool(AZURE_OPENAI_ENDPOINT),
        "api_key_configured": bool(AZURE_OPENAI_API_KEY),
        "deployment_configured": bool(AZURE_OPENAI_DEPLOYMENT),
    }


# --------------------------------------------------
# 4. EARLY-ASSESSMENT ENGINE
# --------------------------------------------------

@app.post("/api/assess", response_model=AssessmentResult)
def assess_reproductive_health(data: AssessmentInput):

    if data.age_group == "under_18":
        return AssessmentResult(
            level="general_information",
            title="This service is designed for adults",
            explanation=(
                "This prototype is intended for adults. "
                "Please speak with a qualified healthcare professional "
                "or an appropriate trusted adult for support."
            ),
            next_steps=[
                "Seek guidance from a qualified healthcare professional."
            ],
            reasons=["The submitted age group is under 18."],
            prototype_notice=(
                "This is an experimental prototype, not a clinical assessment."
            ),
        )

    # Safety-oriented symptom routing comes first.
    if (
        data.sudden_severe_testicular_pain
        or data.significant_genital_swelling
        or data.fever_with_genital_or_urinary_symptoms
    ):
        return AssessmentResult(
            level="urgent",
            title="Urgent medical assessment recommended",
            explanation=(
                "Some reported symptoms can require prompt or emergency "
                "medical assessment. Do not delay care while using this tool."
            ),
            next_steps=[
                "Seek urgent medical assessment now.",
                "If pain is sudden or severe, attend an emergency department immediately.",
            ],
            reasons=[
                "One or more urgent symptom indicators were selected."
            ],
            prototype_notice=(
                "This prototype cannot diagnose or rule out a medical emergency."
            ),
        )

    if (
        data.persistent_discomfort
        or data.urinary_or_genital_symptoms
    ):
        return AssessmentResult(
            level="prompt_clinical_review",
            title="Consider a clinical consultation",
            explanation=(
                "Persistent discomfort or urinary and genital symptoms "
                "deserve assessment by a qualified healthcare professional."
            ),
            next_steps=[
                "Arrange a clinical consultation.",
                "Describe when the symptoms started and how they have changed.",
            ],
            reasons=[
                "Persistent discomfort or urinary/genital symptoms were reported."
            ],
            prototype_notice=(
                "This prototype does not provide a medical diagnosis."
            ),
        )

    reasons = []

    if data.previous_reproductive_condition:
        reasons.append("A previous reproductive health condition was reported.")

    if data.medication_concern:
        reasons.append("A medication-related concern was reported.")

    if data.lifestyle_or_metabolic_concern:
        reasons.append("A lifestyle or metabolic health concern was reported.")

    if data.trying_to_conceive_without_success:
        reasons.append("Difficulty conceiving was reported.")

    if data.wants_human_support:
        reasons.append("Human healthcare support was requested.")

    if data.main_goal == "planning_pregnancy":
        reasons.append("Preconception guidance was requested.")

    if data.main_goal == "understand_test_results":
        reasons.append("Help understanding test results was requested.")

    if reasons:
        return AssessmentResult(
            level="routine_discussion",
            title="A healthcare discussion may be helpful",
            explanation=(
                "Your responses suggest that a routine discussion with "
                "a qualified healthcare professional could help address "
                "your concerns and identify appropriate next steps."
            ),
            next_steps=[
                "Consider arranging a routine healthcare consultation.",
                "Discuss relevant medical history and current concerns.",
                "For preconception planning, discuss health optimization "
                "with a qualified professional.",
            ],
            reasons=reasons,
            prototype_notice=(
                "This is an early-assessment prototype, not a fertility test "
                "or clinical diagnosis."
            ),
        )

    return AssessmentResult(
        level="general_information",
        title="Explore preventive reproductive health",
        explanation=(
            "Your responses do not identify a specific concern in this "
            "limited questionnaire. Preventive health information may "
            "still be useful."
        ),
        next_steps=[
            "Learn about general reproductive health.",
            "Maintain healthy lifestyle habits.",
            "Discuss preventive screening with a healthcare professional "
            "when appropriate.",
        ],
        reasons=["No specific concern was identified by this questionnaire."],
        prototype_notice=(
            "This prototype cannot establish that someone is medically healthy "
            "or fertile."
        ),
    )


# --------------------------------------------------
# 5. AZURE OPENAI CLIENT
# --------------------------------------------------

def get_azure_client():

    if not all([
        AZURE_OPENAI_ENDPOINT,
        AZURE_OPENAI_API_KEY,
        AZURE_OPENAI_DEPLOYMENT,
    ]):
        raise HTTPException(
            status_code=503,
            detail="The AI Companion is not currently configured.",
        )

    return OpenAI(
        api_key=AZURE_OPENAI_API_KEY,
        base_url=f"{AZURE_OPENAI_ENDPOINT}/openai/v1/",
        timeout=30.0,
        max_retries=1,
    )


# --------------------------------------------------
# 6. AI COMPANION
# --------------------------------------------------

@app.post("/api/companion", response_model=CompanionResult)
def companion(data: CompanionInput):

    client = get_azure_client()

    system_instructions = """
You are the educational AI Companion in a male reproductive
health early-assessment prototype.

Your role:
- Provide clear, respectful, evidence-informed general health education.
- Explain male reproductive and preconception health concepts.
- Encourage appropriate conversations with qualified healthcare professionals.
- Use accessible language and a culturally sensitive, non-judgmental tone.

Strict limitations:
- Do not diagnose medical conditions.
- Do not determine or predict an individual's fertility.
- Do not prescribe medication or recommend treatment.
- Do not interpret individual laboratory or semen analysis results.
- Do not claim that a person is medically healthy based on limited information.
- Do not request names, addresses, identification numbers, or other personal identifiers.
- Do not encourage users to share identifiable medical information.

Safety:
- Sudden or severe testicular pain requires immediate emergency assessment.
- Significant genital swelling, or fever with genital or urinary symptoms,
  warrants urgent medical assessment.
- Never suggest that a user delay urgent care to continue chatting.

If asked to interpret individual medical results, explain that a
qualified clinician should interpret them in context.

Keep answers concise, supportive, and educational.
"""

    try:
        response = client.responses.create(
            model=AZURE_OPENAI_DEPLOYMENT,
            instructions=system_instructions,
            input=data.question,
            max_output_tokens=350,
        )

        answer = response.output_text

        if not answer:
            raise HTTPException(
                status_code=502,
                detail="The AI Companion returned an empty response.",
            )

        return CompanionResult(
            answer=answer,
            prototype_notice=(
                "This AI Companion provides general educational information "
                "only. It is not a medical professional and does not provide "
                "diagnosis or treatment."
            ),
        )

    except HTTPException:
        raise

    except Exception:
        raise HTTPException(
            status_code=502,
            detail=(
                "The AI Companion could not complete your request. "
                "Please try again later."
            ),
        )


@app.post("/api/talkready", response_model=TalkReadyResult)
async def generate_talkready(data: TalkReadyInput):
    """
    Helps users prepare for a reproductive-health consultation.
    Does not diagnose, prescribe, or automatically share information.
    """

    client = get_azure_client()

    if client is None:
        raise HTTPException(
            status_code=503,
            detail="The AI service is currently unavailable.",
        )

    system_prompt = """
    You are MenoWell TalkReady, a respectful and culturally sensitive
    consultation preparation assistant.

    Your role is to help adult users prepare to discuss male reproductive
    health and preconception concerns with qualified healthcare professionals.

    IMPORTANT SAFETY RULES:

    1. Do not diagnose medical conditions.
    2. Do not predict whether someone is fertile or infertile.
    3. Do not prescribe medication or recommend treatment.
    4. Do not independently interpret individual laboratory or semen analysis results.
    5. Encourage users to discuss clinical concerns and test results with
       qualified healthcare professionals.
    6. If the user describes sudden severe testicular pain, significant
       genital swelling, or fever with genital or urinary symptoms, advise
       urgent medical assessment. Do not allow consultation preparation
       to delay urgent care.
    7. Do not request names, phone numbers, addresses, identification
       numbers, or other identifying information.
    8. Use respectful, non-judgmental, accessible language.
    9. Do not assume the user's religion, culture, marital status, or
       personal values.
    10. Make clear that the user controls what they choose to share
        with their healthcare professional.

    Return ONLY a valid JSON object containing these five fields:

    {
      "opening_statement": "A short suggested statement the user can
      use to begin their consultation.",
      "questions_to_ask": [
        "A relevant question for the clinician",
        "Another relevant question"
      ],
      "consultation_summary": "A concise first-person summary the user
      can review and edit before their consultation.",
      "practice_prompt": "A gentle suggestion for practising the
      conversation with a healthcare professional.",
      "prototype_notice": "A brief reminder that this tool prepares
      users for consultations and does not replace medical advice."
    }

    Provide approximately 4 to 6 useful questions.
    Keep the opening statement natural and concise.
    Do not invent symptoms, medical history, or test results.
    11. Do not assume how long the user has been trying to conceive.
    Do not describe the user as infertile or imply a fertility problem
    has been established unless the user explicitly states this as
    a clinician-confirmed diagnosis.
    12. Preserve the user's original meaning. Do not add facts, symptoms,
    diagnoses, or medical history that the user did not provide.
    """

    user_message = f"""
    User's concern:
    {data.concern}

    Consultation goal:
    {data.consultation_goal}

    Additional context:
    {data.additional_context or "Not provided"}

    Prepare the consultation guidance using the required JSON structure.
    """

    try:
        response = client.responses.create(
            model=AZURE_OPENAI_DEPLOYMENT,
            instructions=system_prompt,
            input=user_message,
            max_output_tokens=1200,
        )

        raw_output = response.output_text

        result_data = json.loads(raw_output)

        return TalkReadyResult(**result_data)

    except json.JSONDecodeError:
        raise HTTPException(
            status_code=502,
            detail="The AI service returned an unexpected response. Please try again.",
        )

    except Exception:
        raise HTTPException(
            status_code=502,
            detail="TalkReady could not generate your consultation preparation. Please try again.",
        )



# --------------------------------------------------
# 7. FRONTEND FILES
# --------------------------------------------------

if STATIC_DIR.exists():
    app.mount(
        "/static",
        StaticFiles(directory=STATIC_DIR),
        name="static",
    )

@app.get("/", include_in_schema=False)
async def homepage():
    from fastapi.responses import FileResponse

    index_file = STATIC_DIR / "index.html"

    if not index_file.exists():
        raise HTTPException(
            status_code=404,
            detail="Homepage file not found.",
        )

    return FileResponse(index_file)
