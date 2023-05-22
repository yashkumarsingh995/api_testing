from rctools.mail import EmailTemplates
from templates._default_email_template import body
from templates import installer_welcome_email


def apply_params(content: str, params: dict, html=True):
    """Performs a find/replace over the content for any variable provided in the params"""
    for key, value in params.items():
        if f'{{{key}}}' in content:  # note, triple brace syntax is an escaped literal brace {{ plus a brace { around the variable
            content = content.replace(f'{{{key}}}', value)
    return content


def get_content(template_name: EmailTemplates, params: dict) -> dict:
    """Returns an object containing the subject and text and HTML versions of an email with the given template name"""
    if template_name == EmailTemplates.installer__welcomeEmail:
        return {
            'subject': installer_welcome_email.subject,
            'html': apply_params(installer_welcome_email.html, params, html=True),
            'text': apply_params(installer_welcome_email.text, params)
        }
