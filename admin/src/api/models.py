"""Response and request models for FastAPI"""

from datetime import datetime
from typing import List, Optional
from fastapi import Query

from pydantic import BaseModel, Extra

from rctools.models.jobs import JobTicket


class ReadiChargeModel(BaseModel):
    # 'forbid' will cause validation to fail if extra attributes are included
    class Config:
        extra = Extra.forbid  # or just 'forbid'


class HealthResponse(ReadiChargeModel):
    GIT_HASH: str


# Dashboard Model
class DashboardEntry(ReadiChargeModel):
    key: str
    value: int


class DashboardCard(ReadiChargeModel):
    entries: List[DashboardEntry] = []
    link: Optional[str]
    title: str

    def add_entries(self, entries: dict):
        for k, v in entries.items():
            self.entries.append(DashboardEntry(key=k, value=v))


# Installers Model
class InstallersAccount(ReadiChargeModel):
    email: str
    phone_number: str
    address1: str
    address2: str
    city: str
    companyName: str
    state: str
    region: str


class InstallerCompany(ReadiChargeModel):
    id: str
    experience: int
    name: str
    type: str
    jobs: int
    state: str
    rating: int
    email: str
    phone_number: str
    address1: str
    address2: str
    city: str
    companyName: str
    region: int


class InstallersResponse(ReadiChargeModel):
    # Username: str
    id: Optional[str]
    sub: Optional[str] = None
    email: Optional[str]
    name: Optional[str]
    jobs: Optional[int] = None
    type: Optional[str] = None
    state: Optional[str]
    rating: Optional[int] = None
    region: Optional[str]
    referred: Optional[bool] = False
    preferred: Optional[bool] = False
    phone_number: Optional[str]
    email_verified: Optional[bool] = False
    address1: Optional[str]
    address2: Optional[str] = None
    city: Optional[str]
    company_id: Optional[str]
    companyName: Optional[str]
    companyInstallers: Optional[List[InstallerCompany]]
    account: InstallersAccount


class NewInstaller(BaseModel):
    sub: Optional[str]
    email: str
    first_name: str
    last_name: str
    jobs: int = Query(default=0)
    type: str = Query(default='residential')
    state: str
    rating: int = Query(default=3)
    region: str
    referred: bool = Query(default=False)
    preferred: bool = Query(default=False)
    phone_number: str
    email_verified: bool = Query(default=False)
    address1: str
    address2: str
    city: str
    companyName: str
    companyInstallers: Optional[List[InstallerCompany]]
    account: InstallersAccount


class UserGroup(ReadiChargeModel):
    GroupName: str
    UserPoolId: str
    Description: str
    LastModifiedDate: datetime
    CreationDate: datetime


# Users Model
class UsersResponse(ReadiChargeModel):
    Username: str
    id: str
    sub: str
    email: str
    name: str
    phone_number: str
    groups: List[UserGroup]
    UserCreateDate: datetime
    UserLastModifiedDate: datetime
    Enabled: bool
    UserStatus: str
    email_verified: Optional[bool] = False
    phone_number_verified: Optional[str] = 'No'


# JobTickets Model
class JobTicketsResponse(ReadiChargeModel):
    class Config:
        extra = Extra.allow

    # id: str
    # job_number: str
    # date: str
    # time: str
    # installer: str
    # customer: str
    # address: str
    # region: str


# Reports Model
class ReportsResponse(ReadiChargeModel):
    id: int
    type: str
    date: str
    time: str
    user: str


# Companies Models
class InstallerCodeResponse(ReadiChargeModel):
    code: str