import boto3
import logging
import os

from rctools.alerts import add_user_alert, create_welcome_alert
from rctools.aws.aws_lambda import async_invoke
from rctools.mail import EmailTemplates


dynamodb = boto3.resource('dynamodb')
lambda_client = boto3.client('lambda')
logger = logging.getLogger()
logger.setLevel(logging.INFO)

ALERTS_TABLE_NAME = os.environ.get('ALERTS_TABLE_NAME')
SEND_EMAIL_TO_QUEUE_LAMBDA_NAME = os.environ.get('SEND_EMAIL_TO_QUEUE_LAMBDA_NAME')

alerts_table = dynamodb.Table(ALERTS_TABLE_NAME)


def admin_pre_sign_up(event, context):
    logger.info(f'Received admin pre sign up event: {event}')
    logger.info('Auto confirming user')
    event['response']['autoConfirmUser'] = True
    if 'email' in event['request']['userAttributes']:
        event['response']['autoVerifyEmail'] = True  # XXX this process is currently broken in Cognito, as of 12/01, you need to autoVerify both email and phone to get email to work (phone will not be verified)
    if 'phone_number' in event['request']['userAttributes']:
        event['response']['autoVerifyPhone'] = True
    # # Send welcome email
    # async_invoke(
    #     lambda_client,
    #     SEND_EMAIL_TO_QUEUE_LAMBDA_NAME,
    #     {
    #         'to': event['request']['userAttributes']['email'],
    #         'type': EmailTemplates.company__welcomeEmail
    #     }
    # )
    return event


def admin_custom_message(event, context):
    """Override for default Cognito emails"""
    logger.info(f'Cognito custom message override: {event}')
    code = event['request']['codeParameter']
    name = event['request']['userAttributes']['name'].split(' ')[0]
    link_parameter = 'readicharge://reset'
    forgot_pw_html = f"""
        <div>
            <p>{name},</p>
            <p>We recently received a request to reset your password for your ReadiCharge account. Please click <a href="{link_parameter}">here</a> to create a new password
            and use the code {code}.</p>
            <p>For your security, this link will expire in 1 hour.</p>
            <p>If you did not request this change, you can disgregard this message and your password will remain unchanged. 
            <p>This is an automated message to please do not reply to this email address.</p>
            <p>Thanks,</p>
            <p>The ReadiCharge Team</p>
        </div>
    """
    if event['triggerSource'] == 'CustomMessage_ForgotPassword':
        logger.info('Overriding forgot password...')
        event['response']['emailSubject'] = 'Forgot Password'
        event['response']['emailMessage'] = forgot_pw_html
        event['response']['smsMessage'] = f'Your ReadiCharge password reset code is {code}.'
        logger.info(event['response'])
    return event


def customer_custom_message(event, context):
    """Override for default Cognito emails"""
    logger.info(f'Cognito custom message override: {event}')
    code = event['request']['codeParameter']
    name = event['request']['userAttributes']['name'].split(' ')[0]
    link_parameter = 'readicharge://reset'
    forgot_pw_html = f"""
        <div>
            <p>{name},</p>
            <p>We recently received a request to reset your password for your ReadiCharge account. Please click <a href="{link_parameter}">here</a> to create a new password
            and use the code {code}.</p>
            <p>For your security, this link will expire in 1 hour.</p>
            <p>If you did not request this change, you can disgregard this message and your password will remain unchanged. 
            <p>This is an automated message to please do not reply to this email address.</p>
            <p>Thanks,</p>
            <p>The ReadiCharge Team</p>
        </div>
    """
    if event['triggerSource'] == 'CustomMessage_ForgotPassword':
        logger.info('Overriding forgot password...')
        event['response']['emailSubject'] = 'Forgot Password'
        event['response']['emailMessage'] = forgot_pw_html
        event['response']['smsMessage'] = f'Your ReadiCharge password reset code is {code}.'
        logger.info(event['response'])
    return event


def customer_pre_sign_up(event, context):
    logger.info(f'Received customer pre sign up event: {event}')
    logger.info('Auto confirming user')
    event['response']['autoConfirmUser'] = True
    if 'email' in event['request']['userAttributes']:
        event['response']['autoVerifyEmail'] = True  # XXX this process is currently broken in Cognito, as of 12/01, you need to autoVerify both email and phone to get email to work (phone will not be verified)
    if 'phone_number' in event['request']['userAttributes']:
        event['response']['autoVerifyPhone'] = True
    logger.info('Adding welcome alert')
    uid = event['userName']    
    alert = create_welcome_alert(uid, 'This is your dashboard where you can see upcoming jobs, see and edit installation details, message your installer, and more!')
    add_user_alert(alerts_table, uid, alert)
    # Send welcome email
    async_invoke(
        lambda_client,
        SEND_EMAIL_TO_QUEUE_LAMBDA_NAME,
        {
            'to': event['request']['userAttributes']['email'],
            'type': EmailTemplates.customer__welcomeEmail
        }
    )
    return event


def installer_custom_message(event, context):
    """Override for default Cognito emails"""
    logger.info(f'Cognito custom message override: {event}')
    code = event['request']['codeParameter']
    name = event['request']['userAttributes']['name'].split(' ')[0]
    link_parameter = 'readicharge://reset'
    forgot_pw_html = f"""
        <div>
            <p>{name},</p>
            <p>We recently received a request to reset your password for your ReadiCharge account. Please click <a href="{link_parameter}">here</a> to create a new password
            and use the code {code}.</p>
            <p>For your security, this link will expire in 1 hour.</p>
            <p>If you did not request this change, you can disgregard this message and your password will remain unchanged. 
            <p>This is an automated message to please do not reply to this email address.</p>
            <p>Thanks,</p>
            <p>The ReadiCharge Team</p>
        </div>
    """
    if event['triggerSource'] == 'CustomMessage_ForgotPassword':
        logger.info('Overriding forgot password...')
        event['response']['emailSubject'] = 'Forgot Password'
        event['response']['emailMessage'] = forgot_pw_html
        event['response']['smsMessage'] = f'Your ReadiCharge password reset code is {code}.'
        logger.info(event['response'])
    return event


def installer_post_confirmation(event, content):
    logger.info(f'Received installer post confirmation event: {event}')
    return event


def installer_pre_sign_up(event, context):
    logger.info(f'Received installer pre sign up event: {event}')
    event['response']['autoConfirmUser'] = True
    event['response']['autoVerifyEmail'] = True  # XXX this process is currently broken in Cognito, as of 12/01
    if 'phone_number' in event['request']['userAttributes']:
        event['response']['autoVerifyPhone'] = True
    logger.info('Adding welcome alert')
    uid = event['userName']
    # Add welcome alerts
    alert = create_welcome_alert(uid, 'This is your dashboard where you can see upcoming job tickets, contact customers, modify installation details, and more!')
    add_user_alert(alerts_table, uid, alert)
    # Send welcome email
    async_invoke(
        lambda_client,
        SEND_EMAIL_TO_QUEUE_LAMBDA_NAME,
        {
            'to': event['request']['userAttributes']['email'],
            'type': EmailTemplates.installer__welcomeEmail
        }
    )
    logger.info(f'Returning {event}')
    return event
