from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query

from app.middleware.auth_middleware import require_admin
from app.models.schemas import ExpenseInput
from app.services.finance_service import FinanceService

router = APIRouter()


@router.get("/expenses")
def list_expenses(user: dict = Depends(require_admin)):
    return FinanceService.list_expenses(user)


@router.post("/expenses")
def create_expense(data: ExpenseInput, user: dict = Depends(require_admin)):
    return FinanceService.create_expense(user, data)


@router.get("/reports/financial")
def financial_report(
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    user: dict = Depends(require_admin),
):
    if start_date and end_date and start_date > end_date:
        raise HTTPException(status_code=422, detail="Start date must be on or before end date.")
    return FinanceService.get_report(
        user,
        start_date.isoformat() if start_date else None,
        end_date.isoformat() if end_date else None,
    )
