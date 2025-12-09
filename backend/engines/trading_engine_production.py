"""
Production Trading Engine (Live)
================================

This engine manages the lifecycle of live trading positions. It is responsible
for:
1. Checking for open positions and managing their exit (SL/TP/AI).
2. Executing new trade entries based on AI decisions.
3. Interacting with the CCXT service for real order execution.
4. Recording all actions using the new Position and TradeHistory models.
"""
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional
import logging

from backend.models import Bot, Position, TradeHistory
from backend.database import bots_collection, positions_collection, trades_collection, api_keys_collection
from backend.ccxt_service import ccxt_service
from backend.logger_config import logger
from .trade_limiter import trade_limiter
from .ai_decision_engine import ai_decision_engine
from .risk_engine import risk_engine # For checking SL/TP/TS
from backend.realtime_events import rt_events

class TradingEngineProduction:
    
    def __init__(self):
        self.is_running = False
        self.loop_task = None
    
    def start(self):
        if not self.is_running:
            self.is_running = True
            self.loop_task = asyncio.create_task(self._trading_loop())
            logger.info("Live Trading Engine started.")

    def stop(self):
        if self.is_running and self.loop_task:
            self.is_running = False
            self.loop_task.cancel()
            logger.info("Live Trading Engine stopped.")

    async def _trading_loop(self):
        while self.is_running:
            try:
                # 1. Manage open positions (check for exit conditions)
                await self._manage_open_positions()
                
                # 2. Execute new trades for bots without open positions
                await self._execute_new_trades()
                
                # Trade check every 5 minutes
                await asyncio.sleep(300) 
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Live Trading Engine error: {e}")
                await asyncio.sleep(60)

    async def _manage_open_positions(self):
        """Checks open live positions for exit conditions (SL/TP/AI)."""
        open_positions_cursor = positions_collection.find({"trading_mode": "live", "status": "open"})
        open_positions = await open_positions_cursor.to_list(length=None)
        
        for pos_data in open_positions:
            position = Position(**pos_data)
            
            # Get current price
            current_price = await ccxt_service.get_current_price(position.exchange, position.pair)
            
            if ccxt_service.is_fallback_price(current_price):
                logger.warning(f"Skipping live position management for {position.id} due to fallback price.")
                continue
            
            # 1. Check Risk Engine for Exit Signal (SL/TP/TS/Circuit Breaker)
            exit_signal, exit_reason = await risk_engine.check_exit_conditions(position, current_price)
            
            # 2. Check AI for Exit Signal (e.g., market regime change)
            ai_exit_signal, ai_reasoning = await ai_decision_engine.get_exit_decision(position, current_price)
            
            if exit_signal or ai_exit_signal:
                final_reason = exit_reason if exit_signal else ai_reasoning
                await self._execute_live_exit(position, current_price, final_reason)

    async def _execute_new_trades(self):
        """Executes new live trades based on AI decisions for eligible bots."""
        # Find all live bots that are active and do not have an open position
        pipeline = [
            {"$match": {"trading_mode": "live", "status": "live"}},
            {"$lookup": {
                "from": "positions",
                "localField": "id",
                "foreignField": "bot_id",
                "as": "open_positions",
                "pipeline": [{"$match": {"status": "open"}}]
            }},
            {"$match": {"open_positions": {"$size": 0}}}
        ]
        
        eligible_bots_cursor = bots_collection.aggregate(pipeline)
        eligible_bots = await eligible_bots_cursor.to_list(length=None)
        
        for bot_data in eligible_bots:
            bot = Bot(**bot_data)
            
            # 1. Check Rate Limiter
            can_trade, reason = await trade_limiter.can_trade(bot.id)
            if not can_trade:
                logger.debug(f"Bot {bot.name} cannot trade: {reason}")
                continue
            
            # 2. Get AI Decision
            ai_decision = await ai_decision_engine.get_trade_decision(bot)
            decision = ai_decision.get('decision', 'SKIP')
            
            if decision in ["BUY", "SELL"]:
                await self._execute_live_entry(bot, decision, ai_decision)

    async def _execute_live_entry(self, bot: Bot, side: str, ai_decision: Dict[str, Any]):
        """Executes a live trade entry via CCXT."""
        
        # 1. Get API Client
        api_key_doc = await api_keys_collection.find_one(
            {"user_id": bot.user_id, "provider": bot.exchange}, {"api_key": 1, "secret_key": 1}
        )
        if not api_key_doc:
            logger.error(f"No API keys configured for user {bot.user_id} on {bot.exchange}")
            return
        
        try:
            client = await ccxt_service.init_auth_client(
                bot.exchange, api_key_doc['api_key'], api_key_doc['secret_key']
            )
        except Exception as e:
            logger.error(f"Failed to initialize auth client for {bot.exchange}: {e}")
            return

        # 2. Determine Trade Size and Price
        current_price = await ccxt_service.get_current_price(bot.exchange, bot.trading_pair)
        if ccxt_service.is_fallback_price(current_price):
            logger.warning(f"Skipping live entry for {bot.name} due to fallback price.")
            return
            
        # Trade size logic (e.g., 10% of allocated capital)
        trade_capital = bot.total_capital_allocated * 0.1
        amount = trade_capital / current_price
        
        # 3. Check Exchange Limits (Min Amount/Cost)
        if not await ccxt_service.check_trade_limits(bot.exchange, bot.trading_pair, amount, current_price):
            logger.warning(f"Trade for {bot.name} failed limit check.")
            return
            
        # 4. Execute Order
        try:
            order = await ccxt_service.create_order(
                client,
                bot.trading_pair,
                side=side.lower(),
                amount=amount,
                price=current_price # Use limit order at current price for better fill control
            )
            
            # 5. Record Position
            new_position = Position(
                bot_id=bot.id,
                user_id=bot.user_id,
                exchange=bot.exchange,
                pair=bot.trading_pair,
                side=side.lower(),
                entry_price=float(order.get('price', current_price)),
                entry_qty=float(order.get('filled', amount)),
                entry_order_id=order.get('id'),
                trading_mode="live",
                ai_reasoning=ai_decision.get('reasoning', 'AI decision.')
            )
            
            await positions_collection.insert_one(new_position.model_dump())
            await trade_limiter.record_trade(bot.id)
            logger.info(f"Live Entry: {bot.name} {side} {new_position.entry_qty:.4f} {bot.trading_pair} @ {new_position.entry_price:.2f}")
            
            # 6. Real-Time Event Broadcast
            await rt_events.broadcast_trade_event(
                user_id=bot.user_id,
                event_type="new_trade",
                symbol=bot.trading_pair,
                side=side,
                price=new_position.entry_price,
                qty=new_position.entry_qty
            )
            
            # 6. Set Risk Parameters (SL/TP/TS) - Handled by Risk Engine in the next phase
            
        except Exception as e:
            logger.error(f"Live order execution failed for {bot.name}: {e}")

    async def _execute_live_exit(self, position: Position, exit_price: float, exit_reason: str):
        """Executes a live trade exit via CCXT."""
        
        # 1. Get API Client
        api_key_doc = await api_keys_collection.find_one(
            {"user_id": position.user_id, "provider": position.exchange}, {"api_key": 1, "secret_key": 1}
        )
        if not api_key_doc:
            logger.error(f"No API keys configured for user {position.user_id} on {position.exchange}")
            return
        
        try:
            client = await ccxt_service.init_auth_client(
                position.exchange, api_key_doc['api_key'], api_key_doc['secret_key']
            )
        except Exception as e:
            logger.error(f"Failed to initialize auth client for {position.exchange}: {e}")
            return

        # 2. Determine Exit Side (opposite of entry side)
        exit_side = 'sell' if position.side == 'buy' else 'buy'
        
        # 3. Execute Order (Market order for quick exit)
        try:
            order = await ccxt_service.create_order(
                client,
                position.pair,
                side=exit_side,
                amount=position.entry_qty,
                type='market'
            )
            
            # 4. Calculate PnL and Fees (Simplified for now, real data from exchange response)
            exit_qty = float(order.get('filled', position.entry_qty))
            exit_price_actual = float(order.get('price', exit_price))
            
            pnl_gross = (exit_price_actual - position.entry_price) * exit_qty
            fees = float(order.get('fee', {}).get('cost', 0.0)) # Use actual fee from exchange
            pnl_net = pnl_gross - fees
            
            # 5. Create TradeHistory record
            trade_history = TradeHistory(
                position_id=position.id,
                bot_id=position.bot_id,
                user_id=position.user_id,
                exchange=position.exchange,
                pair=position.pair,
                side=position.side,
                entry_price=position.entry_price,
                exit_price=exit_price_actual,
                qty=exit_qty,
                entry_time=position.entry_time,
                profit_loss=pnl_net,
                fees=fees,
                trading_mode="live",
                exit_reason=exit_reason,
                ai_reasoning=position.ai_reasoning
            )
            
            await trades_collection.insert_one(trade_history.model_dump())
            
            # 6. Update Bot stats (Capital update handled by Capital Allocator in next phase)
            is_win = pnl_net > 0
            await bots_collection.update_one(
                {"id": position.bot_id},
                {"$inc": {
                    "total_profit": pnl_net,
                    "win_count": 1 if is_win else 0,
                    "loss_count": 0 if is_win else 1,
                    "trades_count": 1
                }, "$set": {"last_trade_time": datetime.now(timezone.utc).isoformat()}}
            )
            
            # 7. Mark position as closed
            await positions_collection.update_one(
                {"id": position.id},
                {"$set": {"status": "closed"}}
            )
            
            logger.info(f"Live Exit: {position.bot_id} {exit_reason} PnL: {pnl_net:.2f}")
            
            # 8. Real-Time Event Broadcast
            await rt_events.broadcast_trade_event(
                user_id=position.user_id,
                event_type="closed_trade",
                symbol=position.pair,
                side=exit_side,
                price=exit_price_actual,
                qty=exit_qty,
                pnl=pnl_net
            )
            
        except Exception as e:
            logger.error(f"Live order exit failed for {position.bot_id}: {e}")

trading_engine = TradingEngineProduction()
