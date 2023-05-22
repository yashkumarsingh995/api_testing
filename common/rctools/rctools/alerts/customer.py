from rctools.models import Alert
from rctools.utils import as_currency


def create_customer_new_job_alert(user_id: str, content: str = 'Your installation has been scheduled!') -> Alert:
    """Creates new customer job alert"""
    return Alert(**{
        'type': Alert.AlertTypes.notification,
        'title': 'Your installation has been scheduled!',
        'content': content,
        'uid': user_id,
    })

def create_payment_processed_alert(user_id: str, amount: int) -> Alert:
    """Creates an alert after a payment has been processed"""
    return Alert(**{
        'type': Alert.AlertTypes.payment_outgoing,
        'title': 'Payment Sent',
        'content': f'Your {as_currency(amount)} payment has been processed. Thank you!',
        'uid': user_id,
    })
