import hashlib
import hmac
import logging
import os

import httpx

logger = logging.getLogger("counterpoint.razorpay")
RAZORPAY_API = "https://api.razorpay.com/v1"


class PaymentGatewayError(Exception):
    pass


class RazorpayClient:
    def __init__(self, key_id: str | None = None, key_secret: str | None = None):
        self.key_id = key_id if key_id is not None else os.getenv("RAZORPAY_KEY_ID", "")
        self.key_secret = key_secret if key_secret is not None else os.getenv("RAZORPAY_KEY_SECRET", "")
        self.webhook_secret = os.getenv("RAZORPAY_WEBHOOK_SECRET", "")

    @property
    def configured(self) -> bool:
        return bool(self.key_id and self.key_secret)

    def _request(self, method: str, path: str, **kwargs) -> dict:
        if not self.configured:
            raise PaymentGatewayError("Razorpay is not configured. Set RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET.")
        try:
            response = httpx.request(
                method,
                f"{RAZORPAY_API}{path}",
                auth=(self.key_id, self.key_secret),
                timeout=15,
                **kwargs,
            )
        except httpx.TimeoutException as exc:
            logger.warning("Razorpay API request timed out: %s %s", method, path)
            raise PaymentGatewayError("Razorpay did not respond in time. Please retry.") from exc
        except httpx.RequestError as exc:
            logger.exception("Razorpay API request failed: %s %s", method, path)
            raise PaymentGatewayError("Could not reach Razorpay. Check the network and retry.") from exc
        if response.is_error:
            logger.error("Razorpay API returned %s for %s %s", response.status_code, method, path)
            if response.status_code in (401, 403):
                raise PaymentGatewayError("Razorpay credentials were rejected. Check the configured API keys.")
            raise PaymentGatewayError("Razorpay could not complete the payment request.")
        try:
            return response.json()
        except ValueError as exc:
            raise PaymentGatewayError("Razorpay returned an invalid response.") from exc

    def create_order(self, amount_minor: int, currency: str, receipt: str) -> dict:
        return self._request(
            "POST",
            "/orders",
            json={"amount": amount_minor, "currency": currency, "receipt": receipt},
        )

    def fetch_payment(self, payment_id: str) -> dict:
        return self._request("GET", f"/payments/{payment_id}")

    def verify_checkout_signature(self, order_id: str, payment_id: str, signature: str) -> bool:
        if not self.configured:
            raise PaymentGatewayError("Razorpay is not configured.")
        expected = hmac.new(
            self.key_secret.encode(),
            f"{order_id}|{payment_id}".encode(),
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(expected, signature)

    def verify_webhook_signature(self, body: bytes, signature: str) -> bool:
        if not self.webhook_secret:
            raise PaymentGatewayError("Set RAZORPAY_WEBHOOK_SECRET to enable payment webhooks.")
        expected = hmac.new(self.webhook_secret.encode(), body, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, signature)
