import base64
import datetime
import requests
from dotenv import load_dotenv
import os

load_dotenv()

class MpesaClient:
    def __init__(self):
        self.consumer_key = os.getenv('CONSUMER_KEY')
        self.consumer_secret = os.getenv('CONSUMER_SECRET')
        self.shortcode = os.getenv('SHORTCODE')
        self.passkey = os.getenv('PASSKEY')
        self.callback_url = os.getenv('CALLBACK_URL')
        self.initiator_name = os.getenv('INITIATOR_NAME', '')
        self.security_credential = os.getenv('SECURITY_CREDENTIAL', '')
        self.base_url = 'https://sandbox.safaricom.co.ke'
        self.token = None

    def get_access_token(self):
        url = f'{self.base_url}/oauth/v1/generate?grant_type=client_credentials'
        r = requests.get(url, auth=(self.consumer_key, self.consumer_secret))
        r.raise_for_status()
        self.token = r.json()['access_token']
        return self.token

    def stk_push(self, phone_number: str, amount: int, account_reference: str, transaction_desc: str = "Payment"):
        if not self.token:
            self.get_access_token()
        timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        password = base64.b64encode((self.shortcode + self.passkey + timestamp).encode()).decode('utf-8')
        url = f'{self.base_url}/mpesa/stkpush/v1/processrequest'
        payload = {
            "BusinessShortCode": self.shortcode,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": amount,
            "PartyA": phone_number,
            "PartyB": self.shortcode,
            "PhoneNumber": phone_number,
            "CallBackURL": self.callback_url,
            "AccountReference": account_reference,
            "TransactionDesc": transaction_desc
        }
        headers = {'Authorization': f'Bearer {self.token}'}
        response = requests.post(url, json=payload, headers=headers)
        return response.json()

    def b2c(self, phone_number: str, amount: int, remarks: str, occasion: str = "Payout"):
        if not self.token:
            self.get_access_token()
        url = f'{self.base_url}/mpesa/b2c/v1/paymentrequest'
        payload = {
            "InitiatorName": self.initiator_name,
            "SecurityCredential": self.security_credential,
            "CommandID": "BusinessPayment",
            "Amount": amount,
            "PartyA": self.shortcode,
            "PartyB": phone_number,
            "Remarks": remarks,
            "QueueTimeOutURL": self.callback_url,
            "ResultURL": self.callback_url,
            "Occasion": occasion
        }
        headers = {'Authorization': f'Bearer {self.token}'}
        response = requests.post(url, json=payload, headers=headers)
        return response.json()

    def get_balance(self):
        if not self.token:
            self.get_access_token()
        url = f'{self.base_url}/mpesa/accountbalance/v1/query'
        payload = {
            "Initiator": self.initiator_name,
            "SecurityCredential": self.security_credential,
            "CommandID": "AccountBalance",
            "PartyA": self.shortcode,
            "IdentifierType": "4",
            "Remarks": "Balance Query"
        }
        headers = {'Authorization': f'Bearer {self.token}'}
        response = requests.post(url, json=payload, headers=headers)
        return response.json()