# from fastapi import APIRouter, Request, Response
# import boto3
# from botocore.exceptions import ClientError
# import base64
# import json
# import os
# import stripe


# router = APIRouter()

# # XXX Replace with RCTools packages
# def get_secret(secret_name, region):
#     # Create a Secrets Manager client
#     session = boto3.session.Session()
#     client = session.client(
#         service_name='secretsmanager',
#         region_name=region
#     )

#     try:
#         resp = client.get_secret_value(SecretId=secret_name)
#     except ClientError as e:
#         raise e

#     if 'SecretString' in resp:
#         secret = resp['SecretString']
#         return secret
#     else:
#         decoded_binary_secret = base64.b64decode(resp['SecretBinary'])
#         return decoded_binary_secret


# def get_json_secret(secret_name, region):
#     return json.loads(get_secret(secret_name, region))


# def create_customer(email, payment_method):
#     # TODO look into what other metadata we want to store in Stripe
#     stripe.api_key = get_stripe_key()
#     return stripe.Customer.create(
#         email=email,
#         payment_method=payment_method,
#         invoice_settings={
#             'default_payment_method': payment_method
#         }
#     )


# def find_customer(db, uid):
#     query = {'uid': uid}
#     items, _ = db.fetch_items_by_gsi('gsiFirstPayment', query)
#     if items:
#         return items[0]


# def get_customer_id(db, request_data):
#     customer = find_customer(db, request_data['uid'])
#     if not customer:
#         email = request_data['email']
#         payment_method = request_data['payment_method']
#         customer = create_customer(email, payment_method)
#         # 'id' from stripe response
#         return customer['id'], True
#     # 'customer_id' from dynamo
#     return customer['customer_id'], False


# @router.get('/payment')
# def get_stripe_key(request: Request, response: Response) -> int:
#     """
#     Endpoint to create and confirm a Stripe PaymentIntent

#     This endpoint is only used internally by other services (such as policy
#     when binding) and should not be accessed directly by a customer
#     """
#     # STRIPE_KEY_SECRETS = os.environ.get('STRIPE_KEY_SECRETS')
#     # AWS_REGION_NAME = os.environ.get('AWS_REGION_NAME')
#     secret_name = "READICHARGE_STRIPE_KEY"
#     region_name = "us-east-2"


#     stripe_secret = get_json_secret(secret_name, region_name)
#     # stripe_api_key = stripe_secret['READICHARGE_STRIPE_KEY']
#     wrong_key = 123
#     return wrong_key


# # @router.post('/payment')
# # def create_payment(): 