from mail import apply_params
from templates import _default_email_template, installer_welcome_email


def test__apply_params():
    """Tests string replace in apply params"""
    res = apply_params(_default_email_template.body, {'content': installer_welcome_email.html})
    assert installer_welcome_email.html in res