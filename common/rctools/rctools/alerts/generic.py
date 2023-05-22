from datetime import datetime

from rctools.models import Alert


def create_account_updated_alert(user_id: str) -> Alert:
    """Creates welcome alert"""
    return Alert(**{
        'type': Alert.AlertTypes.notification,
        'title': 'Account Info Updated',
        'content': 'Your ReadiCharge account information has been successfully updated.',
        'uid': user_id,
    })


def create_new_message_alert(user_id: str, content: str = '') -> Alert:
    """Creates message alert"""
    msg = f'{content[:90]}...' if len(content) > 90 else content
    return Alert(**{
        'type': Alert.AlertTypes.message,
        'title': 'Message',
        'content': msg,
        'uid': user_id,
    })


def create_password_updated_alert(user_id: str) -> Alert:
    """Creates an alert when a user's password has been updated"""
    now = datetime.now()
    return Alert(**{
        'type': Alert.AlertTypes.notification,
        'title': 'Password Updated',
        'content': f'Your ReadiCharge account password was changed on {now.strftime("%m-%d-%Y")}.',
        'uid': user_id,
    })


def create_welcome_alert(user_id: str, content: str = '') -> Alert:
    """Creates welcome alert"""
    return Alert(**{
        'type': Alert.AlertTypes.notification,
        'title': 'Welcome to ReadiCharge!',
        'content': content,
        'uid': user_id,
    })

    