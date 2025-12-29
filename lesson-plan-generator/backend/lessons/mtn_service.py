import uuid
import requests
import os

MTN_API_USER = os.getenv("MTN_API_USER")  # UUID you generated
MTN_API_KEY = os.getenv("MTN_API_KEY")    # API key returned by MTN
MTN_SUBSCRIPTION_KEY = os.getenv("MTN_SUBSCRIPTION_KEY")
CALLBACK_URL = os.getenv("CALLBACK_URL")
BASE_URL = "https://sandbox.momodeveloper.mtn.com/v1_0"


def request_payment(amount, phone, external_id):
    """
    Initiate MTN MoMo payment request for sandbox.
    Returns the transaction reference ID.
    """
    ref_id = str(uuid.uuid4())  # Unique reference for this transaction

    url = f"{BASE_URL}/collection/v1_0/requesttopay"
    headers = {
        "Authorization": f"Bearer {MTN_API_KEY}",
        "X-Reference-Id": ref_id,
        "X-Target-Environment": "sandbox",
        "Content-Type": "application/json",
        "Ocp-Apim-Subscription-Key": MTN_SUBSCRIPTION_KEY
    }

    body = {
        "amount": str(amount),
        "currency": "USD",  # Sandbox default currency
        "externalId": external_id,
        "payer": {"partyIdType": "MSISDN", "partyId": phone},
        "payerMessage": f"Payment for {external_id}",
        "payeeNote": f"Payment for {external_id}"
    }

    response = requests.post(url, json=body, headers=headers)
    if response.status_code in [200, 202]:
        return ref_id
    else:
        raise Exception(f"MTN Payment failed: {response.text}")
