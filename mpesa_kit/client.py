import base64
import datetime
import os
import time
from typing import Any, Dict, Optional

import requests
from dotenv import load_dotenv

load_dotenv()


class MpesaError(RuntimeError):
    """Raised when Daraja returns an error or configuration is incomplete."""


class MpesaClient:
    SANDBOX_BASE_URL = "https://sandbox.safaricom.co.ke"
    PRODUCTION_BASE_URL = "https://api.safaricom.co.ke"

    def __init__(
        self,
        consumer_key: Optional[str] = None,
        consumer_secret: Optional[str] = None,
        shortcode: Optional[str] = None,
        passkey: Optional[str] = None,
        callback_url: Optional[str] = None,
        initiator_name: Optional[str] = None,
        security_credential: Optional[str] = None,
        environment: Optional[str] = None,
        timeout: int = 30,
        session: Optional[requests.Session] = None,
    ) -> None:
        self.consumer_key = consumer_key or os.getenv("CONSUMER_KEY")
        self.consumer_secret = consumer_secret or os.getenv("CONSUMER_SECRET")
        self.shortcode = shortcode or os.getenv("SHORTCODE")
        self.passkey = passkey or os.getenv("PASSKEY")
        self.callback_url = callback_url or os.getenv("CALLBACK_URL")
        self.initiator_name = initiator_name or os.getenv("INITIATOR_NAME")
        self.security_credential = security_credential or os.getenv("SECURITY_CREDENTIAL")

        self.environment = (environment or os.getenv("MPESA_ENVIRONMENT", "sandbox")).lower()
        if self.environment not in {"sandbox", "production"}:
            raise ValueError("MPESA_ENVIRONMENT must be 'sandbox' or 'production'")

        self.base_url = self.SANDBOX_BASE_URL if self.environment == "sandbox" else self.PRODUCTION_BASE_URL
        self.timeout = timeout
        self.session = session or requests.Session()
        self.token: Optional[str] = None
        self._token_expires_at = 0.0

    @staticmethod
    def normalize_phone(phone_number: str) -> str:
        raw = "".join(ch for ch in str(phone_number) if ch.isdigit())
        if raw.startswith("0") and len(raw) == 10:
            raw = "254" + raw[1:]
        elif raw.startswith("7") and len(raw) == 9:
            raw = "254" + raw
        elif raw.startswith("1") and len(raw) == 9:
            raw = "254" + raw
        if not (raw.startswith("254") and len(raw) == 12):
            raise ValueError("Phone number must be a Kenyan MSISDN, e.g. 254712345678")
        return raw

    @staticmethod
    def _positive_amount(amount: int) -> int:
        value = int(amount)
        if value <= 0:
            raise ValueError("Amount must be greater than zero")
        return value

    def _require(self, **values: Optional[str]) -> None:
        missing = [name for name, value in values.items() if not value]
        if missing:
            raise MpesaError("Missing configuration: " + ", ".join(missing))

    def _json_or_error(self, response: requests.Response) -> Dict[str, Any]:
        try:
            data = response.json()
        except ValueError:
            data = {"raw": response.text}
        try:
            response.raise_for_status()
        except requests.HTTPError as exc:
            raise MpesaError("Daraja HTTP {}: {}".format(response.status_code, data)) from exc
        if isinstance(data, dict) and data.get("errorCode"):
            raise MpesaError("Daraja {}: {}".format(data.get("errorCode"), data.get("errorMessage", data)))
        return data

    def get_access_token(self, force: bool = False) -> str:
        if not force and self.token and time.time() < self._token_expires_at:
            return self.token
        self._require(CONSUMER_KEY=self.consumer_key, CONSUMER_SECRET=self.consumer_secret)
        url = self.base_url + "/oauth/v1/generate?grant_type=client_credentials"
        response = self.session.get(url, auth=(self.consumer_key, self.consumer_secret), timeout=self.timeout)
        data = self._json_or_error(response)
        token = data.get("access_token")
        if not token:
            raise MpesaError("Daraja response did not include access_token")
        expires_in = int(data.get("expires_in", 3600))
        self.token = token
        self._token_expires_at = time.time() + max(60, expires_in - 60)
        return token

    def _request(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        token = self.get_access_token()
        url = self.base_url + path
        response = self.session.post(url, json=payload, headers={"Authorization": "Bearer " + token}, timeout=self.timeout)
        if response.status_code == 401:
            token = self.get_access_token(force=True)
            response = self.session.post(url, json=payload, headers={"Authorization": "Bearer " + token}, timeout=self.timeout)
        return self._json_or_error(response)

    def _stk_credentials(self) -> Dict[str, str]:
        self._require(SHORTCODE=self.shortcode, PASSKEY=self.passkey)
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        password = base64.b64encode((str(self.shortcode) + str(self.passkey) + timestamp).encode("utf-8")).decode("utf-8")
        return {"timestamp": timestamp, "password": password}

    def stk_push(self, phone_number: str, amount: int, account_reference: str, transaction_desc: str = "Payment", transaction_type: str = "CustomerPayBillOnline", callback_url: Optional[str] = None) -> Dict[str, Any]:
        callback = callback_url or self.callback_url
        self._require(CALLBACK_URL=callback)
        creds = self._stk_credentials()
        phone = self.normalize_phone(phone_number)
        payload = {
            "BusinessShortCode": self.shortcode,
            "Password": creds["password"],
            "Timestamp": creds["timestamp"],
            "TransactionType": transaction_type,
            "Amount": self._positive_amount(amount),
            "PartyA": phone,
            "PartyB": self.shortcode,
            "PhoneNumber": phone,
            "CallBackURL": callback,
            "AccountReference": str(account_reference)[:20],
            "TransactionDesc": str(transaction_desc)[:20],
        }
        return self._request("/mpesa/stkpush/v1/processrequest", payload)

    def stk_query(self, checkout_request_id: str) -> Dict[str, Any]:
        creds = self._stk_credentials()
        payload = {"BusinessShortCode": self.shortcode, "Password": creds["password"], "Timestamp": creds["timestamp"], "CheckoutRequestID": checkout_request_id}
        return self._request("/mpesa/stkpushquery/v1/query", payload)

    def b2c(self, phone_number: str, amount: int, remarks: str, occasion: str = "Payout", command_id: str = "BusinessPayment", result_url: Optional[str] = None, timeout_url: Optional[str] = None) -> Dict[str, Any]:
        result = result_url or os.getenv("B2C_RESULT_URL") or self.callback_url
        timeout = timeout_url or os.getenv("B2C_TIMEOUT_URL") or self.callback_url
        self._require(INITIATOR_NAME=self.initiator_name, SECURITY_CREDENTIAL=self.security_credential, SHORTCODE=self.shortcode, B2C_RESULT_URL=result, B2C_TIMEOUT_URL=timeout)
        payload = {"InitiatorName": self.initiator_name, "SecurityCredential": self.security_credential, "CommandID": command_id, "Amount": self._positive_amount(amount), "PartyA": self.shortcode, "PartyB": self.normalize_phone(phone_number), "Remarks": str(remarks)[:100], "QueueTimeOutURL": timeout, "ResultURL": result, "Occasion": str(occasion)[:100]}
        return self._request("/mpesa/b2c/v3/paymentrequest", payload)

    def get_balance(self, result_url: Optional[str] = None, timeout_url: Optional[str] = None, remarks: str = "Balance Query") -> Dict[str, Any]:
        result = result_url or os.getenv("BALANCE_RESULT_URL") or self.callback_url
        timeout = timeout_url or os.getenv("BALANCE_TIMEOUT_URL") or self.callback_url
        self._require(INITIATOR_NAME=self.initiator_name, SECURITY_CREDENTIAL=self.security_credential, SHORTCODE=self.shortcode, BALANCE_RESULT_URL=result, BALANCE_TIMEOUT_URL=timeout)
        payload = {"Initiator": self.initiator_name, "SecurityCredential": self.security_credential, "CommandID": "AccountBalance", "PartyA": self.shortcode, "IdentifierType": "4", "Remarks": remarks, "QueueTimeOutURL": timeout, "ResultURL": result}
        return self._request("/mpesa/accountbalance/v1/query", payload)

    def transaction_status(self, transaction_id: str, result_url: Optional[str] = None, timeout_url: Optional[str] = None, remarks: str = "Transaction Status Query", occasion: str = "Status") -> Dict[str, Any]:
        result = result_url or os.getenv("STATUS_RESULT_URL") or self.callback_url
        timeout = timeout_url or os.getenv("STATUS_TIMEOUT_URL") or self.callback_url
        self._require(INITIATOR_NAME=self.initiator_name, SECURITY_CREDENTIAL=self.security_credential, SHORTCODE=self.shortcode, STATUS_RESULT_URL=result, STATUS_TIMEOUT_URL=timeout)
        payload = {"Initiator": self.initiator_name, "SecurityCredential": self.security_credential, "CommandID": "TransactionStatusQuery", "TransactionID": transaction_id, "PartyA": self.shortcode, "IdentifierType": "4", "ResultURL": result, "QueueTimeOutURL": timeout, "Remarks": remarks, "Occasion": occasion}
        return self._request("/mpesa/transactionstatus/v1/query", payload)

    def register_c2b_urls(self, confirmation_url: Optional[str] = None, validation_url: Optional[str] = None, response_type: str = "Completed") -> Dict[str, Any]:
        confirmation = confirmation_url or os.getenv("C2B_CONFIRMATION_URL")
        validation = validation_url or os.getenv("C2B_VALIDATION_URL")
        self._require(SHORTCODE=self.shortcode, C2B_CONFIRMATION_URL=confirmation, C2B_VALIDATION_URL=validation)
        if response_type not in {"Completed", "Cancelled"}:
            raise ValueError("response_type must be Completed or Cancelled")
        payload = {"ShortCode": self.shortcode, "ResponseType": response_type, "ConfirmationURL": confirmation, "ValidationURL": validation}
        return self._request("/mpesa/c2b/v1/registerurl", payload)
