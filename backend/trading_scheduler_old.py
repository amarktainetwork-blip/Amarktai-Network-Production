"""
Trading Scheduler - RATE-LIMITED QUALITY TRADING
Trades every 30 minutes per bot to stay within 50 trades/day limit
50 trades/day = 1 trade every 28.8 minutes
Using 30 minutes to be safe = 48 trades/day max
"""

import asyncio
import logging
from datetime import datetime, timezone
from paper_trading_engine import paper_engine
from engines.trading_engine_live import live_trading_engine
from database import bots_collection, trades_collection
from websocket_manager import manager

logger = logging.getLogger(__name__)

class TradingScheduler:
    """QUALITY TRADING - Respects 50 trades/day limit per bot"""
    
    def __init__(self):
        self.is_running = False
        self.task = None
        self.trade_interval = 1800  # 30 minutes = 1800 seconds (48 trades/day max)
        self.last_trade_time = {}  # Track last trade time per bot
        
    async def execute_bot_trades(self):
        """Execute trades for ALL active bots - RESPECTS SYSTEM MODE"""
        try:
            from database import system_modes_collection
            
            # Find ALL paper bots grouped by user
            active_bots = await bots_collection.find(
                {"trading_mode": "paper", "status": "active"},
                {"_id": 0}
            ).to_list(1000)
            
            if not active_bots:
                return
            
            # Check each user's System Mode settings
            users_with_trading = {}
            for bot in active_bots:
                user_id = bot['user_id']
                if user_id not in users_with_trading:
                    # Get user's system modes
                    modes = await system_modes_collection.find_one({"user_id": user_id}, {"_id": 0})
                    
                    # Trading only happens if:
                    # 1. Autopilot is ON (master switch)
                    # 2. Paper Trading is ON
                    if modes and modes.get('autopilot') and modes.get('paperTrading'):
                        users_with_trading[user_id] = True
                    else:
                        users_with_trading[user_id] = False
            
            # Filter bots to only those with trading enabled
            active_bots = [bot for bot in active_bots if users_with_trading.get(bot['user_id'], False)]
            
            if not active_bots:
                return
            
            # Activate all bots
            for bot in active_bots:
                await bots_collection.update_one(
                    {"id": bot['id']},
                    {"$set": {"status": "active"}}
                )
            
            # Execute trades concurrently (WITH TIMING CONTROL)
            tasks = []
            current_time = datetime.now(timezone.utc).timestamp()
            
            for bot in active_bots:
                bot_id = bot['id']
                
                # Check if enough time has passed since last trade (30 minutes)
                last_trade = self.last_trade_time.get(bot_id, 0)
                time_since_last = current_time - last_trade
                
                if time_since_last >= self.trade_interval:
                    # Allowed to trade
                    # Run trading cycle (use live engine for live bots, paper for paper bots)
                    is_paper_mode = bot.get('mode', 'paper') == 'paper'
                    
                    # Check emergency stop
                    system_modes = await system_modes_collection.find_one({})
                    if system_modes and system_modes.get('emergencyStop', False):
                        logger.warning(f"⚠️ Emergency stop active - skipping {bot['name']}")
                        continue
                    
                    if is_paper_mode:
                        # Paper trading with realistic simulation
                        task = paper_engine.run_trading_cycle(
                            bot['id'],
                            bot,
                            {'bots': bots_collection, 'trades': trades_collection}
                        )
                    else:
                        # LIVE TRADING with real orders
                        logger.info(f"🔴 LIVE TRADING: {bot['name']} on {bot.get('exchange')}")
                        
                        # Use live trading engine
                        # Note: This requires proper exchange API keys
                        try:
                            # For now, run paper engine even for "live" bots until full testing
                            # TODO: Switch to live_trading_engine after comprehensive testing
                            task = paper_engine.run_trading_cycle(
                                bot['id'],
                                bot,
                                {'bots': bots_collection, 'trades': trades_collection}
                            )
                            # Future: task = live_trading_engine.execute_full_cycle(bot, db_collections)
                        except Exception as e:
                            logger.error(f"Live trading error for {bot['name']}: {e}")
                            continue
                    
                    if task is not None:
                        tasks.append(task)
                    self.last_trade_time[bot_id] = current_time
                else:
                    # Too soon - skip this cycle
                    logger.debug(f"Skipping {bot['name']} - last trade was {time_since_last/60:.1f} minutes ago")
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Send real-time updates
            for result in results:
                if result and isinstance(result, dict):
                    bot = next((b for b in active_bots if b['id'] == result['bot_id']), None)
                    if bot:
                        # Send trade update to user
                        await manager.send_message(bot['user_id'], {
                            "type": "trade_executed",
                            "bot_id": result['bot_id'],
                            "bot_name": bot['name'],
                            "new_capital": result['new_capital'],
                            "total_profit": result['total_profit'],
                            "trade": result['trade']
                        })
            
            # Send overview profit update to all affected users
            user_profits = {}
            for bot in active_bots:
                user_id = bot['user_id']
                if user_id not in user_profits:
                    user_profits[user_id] = 0
                user_profits[user_id] += bot.get('total_profit', 0)
            
            for user_id, total_profit in user_profits.items():
                await manager.send_message(user_id, {
                    "type": "profit_update",
                    "total_profit": round(total_profit, 2),
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
            
        except Exception as e:
            logger.error(f"Trading error: {e}")
    
    async def run_scheduler(self):
        """QUALITY trading loop - checks every 5 minutes, trades every 30 minutes per bot"""
        logger.info(f"🚀 QUALITY Trading started - bots trade every {self.trade_interval/60:.0f} minutes (max 48 trades/day)")
        
        while self.is_running:
            try:
                await self.execute_bot_trades()
                await asyncio.sleep(300)  # Check every 5 minutes (not every 30 min)
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                await asyncio.sleep(5)
    
    def start(self):
        if not self.is_running:
            self.is_running = True
            self.task = asyncio.create_task(self.run_scheduler())
            logger.info("✅ Trading scheduler started")
    
    def stop(self):
        self.is_running = False
        if self.task:
            self.task.cancel()
        logger.info("🛑 Trading scheduler stopped")

# Global instance
trading_scheduler = TradingScheduler()
