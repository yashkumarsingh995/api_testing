from enum import Enum


class EmailTemplates(str, Enum):
    company__welcomeEmail = 'company__welcome-email'
    customer__welcomeEmail = 'customer__welcome-email'
    installer__welcomeEmail = 'installer__welcome-email'