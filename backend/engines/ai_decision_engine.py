"""
AI Decision Engine
==================

The core intelligence for trade execution and bot lifecycle management.
- Generates a trade decision (BUY/SELL/HOLD).
- Approves or rejects bot promotion (Paper -> Candidate).
"""

import asyncio
from typing import Dict, Any, Tuple, Optional
from backend.logger_config import logger
from .ai_model_router import ai_model_router
from .ai_data_processor import ai_data_processor
from backend.models import Bot, Position

class AIDecisionEngine:
    
    def __init__(self):
        self.trade_system_prompt = (
            "You are the Amarktai AI Decision Engine, a highly sophisticated, risk-averse, "
            "algorithmic trading expert. Your sole function is to analyze the provided market "
            "data and bot performance summary to determine the optimal trade action. "
            "You must respond ONLY with a JSON object containing the 'decision' (BUY, SELL, HOLD), "
            "a 'confidence' score (0.0 to 1.0), and a brief 'reasoning' (max 50 words). "
            "Prioritize capital preservation and only recommend a trade if the confidence is above 0.7."
        )
        
        self.promotion_system_prompt = (
            "You are the Amarktai AI Promotion Auditor. Your task is to review a bot's paper trading "
            "performance and determine if it is safe and ready to be promoted to 'candidate' status. "
            "Analyze the metrics (win rate, profit, trades) and the market context. "
            "Respond ONLY with a JSON object containing 'approved' (boolean), and a 'reasoning' (max 100 words). "
            "Reject promotion if the bot shows signs of over-fitting, inconsistent performance, or if the current "
            "market regime is too volatile for a new bot."
        )

    async def get_trade_decision(self, bot: Bot) -> Dict[str, Any]:
        """Generates a trade decision for a specific bot using the AI model."""
        try:
            # 1. Get the processed data payload
            data_payload = await ai_data_processor.get_ai_input_payload(bot)
            
            if not data_payload.get('success'):
                logger.error(f"Failed to get data payload for bot {bot.id}")
                return {"decision": "HOLD", "confidence": 0.0, "reasoning": "Data acquisition failed."}

            # 2. Construct the prompt for the LLM
            prompt = (
                f"Analyze the following data for bot '{bot.name}' trading {bot.trading_pair} on {bot.exchange}. "
                f"The bot is in {bot.trading_mode} mode with {bot.risk_mode} risk.\n\n"
                f"Market Data (OHLCV, last 100 hours):\n{data_payload['market_data']}\n\n"
                f"Bot Performance Summary:\n{data_payload['performance_summary']}\n\n"
                "Based on this, what is the optimal trade action (BUY, SELL, HOLD)? "
                "Respond ONLY with the required JSON format."
            )

            # 3. Call the AI model
            ai_response = await ai_model_router.get_json_response(
                user_id=bot.user_id,
                system_prompt=self.trade_system_prompt,
                user_prompt=prompt,
                model_key="trade_decision"
            )
            
            # 4. Validate and return the decision
            decision = ai_response.get('decision', 'HOLD').upper()
            confidence = float(ai_response.get('confidence', 0.0))
            reasoning = ai_response.get('reasoning', 'No reasoning provided.')
            
            # Enforce confidence threshold
            if confidence < 0.7 and decision != 'HOLD':
                decision = 'HOLD'
                reasoning = f"Confidence ({confidence:.2f}) too low for trade. Defaulting to HOLD."

            return {
                "decision": decision,
                "confidence": confidence,
                "reasoning": reasoning
            }

        except Exception as e:
            logger.error(f"AI Decision Engine error for bot {bot.id}: {e}")
            return {"decision": "HOLD", "confidence": 0.0, "reasoning": f"Internal error: {e}"}

    async def get_promotion_approval(self, bot: Bot) -> Dict[str, Any]:
        """Generates an AI approval decision for bot promotion."""
        try:
            # 1. Get the processed data payload
            data_payload = await ai_data_processor.get_ai_input_payload(bot)
            
            # 2. Construct the prompt for the LLM
            prompt = (
                f"Review the paper trading performance for bot '{bot.name}' on {bot.exchange} "
                f"which has met the minimum criteria (7 days, {bot.trades_count} trades, {bot.win_count} wins, {bot.total_profit:.2f} profit).\n\n"
                f"Bot Performance Summary:\n{data_payload['performance_summary']}\n\n"
                f"Market Context During Training:\n{data_payload['market_data']}\n\n"
                "Should this bot be approved for promotion to 'candidate' status? "
                "Respond ONLY with the required JSON format."
            )

            # 3. Call the AI model
            ai_response = await ai_model_router.get_json_response(
                user_id=bot.user_id,
                system_prompt=self.promotion_system_prompt,
                user_prompt=prompt,
                model_key="system_brain" # Use the more powerful system brain for this critical decision
            )
            
            # 4. Validate and return the decision
            approved = ai_response.get('approved', False)
            reasoning = ai_response.get('reasoning', 'No reasoning provided.')
            
            return {
                "approved": approved,
                "reasoning": reasoning
            }

        except Exception as e:
            logger.error(f"AI Promotion Approval error for bot {bot.id}: {e}")
            return {"approved": False, "reasoning": f"Internal error during AI review: {e}"}

    async def get_exit_decision(self, position: Position, current_price: float) -> Tuple[bool, Optional[str]]:
        """Generates an AI decision to exit an open position (e.g., market regime change)."""
        # This is a placeholder for a future, more complex AI feature.
        # For now, AI only exits if the market regime has violently changed against the position.
        
        # 1. Get the processed data payload (simplified)
        bot_data = await ai_data_processor.get_bot_data(position.bot_id)
        if not bot_data:
            return False, None
        
        # 2. Check if the current price is significantly against the position
        entry_price = position.entry_price
        pnl_pct = (current_price - entry_price) / entry_price
        
        # If the position is losing more than 5% (and SL hasn't hit yet), ask the AI
        if pnl_pct < -0.05:
            # Construct a prompt for the LLM
            prompt = (
                f"The bot '{bot_data.get('name')}' has an open {position.side} position in {position.pair} @ {entry_price:.2f}. "
                f"The current price is {current_price:.2f}, resulting in a {pnl_pct*100:.2f}% loss. "
                "Analyze the current market data and determine if an immediate, emergency exit is required to prevent further loss. "
                "Respond ONLY with a JSON object containing 'exit_now' (boolean) and a 'reasoning' (max 50 words)."
            )
            
            try:
                ai_response = await ai_model_router.get_json_response(
                    user_id=position.user_id,
                    system_prompt=self.trade_system_prompt,
                    user_prompt=prompt,
                    model_key="trade_decision"
                )
                
                if ai_response.get('exit_now', False):
                    return True, f"AI_EMERGENCY_EXIT: {ai_response.get('reasoning', 'Market instability.')}"
            except Exception as e:
                logger.error(f"AI Emergency Exit error: {e}")
        
        return False, None

# Global instance
ai_decision_engine = AIDecisionEngine()
