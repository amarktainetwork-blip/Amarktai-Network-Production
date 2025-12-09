"""
Extended AI Commands
Additional 30+ commands for full system control
"""

EXTENDED_COMMANDS = {
    # Bot Performance
    "show_bot_performance": {
        "pattern": ["show bot * performance", "how is bot * doing", "bot * stats"],
        "action": "get_bot_performance",
        "params": ["bot_name"]
    },
    "rank_bots": {
        "pattern": ["rank bots", "which bot is best", "top performing bots"],
        "action": "rank_all_bots",
        "params": []
    },
    "compare_bots": {
        "pattern": ["compare bots", "bot comparison"],
        "action": "compare_bot_performance",
        "params": []
    },
    
    # Capital Management
    "show_capital": {
        "pattern": ["show capital", "my capital", "total capital"],
        "action": "get_capital_summary",
        "params": []
    },
    "reinvest_now": {
        "pattern": ["reinvest", "compound profits", "reinvest profits"],
        "action": "manual_reinvest",
        "params": []
    },
    "update_bot_capital": {
        "pattern": ["set bot * capital to *", "update bot * capital *"],
        "action": "update_capital",
        "params": ["bot_name", "amount"]
    },
    
    # System Status
    "system_status": {
        "pattern": ["system status", "how is system", "system health"],
        "action": "get_system_health",
        "params": []
    },
    "show_profit": {
        "pattern": ["show profit", "total profit", "how much profit"],
        "action": "get_profit_summary",
        "params": []
    },
    "show_trades_today": {
        "pattern": ["trades today", "how many trades today"],
        "action": "get_today_trades",
        "params": []
    },
    
    # Risk Management
    "check_risk": {
        "pattern": ["check risk", "risk level", "am i at risk"],
        "action": "assess_risk",
        "params": []
    },
    "set_stop_loss": {
        "pattern": ["set stop loss * for bot *", "bot * stop loss *"],
        "action": "set_bot_stop_loss",
        "params": ["bot_name", "percentage"]
    },
    
    # Bot Control Extended
    "clone_bot": {
        "pattern": ["clone bot *", "duplicate bot *"],
        "action": "clone_bot",
        "params": ["bot_name"]
    },
    "rename_bot": {
        "pattern": ["rename bot * to *"],
        "action": "rename_bot",
        "params": ["old_name", "new_name"]
    },
    
    # Analytics
    "show_best_day": {
        "pattern": ["best day", "most profitable day"],
        "action": "get_best_trading_day",
        "params": []
    },
    "show_worst_day": {
        "pattern": ["worst day", "biggest loss day"],
        "action": "get_worst_trading_day",
        "params": []
    },
    "monthly_summary": {
        "pattern": ["monthly summary", "this month performance"],
        "action": "get_monthly_summary",
        "params": []
    },
    
    # Learning & Optimization
    "what_did_you_learn": {
        "pattern": ["what did you learn", "yesterday learning", "daily insights"],
        "action": "get_daily_learning",
        "params": []
    },
    "optimize_bot": {
        "pattern": ["optimize bot *", "improve bot *"],
        "action": "optimize_bot_settings",
        "params": ["bot_name"]
    },
    "optimize_all": {
        "pattern": ["optimize everything", "optimize all bots"],
        "action": "optimize_all_bots",
        "params": []
    }
}

# Command help text
COMMAND_HELP = """
📋 AVAILABLE AI COMMANDS

🤖 BOT MANAGEMENT:
  • create bot [name] on [exchange]
  • delete bot [name]
  • pause bot [name] / resume bot [name]
  • pause all / resume all
  • clone bot [name]
  • rename bot [old] to [new]

💰 CAPITAL & PROFITS:
  • show my capital
  • show my profit
  • reinvest profits
  • set bot [name] capital to [amount]

📊 ANALYTICS:
  • rank bots / which bot is best
  • show bot [name] performance
  • compare bots
  • trades today
  • best day / worst day
  • monthly summary

⚙️ SYSTEM CONTROL:
  • turn on/off autopilot
  • enable paper trading / enable live trading
  • emergency stop / resume trading
  • system status / system health

🛡️ RISK MANAGEMENT:
  • check risk
  • set stop loss [%] for bot [name]

🧠 AI FEATURES:
  • what did you learn yesterday
  • optimize bot [name]
  • optimize everything

Type any command to execute it!
"""
