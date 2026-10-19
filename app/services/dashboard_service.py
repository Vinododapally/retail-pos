from datetime import date, timedelta

from app.repositories.dashboard_repository import get_dashboard_data


class DashboardService:
    @staticmethod
    def get_dashboard(user):
        data = get_dashboard_data(user["tenant_id"])
        by_day = {row["day"]: row["revenue"] for row in data["chart_rows"]}
        chart = []
        for offset in reversed(range(7)):
            day = date.today() - timedelta(days=offset)
            chart.append({
                "day": day.strftime("%a"),
                "date": day.isoformat(),
                "revenue": round(float(by_day.get(day.isoformat(), 0)), 2),
            })
        return {
            "today_revenue": round(data["today"]["revenue"], 2),
            "today_orders": data["today"]["orders"],
            "week_revenue": round(data["week_revenue"], 2),
            "low_stock": data["low_stock"],
            "product_count": data["product_count"],
            "chart": chart,
            "recent_sales": data["recent_sales"],
        }
