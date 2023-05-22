import logging

from enum import Enum
from typing import List


logger = logging.getLogger()
logger.setLevel(logging.INFO)



def send_email(ses_client: any, subject: str, body_text: str, body_html: str, from_addr: str, to_addrs: List, cc_addrs: List = [], bcc_addrs: List = []):
    """Sends an email with SES"""
    destination = {
        'ToAddresses': to_addrs
    }
    if cc_addrs:
        destination['CcAddresses'] = cc_addrs
    if bcc_addrs:
        destination['BccAddresses'] = bcc_addrs
    logger.info(f'Sending to: {to_addrs} {cc_addrs} {bcc_addrs}')
    logger.info(f'Sending text: {body_text}')
    logger.info(f'Sending html: {body_html}')
    resp = ses_client.send_email(
        Source=from_addr,
        Destination=destination,
        Message={
            'Subject': {
                'Data': subject,
                'Charset': 'UTF-8'
            },
            'Body': {
                'Text': {
                    'Data': body_text,
                    'Charset': 'UTF-8'
                },
                'Html': {
                    'Data': body_html,
                    'Charset': 'UTF-8'
                }
            }
        },
        # ReturnPath='team-readicharge@thenewfoundry.com',  # this email must be verified through SES
    )
    logger.info(resp)
    return resp