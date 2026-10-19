from datetime import datetime, timezone

from app.repositories import finance_repository


class FinanceService:
    @staticmethod
    def list_expenses(user):
        return finance_repository.list_expenses(user["tenant_id"])

    @staticmethod
    def create_expense(user, data):
        values = data.model_dump()
        values["category"] = values["category"].strip()
        values["description"] = values["description"].strip()
        return finance_repository.create_expense(
            user["tenant_id"], user["id"], values, datetime.now(timezone.utc).isoformat()
        )

    @staticmethod
    def get_report(user, start_date: str | None = None, end_date: str | None = None):
        report = finance_repository.get_financial_report(user["tenant_id"], start_date, end_date)
        cogs = {row["month"]: row["cost_of_goods"] or 0 for row in report["cost_of_goods"]}
        expenses = {row["month"]: row["total"] or 0 for row in report["expenses"]}
        returns = {row["month"]: row for row in report["returns"]}
        for month in report["sales"]:
            returned = returns.get(month["month"], {})
            month["refunds"] = round(returned.get("refunds") or 0, 2)
            month["net_sales"] = round(month["net_sales"] - month["refunds"], 2)
            month["cost_of_goods"] = round(max(0, cogs.get(month["month"], 0) - (returned.get("cost_reversed") or 0)), 2)
            month["expenses"] = round(expenses.get(month["month"], 0), 2)
            month["gross_profit"] = round(month["net_sales"] - month["cost_of_goods"], 2)
            month["operating_profit"] = round(month["gross_profit"] - month["expenses"], 2)
        report["months"] = report.pop("sales")
        for month in report["yearly"]:
            month_returns = sum((row.get("refunds") or 0) for key, row in returns.items() if key and key.startswith(month["year"]))
            month["refunds"] = round(month_returns, 2)
            month["net_sales"] = round(month["net_sales"] - month_returns, 2)
            month["cost_of_goods"] = round(max(0, sum(row["cost_of_goods"] or 0 for row in report["cost_of_goods"] if row["month"] and row["month"].startswith(month["year"])) - sum((row.get("cost_reversed") or 0) for key, row in returns.items() if key and key.startswith(month["year"]))), 2)
            month["expenses"] = round(sum(row["total"] or 0 for row in report["expenses"] if row["month"] and row["month"].startswith(month["year"])), 2)
            month["operating_profit"] = round(month["net_sales"] - month["cost_of_goods"] - month["expenses"], 2)
        return report
