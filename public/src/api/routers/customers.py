import logging
import os

import boto3
from botocore.exceptions import ClientError
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from rctools.customers import create_customer
from rctools.models import Customer, NewCustomerResponse


COMPANY_DATA_BUCKET = os.getenv('COMPANY_DATA_BUCKET')
CUSTOMER_USER_POOL_ID = os.getenv('CUSTOMER_USER_POOL_ID')
USER_DATA_BUCKET = os.getenv('USER_DATA_BUCKET')


cognito_client = boto3.client('cognito-idp')
logger = logging.getLogger()
logger.setLevel(logging.INFO)
router = APIRouter()
s3_client = boto3.client('s3')


@router.post('/customer', response_model=NewCustomerResponse)
def create_new_customer(data: Customer):
    """
    Creates a new customer user in Cognito. It will return a user id for the
    newly created user.

    Email and phone number are the only required fields, but the endpoint will accept
    any other additional fields that you want to store with the user object.
    """
    logger.info(f'Creating new customer user')  # Careful not to log data object and expose passwords
    try:
        user_id = create_customer(cognito_client, s3_client, CUSTOMER_USER_POOL_ID, USER_DATA_BUCKET, data.dict())
        logger.info(f'Customer {user_id} created!')
        response = NewCustomerResponse(**{'user_id': user_id})  # XXX revisit
        return response
    except ClientError as e:
        logger.exception('Error creating new customer')
        return JSONResponse({'error': str(e)}, 400)


@router.post('/customers/mailing_list/signup', status_code=status.HTTP_200_OK)
def sign_customer_up_for_maling_list(email_address: str) -> bool:
    """
    Adds a customers email to a mailing list to be contacted when more installers
    are added in their area
    """
    logger.info(f'Adding customer email to mailing list {email_address}')
    # TODO
    return True
    


# @router.get('/customer/job/estimate', status_code=status.HTTP_200_OK)
# def get_customer_estimate(id: str, customer: Customer, scope: JobScope) -> str:
#     """
#     Finds what tier the customer falls into and updates the customer attributes. 

#     returns job price estimate
#     """
#     logger.info(f'Determining tier for customer {id}')
#     job_estimate = get_customer_tier(scope) 
#     if job_estimate.tier == 'commercial':
#         return 'Contact ReadiCharge'

#     customer['tier'] = job_estimate.tier
#     put_customer_data_into_s3(s3_client, USER_DATA_BUCKET, id, customer)
#     return determine_price_estimate(job_estimate, customer['state'])
