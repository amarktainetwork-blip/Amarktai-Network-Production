"""
Basic Autopilot Engine
Handles profit reinvestment and basic automation
"""
import asyncio
from datetime import datetime, timezone
from database import bots_collection, system_modes_collection
from engines.bot_manager import bot_manager
from logger_config import logger
from config import REINVEST_THRESHOLD_ZAR, NEW_BOT_CAPITAL, MAX_TOTAL_BOTS, EXCHANGE_BOT_LIMITS


class AutopilotBasic:
    def __init__(self):
        self.is_running = False
        self.task = None
    
    async def check_and_reinvest(self, user_id: str):
        """Check profits and reinvest if threshold met"""
        try:
            # Get user's autopilot status
            modes = await system_modes_collection.find_one({"user_id": user_id}, {"_id": 0})
            
            if not modes or not modes.get('autopilot'):
                return
            
            # Get all bots
            bots = await bots_collection.find({"user_id": user_id}, {"_id": 0}).to_list(1000)
            
            # Calculate total profit
            total_profit = sum(b.get('total_profit', 0) for b in bots)
            
            if total_profit < REINVEST_THRESHOLD_ZAR:
                return
            
            # Check if we can create more bots
            if len(bots) >= MAX_TOTAL_BOTS:
                # Reinvest in top performers
                top_bots = sorted(bots, key=lambda b: b.get('total_profit', 0), reverse=True)[:5]
                
                reinvest_per_bot = total_profit / 5
                
                for bot in top_bots:
                    new_capital = bot.get('current_capital', 0) + reinvest_per_bot
                    await bots_collection.update_one(
                        {"id": bot['id']},
                        {"$set": {"current_capital": new_capital}}
                    )
                
                logger.info(f"💰 Autopilot: Reinvested R{total_profit:.2f} into top 5 bots")
            
            else:
                # Create new bot if profit >= R1000
                if total_profit >= NEW_BOT_CAPITAL:
                    # Find exchange with space
                    for exchange, limit in EXCHANGE_BOT_LIMITS.items():
                        exchange_bots = len([b for b in bots if b.get('exchange') == exchange])
                        if exchange_bots < limit:
                            # Create new bot
                            bot_number = len(bots) + 1
                            result = await bot_manager.create_bot(
                                user_id=user_id,
                                name=f"Auto-Bot-{bot_number}",
                                exchange=exchange,
                                risk_mode='safe',
                                capital=NEW_BOT_CAPITAL
                            )
                            
                            if result['success']:
                                logger.info(f"🤖 Autopilot: Created new bot on {exchange}")
                                # Reset profit counter
                                await bots_collection.update_many(
                                    {"user_id": user_id},
                                    {"$set": {"total_profit": 0}}
                                )
                            break
        
        except Exception as e:
            logger.error(f"Autopilot reinvest error: {e}")
    
    async def autopilot_loop(self):
        """Main autopilot loop - runs every hour"""
        logger.info("🤖 Autopilot engine started")
        
        while self.is_running:
            try:
                # Get all users with autopilot enabled
                users = await system_modes_collection.find({"autopilot": True}, {"_id": 0}).to_list(1000)
                
                for user in users:
                    user_id = user.get('user_id')
                    if user_id:
                        await self.check_and_reinvest(user_id)
                
                # Wait 1 hour
                await asyncio.sleep(3600)
            
            except Exception as e:
                logger.error(f"Autopilot loop error: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes on error
    
    def start(self):
        """Start autopilot engine"""
        if not self.is_running:
            self.is_running = True
            self.task = asyncio.create_task(self.autopilot_loop())
            logger.info("✅ Autopilot engine started")
    
    def stop(self):
        """Stop autopilot engine"""
        self.is_running = False
        if self.task:
            self.task.cancel()
        logger.info("⏹️ Autopilot engine stopped")


autopilot_basic = AutopilotBasic()
