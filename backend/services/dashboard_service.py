"""
dashboard_service.py
--------------------
Computes dashboard KPI statistics from in-memory data.
"""

from data_loader import AppData


def get_summary(d: AppData) -> dict:
    pa = d.pattern_alerts

    critical = int((pa["priority"] == "CRITICAL").sum()) if not pa.empty and "priority" in pa.columns else 0
    high = int((pa["priority"] == "HIGH").sum()) if not pa.empty and "priority" in pa.columns else 0
    watch = int((pa["priority"] == "WATCH").sum()) if not pa.empty and "priority" in pa.columns else 0

    # high-risk routes from route_intelligence
    high_risk = 0
    emerging = 0
    if not d.route_intelligence.empty and "route_status" in d.route_intelligence.columns:
        high_risk = int((d.route_intelligence["route_status"] == "HIGH_RISK").sum())
        emerging = int((d.route_intelligence["route_status"] == "EMERGING").sum())

    # active investigations = IMMEDIATE + HIGH priority in investigation_targets
    active_inv = 0
    if not d.investigation_targets.empty and "priority" in d.investigation_targets.columns:
        active_inv = int(
            d.investigation_targets["priority"].isin(["IMMEDIATE", "HIGH"]).sum()
        )

    return {
        "total_incidents": len(d.incidents),
        "total_actors": len(d.actors),
        "total_routes": len(d.routes),
        "total_shipments": len(d.shipments),
        "total_alerts": len(pa),
        "critical_alerts": critical,
        "high_alerts": high,
        "watch_alerts": watch,
        "active_investigations": active_inv,
        "high_risk_routes": high_risk,
        "emerging_hubs": emerging,
    }
