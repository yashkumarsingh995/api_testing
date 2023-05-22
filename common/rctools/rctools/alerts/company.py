"""
Helper functions to create different kinds of alerts for company admins.
"""
from rctools.models import Alert
from rctools.utils import as_currency

def create_certification_in_progress_alert(user_id: str) -> Alert:
    """Creates an alert when an installers certification has begun"""
    return Alert(**{
        'type': Alert.AlertTypes.notification,
        'title': 'Certification in Progress',
        'content': 'Your certification is in progress!',
        'uid': user_id,
    })

def create_certification_approved_alert(user_id: str) -> Alert:
    """Creates an alert when an installers certification has been approved"""
    return Alert(**{
        'type': Alert.AlertTypes.notification,
        'title': 'Certification Approved',
        'content': 'Your certification has been approved! Your can now activate your schedule.',
        'uid': user_id,
    })

def create_certification_rejected_alert(user_id: str) -> Alert:
    """Creates an alert when an installers certification is rejected"""
    return Alert(**{
        'type': Alert.AlertTypes.warning,
        'title': 'Certification Rejected',
        'content': 'Your certification has not been approved at this time. See email for details.',
        'uid': user_id,
    })

def create_onboarding_setup_incomplete(user_id: str, user_first_name: str, user_last_name: str) -> Alert:
    """1x a day for 3 consecutive days after account created, if setup is not completed; then every 7 days for 3 weeks"""
    return Alert(**{
        'type': Alert.AlertTypes.warning,
        'title': 'Certification Rejected',
        'content': 'Your certification has not been approved at this time. See email for details.',
        'content': f'{user_first_name} {user_last_name} has not completed their account setup.',
        'uid': user_id,
    })
