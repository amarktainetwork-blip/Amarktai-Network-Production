"""
AI Data Processor Engine
- Responsible for gathering, cleaning, and structuring data for the AI Decision Engine.
- Focuses on providing a concise, high-quality data payload.
"""

import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List
from backend.logger_config import logger
from backend.database import trades_collection, bots_collection
from backend.ccxt_service import ccxt_service # For real-time market data

class AIDataProcessor:
    def __init__(self):
        pass

    async def get_market_data(self, exchange: str, pair: str, timeframe: str = '1h', limit: int = 100) -> List[Dict]:
        """
        Fetches historical OHLCV data for a given pair and exchange.
        """
        try:
            # Placeholder for actual CCXT implementation
            # In a real system, this would call ccxt_service.fetch_ohlcv
            
            # For now, simulate data structure
            simulated_data = []
            now = datetime.now(timezone.utc)
            for i in range(limit):
                timestamp = int((now - timedelta(hours=i)).timestamp() * 1000)
                simulated_data.append({
                    'timestamp': timestamp,
                    'open': 100000 + (i * 10),
                    'high': 100000 + (i * 10) + 50,
                    'low': 100000 + (i * 10) - 50,
                    'close': 100000 + (i * 10) + 20,
                    'volume': 100 + (i * 0.5)
                })
            
            # Reverse to be chronological (oldest first)
            return simulated_data[::-1]
        except Exception as e:
            logger.error(f"Error fetching market data for {exchange}/{pair}: {e}")
            return []

    async def get_bot_performance_summary(self, bot_id: str) -> Dict:
        """
        Generates a summary of the bot's recent performance.
        """
        try:
            trades = await trades_collection.find(
                {"bot_id": bot_id},
                {"_id": 0, "profit_loss": 1, "timestamp": 1}
            ).sort("timestamp", -1).to_list(50) # Last 50 trades

            if not trades:
                return {"trades_count": 0, "win_rate": 0, "avg_profit": 0}

            winning_trades = sum(1 for t in trades if t.get('profit_loss', 0) > 0)
            total_profit = sum(t.get('profit_loss', 0) for t in trades)
            
            return {
                "trades_count": len(trades),
                "win_rate": round(winning_trades / len(trades), 4),
                "avg_profit": round(total_profit / len(trades), 2),
                "last_trade_time": trades[0]['timestamp'] if trades else None
            }
        except Exception as e:
            logger.error(f"Error getting bot performance summary for {bot_id}: {e}")
            return {"trades_count": 0, "win_rate": 0, "avg_profit": 0}

    async def get_ai_input_payload(self, bot: Dict) -> Dict[str, Any]:
        """
        Compiles the final data payload for the AI Decision Engine.
        """
        try:
            exchange = bot.get('exchange', 'luno')
            pair = bot.get('trading_pair', 'BTC/ZAR')
            
            # 1. Market Data (e.g., last 100 1-hour candles)
            market_data = await self.get_market_data(exchange, pair, timeframe='1h', limit=100)
            
            # 2. Bot Performance
            performance_summary = await self.get_bot_performance_summary(bot['id'])
            
            # 3. System Context
            system_context = {
                "current_capital": bot.get('current_capital', 1000),
                "risk_mode": bot.get('risk_mode', 'safe'),
                "trading_mode": bot.get('trading_mode', 'paper'),
                "ai_model_version": bot.get('ai_model_version', 'v1.0')
            }
            
            return {
                "success": True,
                "exchange": exchange,
                "pair": pair,
                "market_data": market_data,
                "performance_summary": performance_summary,
                "system_context": system_context
            }
        except Exception as e:
            logger.error(f"Error compiling AI input payload for bot {bot['id']}: {e}")
            return {"success": False, "error": str(e)}

# Global instance
ai_data_processor = AIDataProcessor()
