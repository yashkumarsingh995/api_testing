from typing import List, Optional
from uuid import uuid4
from pydantic import Extra

from rctools.models.base import IdMixin, TimestampMixin, ReadiChargeBaseModel

from .users import SupportRequest


class JobNote(ReadiChargeBaseModel):
    note_id: Optional[str] # TODO, change to just id
    uid: str
    title: Optional[str]
    ticket_id: str
    note: str

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.note_id:
            self.note_id = str(uuid4())


class JobPhoto(ReadiChargeBaseModel):
    photo_id: Optional[str] # TODO, change to just id
    uid: str
    uri: str
    ticket_id: str
    caption: Optional[str]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.photo_id:
            self.photo_id = str(uuid4())


class CustomerHome(ReadiChargeBaseModel):
    address_1: str
    address_2: Optional[str]
    city: str
    state: str
    zip: str


class CustomerInfo(ReadiChargeBaseModel):
    class Config:
        extra = Extra.ignore

    given_name: Optional[str]
    family_name: Optional[str]
    name: Optional[str]  # first and last name combined


class JobScopeHome(ReadiChargeBaseModel):
    year_built: int
    rent_own: str
    panel_upgraded: Optional[str]
    nema_charger: Optional[str]


class JobScopeChargerLocations(ReadiChargeBaseModel):
    class Config:
        extra = Extra.allow  # XXX

    # doYouHaveExisting,
    # outletType,
    # insideOrOut,
    # upgradeOutlet,
    # whereInHome,
    # insideOrOutDetached,
    # hardScapedDetached,
    # exteriorDetached,
    # garageAttached,
    # wallLocation,
    # wallType,
    # material,
    # interiorMaterial,
    # electricPanel,
    # panelLocation,
    # sameFloor,
    # electricPanelType,
    # openBreakerSpaces,
    # breakerBrand,
    # connectedAppliance,
    # breakerSize,
    # circuits,
    # panelDistance,
    # installPreference,
    # note,
    # purchased,
    # purchasedTwo,
    # purchasedThree,
    # purchasedMake,
    # purchasedMakeTwo,
    # purchasedMakeThree,
    # purchasedModel,
    # proceed4,
    # proceed5,
    # proceed6,
    # proceed8,
    # proceed9,
    # proceed12,
    # proceed13,
    # proceed15,

class JobScopeChargers(ReadiChargeBaseModel):
    class Purchased(ReadiChargeBaseModel):
        id: Optional[str] # XXX need to distinguish between chargers [1,2,3]
        purchased: bool
        make: Optional[str]
        purchased_type: Optional[str]
        purchased_nema_type: Optional[str]
        purchased_hardwired_type: Optional[str]

    num_chargers: int
    purchased: List[Purchased]


class JobScopeMeasurement(ReadiChargeBaseModel):
    height: str
    length: str
    width: str
    note: Optional[str]


class JobScopeVehicles(ReadiChargeBaseModel):
    make: str
    model: str


class JobTier(ReadiChargeBaseModel):
    """Model representing the pricing tier a job is put into"""
    name: str
    description: str
    hours: List[int]  # range like, [5,7]
    num_chargers: int
    price: float


class JobScope(ReadiChargeBaseModel):
    home: Optional[JobScopeHome]
    chargers: Optional[JobScopeChargers]
    locations: Optional[List[JobScopeChargerLocations]]
    measurement: Optional[JobScopeMeasurement]
    tier: Optional[JobTier]
    vehicles: Optional[List[JobScopeVehicles]]


class JobTicket(TimestampMixin, ReadiChargeBaseModel):
    """Root job ticket model"""
    ticket_id: Optional[str]
    conversation_id: Optional[str]
    customer_id: str
    customer: Optional[CustomerInfo]
    installer_id: Optional[str]
    address: Optional[CustomerHome]
    job_scope: Optional[JobScope]
    # images: Optional[List[UploadFile]]  # https://stackoverflow.com/questions/69950072/pydantic-params-validation-with-file-upload
    notes: Optional[List[str]]
    photos: Optional[List[str]]
    support_request: Optional[SupportRequest]
    completed: Optional[bool]
    reschedule: Optional[bool]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.ticket_id:
            self.ticket_id = str(uuid4())
    

class JobsResponse(ReadiChargeBaseModel):
    jobs: Optional[List[JobTicket]] = []


class Reservation(IdMixin, TimestampMixin, ReadiChargeBaseModel):
    installer_id: Optional[str]
    customer_id: Optional[str]
    start_time: Optional[str]
    reservation_date: Optional[str]
    ticket_id: Optional[str]


class JobSchedule(TimestampMixin, ReadiChargeBaseModel):
    class Config:
        extra = Extra.ignore
    
    job_schedule_id: str = str(uuid4())
    installer_id: Optional[str]
    customer_id: Optional[str]
    start_time: Optional[str]
    job_schedule_date: Optional[str]
    ticket_id: Optional[str]
    duration: Optional[str]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.job_schedule_id:
            self.job_schedule_id = str(uuid4())
