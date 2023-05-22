"""
Helper functions to create different kinds of alerts for installers.

Note, some notifications like:

 - "account setup incomplete", 
 - "account has been paused", 
 - "reminder to unpause"

make more sense to handle
entirely client-side (rather than running timed jobs on the server to send out alerts)
"""
from rctools.models import Alert
from rctools.utils import as_currency


def create_bond_expires_reminder(user_id: str, days: int) -> Alert:
    """Creates an alert reminder user of an expiring bond"""
    days_str = 'day' if days == 1 else 'days'
    return Alert(**{
        'type': Alert.AlertTypes.warning,
        'title': 'Bond Expiring',
        'content': f'Your bond expires in {days} {days_str}. Your account will be paused if your bond expires. Go to Account Settings to update.',
        'uid': user_id,
    })


def create_background_check_approved_alert(user_id: str) -> Alert:
    """Creates an alert when an installers background check has been approved"""
    return Alert(**{
        'type': Alert.AlertTypes.notification,
        'title': 'Background Check Approved',
        'content': 'Your background check has been approved! You can now activate your schedule.',
        'uid': user_id,
    })


def create_background_check_in_progress_alert(user_id: str) -> Alert:
    """Creates an alert when an installers background check has begun"""
    return Alert(**{
        'type': Alert.AlertTypes.notification,
        'title': 'Background Check in Progress',
        'content': 'Your background check is in progress!',
        'uid': user_id,
    })


def create_background_check_rejected_alert(user_id: str) -> Alert:
    """Creates an alert when an installers background check is rejected"""
    return Alert(**{
        'type': Alert.AlertTypes.warning,
        'title': 'Background Check Rejected',
        'content': 'Your background check has not been approved at this time. See email for details.',
        'uid': user_id,
    })


def create_certification_approved_alert(user_id: str) -> Alert:
    """Creates an alert when an installers certification has been approved"""
    return Alert(**{
        'type': Alert.AlertTypes.notification,
        'title': 'Certification Approved',
        'content': 'Your certification has been approved! You can now activate your schedule.',
        'uid': user_id,
    })


def create_certification_in_progress_alert(user_id: str) -> Alert:
    """Creates an alert when an installers certification has begun"""
    return Alert(**{
        'type': Alert.AlertTypes.notification,
        'title': 'Certification in Progress',
        'content': 'Your certification is in progress!',
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


def create_installer_new_job_alert(user_id: str) -> Alert:
    return Alert(**{
        'type': Alert.AlertTypes.notification,
        'title': 'You have a new job!',
        'content': 'You have a new job!',
        'uid': user_id,
    })

def create_insurance_expires_reminder(user_id: str, days: int) -> Alert:
    """Creates an alert reminder user of expiring insurance"""
    days_str = 'day' if days == 1 else 'days'
    return Alert(**{
        'type': Alert.AlertTypes.warning,
        'title': 'Insurance Expiring',
        'content': f'Your insurance expires in {days} {days_str}. Your account will be paused if your insurance expires. Go to Account Settings to update.',
        'uid': user_id,
    })


def create_fee_processed_alert(user_id: str, fee_type: str, amount: int) -> Alert:
    """Creates an alert after a fee has been processed"""
    return Alert(**{
        'type': Alert.AlertTypes.payment_outgoing,
        'title': 'Payment Sent',
        'content': f'Your ${as_currency(amount)} {fee_type} fee has been paid.',
        'uid': user_id,
    })


def create_license_expires_reminder(user_id: str, days: int) -> Alert:
    """Creates an alert reminder user of expiring license"""
    days_str = 'day' if days == 1 else 'days'
    return Alert(**{
        'type': Alert.AlertTypes.warning,
        'title': 'License Expiring',
        'content': f'Your state license expires in {days} {days_str}. Your account will be paused if your licence expires. Go to Account Settings to update.',
        'uid': user_id,
    })


def create_payment_received_alert(user_id: str, job_id: str, amount: int) -> Alert:
    """Creates an alert when an installer recieves a payment after a completed job"""
    return Alert(**{
        'type': Alert.AlertTypes.payment_incoming,
        'title': 'Payment Received',
        'content': f'{as_currency(amount)} received for job #{job_id}.',
        'uid': user_id,
    })


def create_support_updated_alert(user_id: str, who: str = '') -> Alert:
    """Creates an alert for admin or support changes to installer accounts"""
    return Alert(**{
        'type': Alert.AlertTypes.notification,
        'title': 'New Job Ticket!',
        'content': f'Your ReadiCharge account information has been successfully updated by {who}.',
        'uid': user_id,
    })
