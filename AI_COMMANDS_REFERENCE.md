# 🤖 AI COMMAND REFERENCE - Complete Control System

## Overview
You can control the ENTIRE Amarktai system via natural language in the AI chat.
No need to click buttons - just tell the AI what you want!

---

## 📝 AVAILABLE COMMANDS

### BOT MANAGEMENT

**Create Bot**
- "create a bot called Zeus"
- "make me a new bot named Apollo on Binance"
- "spawn a risky bot with R2000 capital"

**Delete Bot**
- "delete bot Zeus"
- "remove the bot called Apollo"
- "delete all bots" (deletes all your bots)

**Pause/Resume**
- "pause bot Zeus"
- "resume bot Apollo"
- "pause all bots"
- "resume all bots"

**Rename Bot**
- "rename Zeus to Poseidon"

---

### SYSTEM CONTROL

**Toggle Modes**
- "turn on autopilot"
- "disable autopilot"
- "enable paper trading"
- "switch to live trading" (⚠️ REAL MONEY!)

**Emergency Controls**
- "emergency stop" (stops everything immediately)
- "resume trading" (restarts paper mode)

**Admin Panel**
- "show admin" (requires password)
- "hide admin"

---

### ANALYSIS & INSIGHTS

**Performance**
- "analyze performance" (full system analysis)
- "show top performers" (best 5 bots)
- "show bottom performers" (worst 5 bots)
- "run learning analysis" (triggers AI learning)

**Information**
- "what is my profit?" (gets current profit)
- "how many bots do I have?" (bot count)
- "show me today's trades" (recent trades)
- "what's my win rate?" (performance metrics)

---

## 💡 NATURAL LANGUAGE

The AI understands natural variations:
- "make a bot" = "create a bot" = "spawn a bot"
- "turn off" = "disable" = "deactivate"
- "analyze" = "check" = "review"

---

## 🔐 SECURITY

Admin commands require password authentication:
1. Say "show admin"
2. AI asks for password
3. Enter: (configured in frontend)
4. Admin panel appears

---

## 📊 EXAMPLES

**Scenario 1: Quick Bot Creation**
```
You: "create 3 bots on Luno"
AI: ✅ Created Bot-1, Bot-2, Bot-3 on LUNO
```

**Scenario 2: Emergency Stop**
```
You: "emergency stop everything"
AI: 🚨 EMERGENCY STOP - All bots paused, trading disabled
```

**Scenario 3: Performance Check**
```
You: "how am I doing?"
AI: Your profit is R1,234.56 (12.3% ROI). You have 5 active bots with a 58% win rate.
```

---

## 🚀 PRO TIPS

1. **Batch Commands**: "create 5 bots and enable autopilot"
2. **Context Aware**: AI remembers your conversation
3. **Error Handling**: If command fails, AI explains why
4. **Real-Time**: Changes reflect immediately on dashboard

---

## 🛠️ TROUBLESHOOTING

**Command not working?**
- Check if you're logged in
- Ensure correct spelling
- Try rephrasing naturally
- Check browser console for errors

**AI not responding?**
- Check backend logs: `tail -f /var/log/supervisor/backend.err.log`
- Verify EMERGENT_LLM_KEY is set
- Restart backend: `sudo supervisorctl restart backend`

---

*Last Updated: Dec 2024*
*System Version: 2.0 - Full AI Control*