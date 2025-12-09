"""
Public API Endpoints
====================

This module exposes top‑level API endpoints that map directly to the
frontend's expected URLs. Many of the core features are already
implemented elsewhere (e.g. in the `trading` router), but those
implementations live under a nested prefix such as `/trading`. The
frontend, however, calls `/metrics`, `/system/modes` and similar
paths. To bridge that gap we import the appropriate handler
functions and forward requests to them. When necessary we wrap the
call to inject dependencies or perform additional logic.

The routes defined here should *not* include an extra prefix like
`/api`. The server attaches this router under the `/api` prefix
automatically. See `server.py` for details.
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Any, Dict

from .trading import get_overview, get_recent_trades, get_system_modes
from .auth import get_current_user

from backend.database import system_modes_collection as modes_collection, trades_collection, bots_collection
from backend.logger_config import logger

# Import API key handlers for alias routes
from .api_keys import create_api_key, get_api_keys, delete_api_key, test_api_key

from backend.ccxt_service import ccxt_service
from ..engines.wallet_manager import wallet_manager
from datetime import datetime, timezone, timedelta

router = APIRouter()


@router.get("/metrics", tags=["Dashboard"])
async def metrics(user_id: str = Depends(get_current_user)) -> Dict[str, Any]:
    """Alias for the dashboard overview.

    Returns the same payload as `/trading/metrics` but is mounted at
    `/api/metrics` instead of `/api/trading/metrics`. This ensures
    compatibility with the frontend's expected endpoint.
    """
    return await get_overview(user_id)


@router.get("/trades/recent", tags=["Trading"])
async def trades_recent(limit: int = 50, user_id: str = Depends(get_current_user)) -> Dict[str, Any]:
    """Alias for recent trades."""
    return await get_recent_trades(limit, user_id)


@router.get("/system/modes", tags=["System Modes"])
async def list_system_modes(user_id: str = Depends(get_current_user)) -> Dict[str, Any]:
    """Retrieve the current system mode flags for the user."""
    return await get_system_modes(user_id)


@router.post("/system/modes/{mode}", tags=["System Modes"])
async def toggle_system_mode(mode: str, enabled: bool = True, user_id: str = Depends(get_current_user)) -> Dict[str, Any]:
    """Enable or disable a system mode for the user."""
    # Normalize mode names
    normalized = mode.strip().lower()
    if normalized in {"paper", "papertrading"}:
        field = "paperTrading"
    elif normalized in {"live", "livetrading"}:
        field = "liveTrading"
    elif normalized in {"auto", "autopilot"}:
        field = "autopilot"
    else:
        raise HTTPException(status_code=400, detail=f"Invalid mode '{mode}'. Valid modes: paper, live, autopilot")

    # Ensure a modes document exists
    modes_doc = await modes_collection.find_one({"user_id": user_id})
    if not modes_doc:
        modes_doc = {
            "user_id": user_id,
            "paperTrading": False,
            "liveTrading": False,
            "autopilot": False,
        }
        await modes_collection.insert_one(modes_doc)

    # Update the selected mode
    update = {field: bool(enabled), "updated_at": datetime.now(timezone.utc).isoformat()}
    await modes_collection.update_one({"user_id": user_id}, {"$set": update})

    # Return the updated document (omit Mongo _id)
    return await modes_collection.find_one({"user_id": user_id}, {"_id": 0})


# -----------------------------------------------------------------------------
# API Key Aliases
# -----------------------------------------------------------------------------

@router.get("/api_keys", tags=["API Keys"])
async def alias_get_api_keys(user_id: str = Depends(get_current_user)):
    """Alias for `GET /api-keys`. Simply forwards to the existing handler."""
    return await get_api_keys(user_id)  # type: ignore


@router.post("/api_keys", tags=["API Keys"], status_code=201)
async def alias_create_api_key(key_data: Any, user_id: str = Depends(get_current_user)):
    """Alias for `POST /api-keys`. Accepts the same payload as the original."""
    return await create_api_key(key_data, user_id)  # type: ignore


@router.delete("/api_keys/{provider}", tags=["API Keys"], status_code=204)
async def alias_delete_api_key(provider: str, user_id: str = Depends(get_current_user)):
    """Alias for `DELETE /api-keys/{provider}`."""
    return await delete_api_key(provider, user_id)  # type: ignore


@router.post("/api_keys/{provider}/test", tags=["API Keys"])
async def alias_test_api_key(provider: str, user_id: str = Depends(get_current_user)):
    """Alias for `POST /api-keys/{provider}/test`. Performs a connection test."""
    return await test_api_key(provider, user_id)  # type: ignore


# -----------------------------------------------------------------------------
# Market Data and Analytics
# -----------------------------------------------------------------------------

@router.get("/market/prices", tags=["Market"])
async def get_market_prices(exchange: str = "luno", pairs: str = "BTC/ZAR,ETH/ZAR", user_id: str = Depends(get_current_user)):
    """
    Get current market prices for a comma‑separated list of trading pairs.

    Args:
        exchange: The exchange to query (default: luno).
        pairs: A comma‑separated string of trading pairs (e.g. "BTC/ZAR,ETH/ZAR").
        user_id: Injected by FastAPI; unused but reserved for future per‑user routing.

    Returns:
        A dictionary mapping each pair to its last traded price. If a price
        cannot be fetched the fallback value from ccxt_service is returned.
    """
    result: Dict[str, float] = {}
    for pair in [p.strip().upper() for p in pairs.split(",") if p.strip()]:
        try:
            price = await ccxt_service.get_current_price(exchange, pair)
            result[pair] = price
        except Exception as e:
            logger.error(f"Failed to fetch price for {pair} on {exchange}: {e}")
            result[pair] = None
    return {"exchange": exchange, "prices": result, "timestamp": datetime.now(timezone.utc).isoformat()}


@router.get("/graphs/profit", tags=["Analytics"])
async def profit_graph(period: str = "7d", user_id: str = Depends(get_current_user)):
    """
    Generate a profit/time series for the given period.

    Args:
        period: One of "7d", "30d" or "90d". Determines how many days of trading history to include.
        user_id: Injected by FastAPI.

    Returns:
        A dictionary with two lists: `dates` (ISO strings) and `profit` values representing total P&L for each day.
    """
    now = datetime.now(timezone.utc)
    if period.endswith("d") and period[:-1].isdigit():
        days = int(period[:-1])
    else:
        days = 7
    start = now - timedelta(days=days)
    pipeline = [
        {"$match": {"user_id": user_id, "timestamp": {"$gte": start.isoformat()}}},
        {"$project": {"date": {"$substr": ["$timestamp", 0, 10]}, "profit_loss": "$profit_loss"}},
        {"$group": {"_id": "$date", "total_profit": {"$sum": "$profit_loss"}}},
        {"$sort": {"_id": 1}}
    ]
    try:
        cursor = trades_collection.aggregate(pipeline)
        data = []
        dates = []
        async for doc in cursor:
            dates.append(doc["_id"])
            data.append(round(doc.get("total_profit", 0), 2))
        return {"dates": dates, "profit": data}
    except Exception as e:
        logger.error(f"Profit graph error: {e}")
        return {"dates": [], "profit": []}


@router.get("/countdown", tags=["Analytics"])
async def countdown_to_million(target: float = 1_000_000.0, user_id: str = Depends(get_current_user)):
    """
    Estimate the number of days remaining to reach a target account value (default R1M).

    The calculation uses the current master wallet balance plus the sum of active bot capital to determine the user's base capital. It then computes the average daily profit over the last 7 days and projects the time required to reach the target under a simple linear growth assumption.

    Args:
        target: The financial goal in ZAR (default 1,000,000).
        user_id: Injected by FastAPI.

    Returns:
        A dictionary with the estimated days remaining and the target date.
    """
    master_balance = await wallet_manager.get_master_balance(user_id)
    total_zar = float(master_balance.get("total_zar", 0) or 0)
    bot_capital = 0.0
    try:
        async for bot in bots_collection.find({"user_id": user_id, "status": {"$ne": "deleted"}}, {"current_capital": 1}):
            bot_capital += float(bot.get("current_capital", 0) or 0)
    except Exception:
        pass
    current_total = total_zar + bot_capital
    now = datetime.now(timezone.utc)
    start = now - timedelta(days=7)
    pipeline = [
        {"$match": {"user_id": user_id, "timestamp": {"$gte": start.isoformat()}}},
        {"$project": {"date": {"$substr": ["$timestamp", 0, 10]}, "profit_loss": "$profit_loss"}},
        {"$group": {"_id": "$date", "profit": {"$sum": "$profit_loss"}}}
    ]
    daily_profits = []
    try:
        async for doc in trades_collection.aggregate(pipeline):
            daily_profits.append(doc.get("profit", 0))
    except Exception as e:
        logger.error(f"Countdown profit aggregation error: {e}")
    avg_daily_profit = sum(daily_profits) / len(daily_profits) if daily_profits else 0
    if current_total >= target:
        days_remaining = 0
    elif avg_daily_profit > 0:
        days_remaining = int((target - current_total) / avg_daily_profit)
    else:
        return {
            "current_total": current_total,
            "avg_daily_profit": avg_daily_profit,
            "days_remaining": None,
            "target_date": None
        }
    target_date = (now + timedelta(days=days_remaining)).date().isoformat()
    return {
        "current_total": current_total,
        "avg_daily_profit": round(avg_daily_profit, 2),
        "days_remaining": days_remaining,
        "target_date": target_date
    }


@router.get("/flokx/alerts", tags=["Market"])
async def flokx_alerts(user_id: str = Depends(get_current_user)):
    """
    Placeholder endpoint for FLOKx alerts. Returns an empty list of alerts.
    """
    return {"alerts": [], "message": "FLOKx alerts not yet implemented"}