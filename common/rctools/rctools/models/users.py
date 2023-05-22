from typing import Dict, List, Optional
from uuid import uuid4

from pydantic import Extra
from rctools.models.base import ReadiChargeBaseModel
from rctools.models.messages import Message


class AdminUser(ReadiChargeBaseModel):
    """Cognito admin user"""
    class Config:
        extra = Extra.ignore

    @staticmethod
    def strip_cognito_fields(data):
        fields = ['sub', 'email', 'phone_number', 'given_name', 'family_name', 'name', 'password']
        for f in fields:
            if f in data:
                del data[f]

    sub: Optional[str]
    given_name: Optional[str]
    family_name: Optional[str]
    name: Optional[str]  # first and last name combined
    email: str
    phone_number: str


class Admin(ReadiChargeBaseModel):
    """
    Admin user object that inherits the Cognito user values and allows any other other values
    to be attached and stored in S3
    """
    class Config:
        # Allow any extra user data to be stored in S3
        extra = Extra.allow

    name: Optional[str]  # first and last name combined
    email: str
    phone_number: str
    company_id: Optional[str]
    id: Optional[str]


class CompanyAdminUser(ReadiChargeBaseModel):
    """Cognito admin user"""
    class Config:
        extra = Extra.ignore

    @staticmethod
    def strip_cognito_fields(data):
        fields = ['sub', 'email', 'phone_number', 'given_name', 'family_name', 'name', 'password']
        for f in fields:
            if f in data:
                del data[f]
    
    sub: Optional[str]  # not present before an InstallerUser is first created
    given_name: Optional[str]
    family_name: Optional[str]
    name: Optional[str]  # first and last name combined
    email: str
    phone_number: str


class CompanyAdmin(ReadiChargeBaseModel):
    """
    Company admin user object that inherits the Cognito user values and allows any other other values
    to be attached and stored in S3
    """
    class Config:
        # Allow any extra user data to be stored in S3
        extra = Extra.allow

    def set_company_id(self, new_id):
        self.company_id = new_id

    def set_id(self, id):
        self.id = id
    
    name: Optional[str]  # first and last name combined
    email: str
    phone_number: str
    company_id: Optional[str]
    id: Optional[str]

class CustomerUser(ReadiChargeBaseModel):
    """Cognito customer user"""
    class Config:
        extra = Extra.ignore

    @staticmethod
    def strip_cognito_fields(data):
        fields = ['sub', 'email', 'phone_number', 'given_name', 'family_name', 'name', 'password']
        for f in fields:
            if f in data:
                del data[f]
    
    sub: Optional[str]  # not present before an InstallerUser is first created
    given_name: Optional[str]
    family_name: Optional[str]
    name: Optional[str]  # first and last name combined
    email: str
    phone_number: str


class Customer(CustomerUser):
    """
    Customer user object that inherits the Cognito user values and allows any other other values
    to be attached and stored in S3
    """
    class Config:
        # Allow any extra user data to be stored in S3
        extra = Extra.allow

    email: Optional[str]
    phone_number: Optional[str]


class Day(ReadiChargeBaseModel):
    start: int = 700
    end: int = 1900
    available: bool = True


class Scheduling(ReadiChargeBaseModel):
    """
    Model for scheduling for installers. Weekday keys contain
    hours of availability in 24 hr time. For example, 9AM to 5PM
    availability would be saved as [900, 1700].

    Exceptions contain similar int sets with a YYYYmmdd date string
    as the date.
    """
    # TODO adding optional to get messages working during customer onboarding
    class Config:
        extra = Extra.ignore

    mon: Optional[Day] 
    tue: Optional[Day] 
    wed: Optional[Day] 
    thu: Optional[Day] 
    fri: Optional[Day] 
    sat: Optional[Day] 
    sun: Optional[Day] 
    exceptions: Optional[Dict[str, Day]]


class BackgroundCheck(ReadiChargeBaseModel):
    """Background check model for installers"""
    report_key: Optional[str]
    status: Optional[str]


class License(ReadiChargeBaseModel):
    """License model for installers"""
    class Config:
        extra = Extra.allow
    licenseNumber: Optional[str]


class ServiceArea(ReadiChargeBaseModel):
    """Service area model for installers"""
    class Config:
        extra = Extra.allow
    radius: str


class StripeAccount(ReadiChargeBaseModel):
    """Stripe information for installers"""
    class Config:
        extra = Extra.ignore

    connected_account_id: Optional[str]
    refresh_token: Optional[str]


class InstallerUser(ReadiChargeBaseModel):
    """Cognito installer user"""
    class Config:
        extra = Extra.ignore

    @staticmethod
    def strip_cognito_fields(data):
        fields = ['sub', 'email', 'phone_number', 'given_name', 'family_name', 'name', 'password']
        for f in fields:
            if f in data:
                del data[f]

    sub: Optional[str]  # not present before an InstallerUser is first created
    given_name: Optional[str]
    family_name: Optional[str]
    name: Optional[str]  # first and last name combined
    email: str
    phone_number: str


class Installer(InstallerUser):
    """
    Installer user object that inherits the Cognito user values and allows any other other values
    to be attached and stored in S3
    """
    class Config:
        # Allow any extra user data to be stored in S3
        extra = Extra.allow

    def get_first_name(self):
        """Returns the installers first name, if defined, otherwise it guesses it from full name"""
        if self.given_name:
            return self.given_name
        return self.name.split(' ')[0]
    
    email: Optional[str]
    phone_number: Optional[str]
    background_check: Optional[BackgroundCheck]
    license: Optional[License]
    scheduling: Optional[Scheduling]
    serviceArea: Optional[ServiceArea]  # TODO fix case
    payments: Optional[StripeAccount]


class FileUploadResponse(ReadiChargeBaseModel):
    path: str


class InstallerImage(ReadiChargeBaseModel):
    image_id: str = str(uuid4())
    uid: str
    uri: str
    type: str

class NewCustomerResponse(ReadiChargeBaseModel):
    user_id: Optional[str]
    id: Optional[str]


class NewInstallerResponse(ReadiChargeBaseModel):
    # class Config:
    #     # Allow any extra user data to be stored in S3
    #     extra = Extra.ignore
    id: Optional[str]
    user_id: Optional[str]
    temp_password: Optional[str]
    

class SupportRequest(ReadiChargeBaseModel):
    uid: str
    type: str
    title: str
    desc: str
