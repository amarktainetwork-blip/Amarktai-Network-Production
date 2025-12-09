"""
AI Chat Handler - Intelligent System Control
Makes AI chat aware of full system state and able to execute commands
"""

from database import bots_collection, users_collection, system_modes_collection, trades_collection
from logger_config import logger
from emergentintegrations.llm.chat import LlmChat, UserMessage
import os


class AIChatHandler:
    def __init__(self):
        self.api_key = os.environ.get('EMERGENT_LLM_KEY')
        
    async def get_system_context(self, user_id: str) -> str:
        """Get comprehensive system state for AI"""
        try:
            # Get user info
            user = await users_collection.find_one({"id": user_id}, {"_id": 0})
            
            # Get all bots
            bots = await bots_collection.find({"user_id": user_id}, {"_id": 0}).to_list(100)
            active_bots = [b for b in bots if b.get('status') == 'active']
            paper_bots = [b for b in active_bots if b.get('trading_mode') == 'paper']
            live_bots = [b for b in active_bots if b.get('trading_mode') == 'live']
            
            # Get system modes
            modes = await system_modes_collection.find_one({"user_id": user_id}, {"_id": 0})
            
            # Calculate total capital and profit
            total_capital = sum(b.get('current_capital', 0) for b in active_bots)
            total_initial = sum(b.get('initial_capital', 0) for b in active_bots)
            total_profit = total_capital - total_initial
            
            # Get today's trades
            from datetime import datetime, timezone as tz
            today_start = datetime.now(tz.utc).replace(hour=0, minute=0, second=0).isoformat()
            trades_today = await trades_collection.count_documents({
                "user_id": user_id,
                "timestamp": {"$gte": today_start}
            })
            
            context = f"""SYSTEM STATUS:
User: {user.get('first_name', 'User')} ({user.get('email')})

BOTS:
- Total Active: {len(active_bots)} bots
- Paper Mode: {len(paper_bots)} bots
- Live Mode: {len(live_bots)} bots

CAPITAL:
- Total Capital: R{total_capital:,.2f}
- Total Profit: R{total_profit:,.2f}
- Return: {(total_profit/total_initial*100) if total_initial > 0 else 0:.2f}%

MODES:
- Autopilot: {'ON' if modes and modes.get('autopilot') else 'OFF'}
- Paper Trading: {'ON' if modes and modes.get('paperTrading') else 'OFF'}
- Live Trading: {'ON' if modes and modes.get('liveTrading') else 'OFF'}

TODAY'S ACTIVITY:
- Trades Executed: {trades_today}

COMMANDS YOU CAN EXECUTE:
- "show admin" / "hide admin" - Toggle admin panel
- "create bot [name]" - Create new bot
- "turn on/off [autopilot/paper/live]" - Toggle modes
- System already has: {len(active_bots)} active bots, modes configured
"""
            return context
            
        except Exception as e:
            logger.error(f"System context error: {e}")
            return "SYSTEM STATUS: Unable to fetch current state"
    
    async def process_command(self, user_id: str, message: str) -> dict:
        """Process user command and ACTUALLY EXECUTE IT"""
        message_lower = message.lower().strip()
        
        # Admin commands
        if "show admin" in message_lower:
            return {
                "type": "admin_command",
                "action": "show",
                "response": "Please enter the admin password to access the admin panel."
            }
        
        if "hide admin" in message_lower:
            return {
                "type": "admin_command",
                "action": "hide",
                "response": "Please enter the admin password to hide the admin panel."
            }
        
        # Bot creation
        if "create bot" in message_lower or "add bot" in message_lower:
            try:
                from uuid import uuid4
                from datetime import datetime, timezone, timedelta
                
                # Extract bot name if provided
                bot_name = "AI-Bot"
                if "create bot" in message_lower:
                    parts = message_lower.split("create bot")
                    if len(parts) > 1 and parts[1].strip():
                        bot_name = parts[1].strip().title()
                
                # Create bot in database
                new_bot = {
                    "id": str(uuid4()),
                    "user_id": user_id,
                    "name": bot_name,
                    "status": "active",
                    "exchange": "luno",
                    "pair": "BTC/ZAR",
                    "risk_mode": "safe",
                    "initial_capital": 1000,
                    "current_capital": 1000,
                    "trading_mode": "paper",
                    "trades_count": 0,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "paper_end_date": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
                }
                await bots_collection.insert_one(new_bot)
                
                return {
                    "type": "bot_creation",
                    "response": f"✅ Successfully created '{bot_name}' bot with R1,000 capital on Luno (Paper Mode for 7 days)!"
                }
            except Exception as e:
                logger.error(f"Bot creation error: {e}")
                return {
                    "type": "bot_creation",
                    "response": f"❌ Failed to create bot: {str(e)}"
                }
        
        # Mode toggles - ACTUALLY EXECUTE THEM
        if "turn on autopilot" in message_lower or "enable autopilot" in message_lower or "autopilot on" in message_lower:
            try:
                await system_modes_collection.update_one(
                    {"user_id": user_id},
                    {"$set": {"autopilot": True}},
                    upsert=True
                )
                return {
                    "type": "mode_toggle",
                    "mode": "autopilot",
                    "enabled": True,
                    "response": "✅ Autopilot mode is NOW ON! The system will automatically reinvest profits and spawn new bots."
                }
            except Exception as e:
                logger.error(f"Autopilot enable error: {e}")
                return {
                    "type": "mode_toggle",
                    "response": f"❌ Failed to enable autopilot: {str(e)}"
                }
        
        if "turn off autopilot" in message_lower or "disable autopilot" in message_lower or "autopilot off" in message_lower:
            try:
                await system_modes_collection.update_one(
                    {"user_id": user_id},
                    {"$set": {"autopilot": False}},
                    upsert=True
                )
                return {
                    "type": "mode_toggle",
                    "mode": "autopilot",
                    "enabled": False,
                    "response": "✅ Autopilot mode is NOW OFF!"
                }
            except Exception as e:
                logger.error(f"Autopilot disable error: {e}")
                return {
                    "type": "mode_toggle",
                    "response": f"❌ Failed to disable autopilot: {str(e)}"
                }
        
        # Paper Trading toggle
        if "turn on paper" in message_lower or "enable paper" in message_lower:
            try:
                await system_modes_collection.update_one(
                    {"user_id": user_id},
                    {"$set": {"paperTrading": True}},
                    upsert=True
                )
                return {
                    "type": "mode_toggle",
                    "response": "✅ Paper Trading mode is NOW ON!"
                }
            except Exception as e:
                return {"type": "mode_toggle", "response": f"❌ Failed: {str(e)}"}
        
        if "turn off paper" in message_lower or "disable paper" in message_lower:
            try:
                await system_modes_collection.update_one(
                    {"user_id": user_id},
                    {"$set": {"paperTrading": False}},
                    upsert=True
                )
                return {
                    "type": "mode_toggle",
                    "response": "✅ Paper Trading mode is NOW OFF!"
                }
            except Exception as e:
                return {"type": "mode_toggle", "response": f"❌ Failed: {str(e)}"}
        
        # If no command detected, it's a general question
        return {"type": "question", "response": None}
    
    async def get_ai_response(self, user_id: str, message: str) -> str:
        """Get intelligent AI response with system awareness"""
        try:
            # First check if it's a command
            command_result = await self.process_command(user_id, message)
            
            if command_result['type'] != 'question':
                return command_result['response']
            
            # It's a question - get system context and ask AI
            system_context = await self.get_system_context(user_id)
            
            # Get current date/time
            from datetime import datetime, timezone
            current_time = datetime.now(timezone.utc)
            date_str = current_time.strftime("%A, %B %d, %Y")
            time_str = current_time.strftime("%H:%M:%S UTC")
            
            # Use OpenAI GPT-4o for chat with conversation memory
            chat = LlmChat(
                api_key=self.api_key,
                session_id=f"chat_{user_id}",
                system_message=f"""You are Amarktai AI Assistant, an expert in cryptocurrency trading and the Amarktai trading system.

CURRENT DATE & TIME: {date_str} at {time_str}

{system_context}

IMPORTANT INSTRUCTIONS:
- You have full knowledge of the user's system state shown above
- Answer questions accurately using EXACT numbers from the system status
- You have conversation memory through your session
- When asked about time/date, use the current date/time shown above
- Be helpful, concise, and professional
- If user asks what you talked about before, you SHOULD remember (you have session memory)

AVAILABLE COMMANDS (tell user these work):
- "turn on autopilot" / "turn off autopilot" - I will ACTUALLY execute this
- "create bot [name]" - I will ACTUALLY create a bot
- "turn on paper" / "turn off paper" - I will ACTUALLY toggle paper trading
- Ask me anything about the system and I'll answer with accurate data"""
            ).with_model("openai", "gpt-4o")
            
            response = await chat.send_message(UserMessage(text=message))
            # Response can be a string or object with .text attribute
            if isinstance(response, str):
                return response
            return response.text if hasattr(response, 'text') else str(response)
            
        except Exception as e:
            logger.error(f"AI response error: {e}")
            return "I'm having trouble processing that request right now. Please try again or contact support."


# Global instance
ai_chat_handler = AIChatHandler()
