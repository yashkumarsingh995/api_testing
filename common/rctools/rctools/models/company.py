from pydantic import Extra
from typing import Optional

from rctools.models.base import ReadiChargeBaseModel, IdMixin, TimestampMixin


class Company(ReadiChargeBaseModel, IdMixin):
    name: str
    address_1: str
    address_2: Optional[str]
    email: str
    phone_number: str
    city: str
    state: str
    zip: str
    # a company object can be created without this, even though all company objects should have one
    account_owner_id: Optional[str]

    def set_company_id(self, new_id):
        self.id = new_id

    def set_account_owner(self, owner_id):
        self.account_owner_id = owner_id


class CompanyInstaller(TimestampMixin, ReadiChargeBaseModel):
    """Company installer code object"""
    class Config:
        extra = Extra.ignore

    code: str
    company_id: Optional[str]  # can be provided as a URL param TODO array of company_id's seems possible
    name: Optional[str]
    first_name: str
    last_name: str
    email: str
    phone_number: str
    user_created: Optional[bool]
    address_1: Optional[str]
    address_2: Optional[str]
    state: Optional[str]
    zip: Optional[str]
    city: Optional[str]
    company: Optional[Company]
