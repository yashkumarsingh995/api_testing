

class CustomerNotAuthorizedToEditTicket(Exception):
    """Base class for other exceptions"""
    pass


class CustomerNotAuthorizedToEditSchedule(Exception):
    """Base class for other exceptions"""
    pass


class ReservationConflict(Exception):
    """Base class for other exceptions"""
    pass


class InstallerNotAuthorizedToEditTicket(Exception):
    """Base class for other exceptions"""
    pass


class InstallerNotAuthorizedToEditSchedule(Exception):
    """Base class for other exceptions"""
    pass


class UserNotAuthorizedToListTickets(Exception):
    """Base class for other exceptions"""
    pass


class UserNotAuthorizedToEditInstaller(Exception):
    """Base class for other exceptions"""
    pass
