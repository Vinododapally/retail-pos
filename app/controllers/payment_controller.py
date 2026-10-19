import json
import logging

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from fastapi.responses import JSONResponse

from app.middleware.auth_middleware import CurrentUser
from app.models.schemas import RazorpayOrderInput, RazorpayVerifyInput
from app.services.payment_service import PaymentService
from app.utils.razorpay import PaymentGatewayError, RazorpayClient

logger = logging.getLogger("counterpoint.payments")
router = APIRouter()


def get_gateway() -> RazorpayClient:
    return RazorpayClient()


@router.get("/payments/razorpay/config")
def razorpay_config(user: CurrentUser, gateway: RazorpayClient = Depends(get_gateway)):
    return PaymentService.config(user, gateway)


@router.post("/payments/razorpay/orders")
def create_razorpay_order(
    data: RazorpayOrderInput,
    user: CurrentUser,
    gateway: RazorpayClient = Depends(get_gateway),
):
    return PaymentService.create_order(user, data, gateway)


@router.post("/payments/razorpay/verify")
def verify_razorpay_payment(
    data: RazorpayVerifyInput,
    user: CurrentUser,
    gateway: RazorpayClient = Depends(get_gateway),
):
    return PaymentService.verify_checkout(user, data, gateway)


@router.post("/payments/razorpay/webhook")
async def razorpay_webhook(
    request: Request,
    x_razorpay_signature: str | None = Header(default=None),
    x_razorpay_event_id: str | None = Header(default=None),
    gateway: RazorpayClient = Depends(get_gateway),
):
    if not x_razorpay_signature:
        raise HTTPException(status_code=400, detail="Missing Razorpay webhook signature.")
    body = await request.body()
    try:
        valid = gateway.verify_webhook_signature(body, x_razorpay_signature)
    except PaymentGatewayError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    if not valid:
        logger.warning("Rejected Razorpay webhook with invalid signature (event %s)", x_razorpay_event_id or "unknown")
        raise HTTPException(status_code=400, detail="Razorpay webhook signature is invalid.")
    try:
        event = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid Razorpay webhook body.")
    result = PaymentService.process_webhook(event, gateway)
    return JSONResponse(
        content=result,
        status_code=200,
        headers={"X-Razorpay-Event-ID": x_razorpay_event_id} if x_razorpay_event_id else None,
    )
