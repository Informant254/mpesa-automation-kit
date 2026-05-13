import base64
import hashlib
import json
import requests
from datetime import datetime
from typing import Dict, Optional
import os
from dotenv import load_dotenv

load_dotenv()

class MpesaClient:
    def __init__(self):
        self.consumer_key = os.getenv('MPESA_CONSUMER_KEY')
        self.consumer_secret = os.getenv('MPESA_CONSUMER_SECRET')
        self.shortcode = os.getenv('MPESA_SHORTCODE')
        self.passkey = os.getenv('MPESA_PASSKEY')
        self.initiator_name = os.getenv('MPESA_INITIATOR_NAME')
        self.initiator_password = os.getenv('MPESA_INITIATOR_PASSWORD')
        self.base_url = os.getenv('MPESA_BASE_URL', 'https://sandbox.safaricom.co.ke')
        self.token = None

    def _get_access_token(self):
        url = f'{self.base_url}/oauth/v1/generate?grant_type=client_credentials'
        auth = base64.b64encode(f'{self.consumer_key}:{self.consumer_secret}'.encode()).decode()
        headers = {'Authorization': f'Basic {auth}'}
        response = requests.get(url, headers=headers)
        data = response.json()
        self.token = data.get('access_token')
        return self.token

    def _make_request(self, endpoint, data, method='POST'):
        if not self.token:
            self._get_access_token()
        headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }
        url = f'{self.base_url}{endpoint}'
        if method == 'POST':
            response = requests.post(url, json=data, headers=headers)
        else:
            response = requests.get(url, headers=headers)
        return response.json()

    def stk_push(self, phone: str, amount: int, account_ref: str, transaction_desc: str = 'Payment'):
        """STK Push (Lipa Na M-Pesa)"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        password = base64.b64encode(f'{self.shortcode}{self.passkey}{timestamp}'.encode()).decode()
        data = {
            'BusinessShortCode': self.shortcode,
            'Password': password,
            'Timestamp': timestamp,
            'TransactionType': 'CustomerPayBillOnline',
            'Amount': amount,
            'PartyA': phone,
            'PartyB': self.shortcode,
            'PhoneNumber': phone,
            'CallBackURL': os.getenv('MPESA_CALLBACK_URL'),
            'AccountReference': account_ref,
            'TransactionDesc': transaction_desc
        }
        return self._make_request('/mpesa/stkpush/v1/processrequest', data)

    def b2c(self, phone: str, amount: int, remarks: str, occasion: str = ''):
        """Business to Customer payment"""
        data = {
            'InitiatorName': self.initiator_name,
            'SecurityCredential': base64.b64encode(self.initiator_password.encode()).decode(),
            'CommandID': 'BusinessPayment',
            'Amount': amount,
            'PartyA': self.shortcode,
            'PartyB': phone,
            'Remarks': remarks,
            'QueueTimeOutURL': os.getenv('MPESA_CALLBACK_URL'),
            'ResultURL': os.getenv('MPESA_CALLBACK_URL'),
            'Occasion': occasion
        }
        return self._make_request('/mpesa/b2c/v1/paymentrequest', data)

    def get_balance(self):
        """Check account balance"""
        data = {
            'Initiator': self.initiator_name,
            'SecurityCredential': base64.b64encode(self.initiator_password.encode()).decode(),
            'CommandID': 'AccountBalance',
            'PartyA': self.shortcode,
            'IdentifierType': '4',
            'Remarks': 'Balance check'
        }
        return self._make_request('/mpesa/accountbalance/v1/query', data)
