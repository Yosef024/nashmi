import uuid
from datetime import date, datetime, timedelta
from enum import Enum
from typing import Dict, Optional

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field, validator

# --- Enums & Models ---

class ApplicationStatus(str, Enum):
    PENDING = "PENDING"
    ELIGIBILITY_FAILED = "ELIGIBILITY_FAILED"
    AWAITING_PAYMENT = "AWAITING_PAYMENT"
    PAID = "PAID"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"

class ApplicationBase(BaseModel):
    national_id: str = Field(..., pattern=r"^\d{10}$", description="10-digit Jordanian National ID")
    full_name: str
    date_of_birth: date

class ApplicationCreate(ApplicationBase):
    pass

class ApplicationResponse(BaseModel):
    application_id: uuid.UUID
    status: ApplicationStatus
    fee_amount: float = 50.00

class ApplicationStatusResponse(BaseModel):
    application_id: uuid.UUID
    status: ApplicationStatus
    payment_status: bool
    created_at: datetime
    estimated_completion_date: datetime

# --- Mock External Services ---

class ExternalMocks:
    @staticmethod
    def mock_gsb_verify_nationality(national_id: str) -> bool:
        # Returns True if ID starts with '9'
        return national_id.startswith('9')

    @staticmethod
    def mock_gsb_criminal_record_check(national_id: str) -> bool:
        # Returns True (Clean) unless ID ends in '00'
        return not national_id.endswith('00')

    @staticmethod
    def mock_efawateercom_payment_trigger(application_id: uuid.UUID, amount: float) -> str:
        return f"EFAW-{uuid.uuid4().hex[:8].upper()}"

# --- Business Logic Service ---

class VerificationService:
    @staticmethod
    def calculate_age(dob: date) -> int:
        today = date.today()
        return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

    @classmethod
    def verify_eligibility(cls, app_data: ApplicationCreate):
        # 1. Nationality Check
        if not ExternalMocks.mock_gsb_verify_nationality(app_data.national_id):
            return False, "Applicant must be of Jordanian nationality."

        # 2. Age Check
        if cls.calculate_age(app_data.date_of_birth) <= 10:
            return False, "Applicant must be older than 10 years."

        # 3. Criminal Record Check
        if not ExternalMocks.mock_gsb_criminal_record_check(app_data.national_id):
            return False, "Eligibility failed due to criminal record restrictions."

        return True, "Eligible"

# --- In-Memory Database ---

db: Dict[uuid.UUID, dict] = {}

# --- FastAPI App & Endpoints ---

app = FastAPI(title="Jordanian Passport Issuance Service (MVP)")

@app.post("/api/v1/passport/apply", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED)
async def apply(payload: ApplicationCreate):
    # Run Eligibility Logic
    is_eligible, reason = VerificationService.verify_eligibility(payload)
    
    if not is_eligible:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=reason
        )

    # Create Application Record
    app_id = uuid.uuid4()
    now = datetime.utcnow()
    
    application_record = {
        "id": app_id,
        "national_id": payload.national_id,
        "full_name": payload.full_name,
        "date_of_birth": payload.date_of_birth,
        "status": ApplicationStatus.AWAITING_PAYMENT,
        "payment_status": False,
        "created_at": now,
        "updated_at": now
    }
    
    db[app_id] = application_record
    
    return {
        "application_id": app_id,
        "status": application_record["status"],
        "fee_amount": 50.00
    }

@app.get("/api/v1/passport/status/{application_id}", response_model=ApplicationStatusResponse)
async def get_status(application_id: uuid.UUID):
    if application_id not in db:
        raise HTTPException(status_code=404, detail="Application not found")
    
    app_data = db[application_id]
    estimated_date = app_data["created_at"] + timedelta(days=7)
    
    return {
        "application_id": app_data["id"],
        "status": app_data["status"],
        "payment_status": app_data["payment_status"],
        "created_at": app_data["created_at"],
        "estimated_completion_date": estimated_date
    }

@app.post("/api/v1/passport/pay")
async def pay(application_id: uuid.UUID):
    if application_id not in db:
        raise HTTPException(status_code=404, detail="Application not found")
    
    app_data = db[application_id]
    
    if app_data["payment_status"]:
        return {"message": "Application already paid", "status": app_data["status"]}

    # Trigger Mock Payment Gateway
    transaction_ref = ExternalMocks.mock_efawateercom_payment_trigger(application_id, 50.00)
    
    # Update Status
    app_data["payment_status"] = True
    app_data["status"] = ApplicationStatus.PROCESSING
    app_data["updated_at"] = datetime.utcnow()
    
    return {
        "application_id": application_id,
        "payment_status": True,
        "status": app_data["status"],
        "transaction_reference": transaction_ref
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)