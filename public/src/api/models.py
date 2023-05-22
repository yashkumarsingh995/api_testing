"""Response and request models for FastAPI"""
from pydantic.fields import Optional
from typing import List

from rctools.models import CompanyInstaller, ReadiChargeBaseModel


class HealthResponse(ReadiChargeBaseModel):
    GIT_HASH: str


class CompanyContactInfo(ReadiChargeBaseModel):
    email: str
    phone: Optional[str]


class InstallerCodeResponse(ReadiChargeBaseModel):
    contact_info: Optional[CompanyContactInfo]
    installer: Optional[CompanyInstaller]
    valid: bool = False


class InstallersInYourAreaResponse(ReadiChargeBaseModel):
    installers_found: bool = False


class QualificationResponseCurrentRate(ReadiChargeBaseModel):
    annual: int = 0
    per_job: int = 0


class QualificationResponse(ReadiChargeBaseModel):
    current_rate: QualificationResponseCurrentRate = QualificationResponseCurrentRate()
    reasons: List[str] = []
    qualify: bool = False


class QualificationUserData(ReadiChargeBaseModel):
    first_name: str
    last_name: str
    email: str
    state: str
    # The follow values needs to be True to qualify, but we want to process disqualifications rather than rejecting them for required values
    licensed: Optional[bool]
    insured: Optional[bool]
    agree_to_background_check: Optional[bool]


class NewCompanyAdminRequest(ReadiChargeBaseModel):
    given_name: str
    family_name: str
    password: str
    email: str
    company: str
    phone_number: str
    address_one: str
    address_two: str
    city: str
    state: str
    zip: str


class NewCompanyAdminResponse(ReadiChargeBaseModel):
    company_id: str
    user_id: str
