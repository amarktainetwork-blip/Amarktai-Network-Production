# COMPLETE TODO LIST - Amarktai Network Production Readiness

## 🔴 P0 - CRITICAL (Must Fix Immediately)

### 1. Show/Hide Admin Command - BROKEN (Recurring Issue #100+)
- **Status:** NOT WORKING
- **What:** User types "show admin", enters password, admin panel should appear
- **Current State:** Backend blocks command correctly, but frontend logic may have state/timing issues
- **Fix Needed:** Debug frontend React state flow, ensure `setShowAdmin(true)` properly triggers nav link visibility
- **Test:** Type "show admin" → enter password → admin tab should appear in nav → click it → see admin panel

### 2. Bot Management Runtime Error
- **Status:** BROKEN
- **What:** Clicking "Bot Management" section gives runtime error
- **Fix Needed:** Check console errors, trace the error in renderBots() function
- **Test:** Click "🤖 Bot Management" → should load without errors

### 3. Bot Setup Error Message on Success
- **Status:** BROKEN (Says fail but bots are created)
- **What:** Bot creation shows error message even when bots are successfully created
- **Root Cause:** Response handling in frontend - might be checking wrong field or error state
- **Fix Needed:** Check frontend handleBatchCreate success handling in Dashboard.js around line 998
- **Test:** Create bots → should show success message → refresh → bots should exist

---

## 🟡 P1 - HIGH PRIORITY (Fix After P0)

### 4. AI System Reset Incomplete
- **What:** "Best Day" and "Avg Day" stats don't clear after reset
- **Investigation:** Backend deletes trades correctly, stats calculated from trades
- **Fix Needed:** Test reset command end-to-end, verify frontend reloads profit data
- **Test:** Reset system → check profit graphs → should show zeros

### 5. AI Feature Buttons Not Working
- **What:** "Evolve Bots", "AI Insights", etc. buttons do nothing
- **Fix Needed:** Implement backend endpoints for AI features
- **Test:** Click each AI button → should trigger AI action or show response

### 6. Flokx Section Runtime Error (Pending Verification)
- **Status:** Fix applied (optional chaining), needs user verification
- **Test:** Click Flokx section → should load without crash

### 7. Duplicate Trade Display (Pending Verification)
- **Status:** Fix applied (removed duplicate WebSocket handler), needs verification
- **Test:** Make trades → should appear once in UI

---

## 🟢 P2 - IMPORTANT (UX & Features)

### 8. Wallet Hub UX Redesign
- **Current:** New component created but not styled to match dashboard
- **Required:** Implement user's comprehensive wallet spec (see detailed requirements below)
- **Components Needed:**
  - Dashboard Wallet Overview Card (total equity, per-exchange summary, health badges)
  - Dedicated Wallet Section (detailed table, drill-down panels, graphs)
  - Exchange status strip with connection indicators
  - Per-exchange bot allocation display
  - Capital movement history/timeline
  - 7-day paper mode status banner
  - Go-Live confirmation modal
- **Styling:** Must match existing dashboard glass/dark theme

### 9. Emergency Stop UI
- **What:** Create emergency stop button
- **Endpoint:** Already exists `/api/system/emergency-stop`
- **Fix Needed:** Add button to dashboard, wire to endpoint
- **Test:** Click emergency stop → all trading should pause

### 10. System Health LED Indicators
- **What:** Visual health indicators for system components
- **Endpoint:** Already exists `/api/system/health/indicators`
- **Fix Needed:** Create UI component to display health data
- **Test:** View health LEDs → should show real-time system status

---

## 📊 WALLET REDESIGN - DETAILED REQUIREMENTS

### Dashboard Level (Always Visible)

**Wallet Overview Card:**
```
💰 Wallet Overview
Total Equity (All Exchanges): R 23,450

🏦 Master Wallet (Luno): R 12,000
🔄 Binance: R 4,200
🔷 KuCoin: R 3,100
📊 Kraken: R 2,000
💠 VALR: R 2,150

Allocated to Bots: R 18,000
Free / Available: R 5,450

📝 Paper Mode: ACTIVE (Day 3/7)
🤖 Autopilot Reinvest: ON
```

**Mini Health Badges:**
- Luno – Master Wallet, Connected ✅, 5/5 bots
- Binance – Connected ✅, 8/10 bots
- KuCoin – Not Connected ❌
- Kraken – Connected ✅, 2/10 bots
- VALR – Connected ✅, 0/10 bots

### Dedicated Wallet Section

**Summary Table:**
| Exchange | Role | Status | Free Balance | Allocated to Bots | # Bots | Mode |
|----------|------|--------|--------------|-------------------|--------|------|
| Luno | Master + Trade | ✅ Connected | R 12,000 | R 5,000 | 5/5 | Paper/Live |
| Binance | Trading | ✅ Connected | R 4,200 | R 3,500 | 8/10 | Paper/Live |
| KuCoin | Trading | ❌ Not Connected | – | – | 0/10 | Disabled |
| Kraken | Trading | ✅ Connected | R 2,000 | R 1,200 | 2/10 | Paper/Live |
| VALR | Trading | ✅ Connected | R 2,150 | R 1,300 | 0/10 | Paper/Live |

**Exchange Drill-Down Panel (on click):**
- Exchange name & status
- API key status with "Test Connection" button
- Balance breakdown (total ZAR, free, allocated, 24h P&L)
- List of bots on that exchange
- Actions: [View Bots] [Change Autopilot Rules]

**Capital Movement Graph:**
- X-axis: Last 7/30 days
- Y-axis: Total equity
- Toggles: [All Exchanges] [Show Only Real Funds] [Include Virtual Paper]
- Shows growth, rebalancing, bot allocation over time

### Bot ↔ Wallet Linking

**Bot Table Additions:**
- Add "Exchange" column
- Add "Capital" column (allocated amount)
- Clicking Capital/Exchange → jump to Wallet panel for that exchange

**Bot Detail Panel:**
- Show exchange
- Show current capital
- Show capital history (how AI adjusted it)
- Link: [View this bot in Wallet]

### 7-Day Paper Mode → Live UX

**Status Banner (Top of Dashboard):**
```
🎓 Training Mode: Day 3 of 7 – All trades are PAPER ONLY (virtual funds)
[Learn More]
```

**After 7 Days (Success):**
```
✅ Training Complete – System ready for LIVE trading
Win rate: 58% | Avg profit: R 0.43/trade | Max drawdown: 8%
[Enable Live Trading]
```

**Go-Live Confirmation Modal:**
```
🚀 Ready for Live Trading

Win rate: 58%
Avg profit per trade: R 0.43
Max drawdown: 8%

Do you want to switch from Paper → Real Funds?

⚠️ Type: GO LIVE to confirm you understand real money will be used.

[Input field: GO LIVE]
[Confirm] [Stay in Paper Mode]
```

### Exchange Status & Onboarding

**Exchange Status Strip (Dashboard):**
```
Exchanges: Luno ✅ · Binance ✅ · KuCoin ❌ · Kraken ✅ · VALR ✅
```

**Onboarding for Disconnected Exchanges:**
```
📊 Kraken – Not Connected

Supports: BTC, ETH, XRP, etc.
AI can use this for diversification.

[Connect Kraken API Keys]
```

**Connection Modal:**
- Where to get API keys
- Permission requirements (trade only, no withdraw)
- Paste API key + secret
- [Test Connection] button
- Auto-update status on success

### Safety & Transparency

**Safety Banners:**
- ⚠️ Low Luno balance: R 350 – Autopilot may be unable to fund new bots
- 🛑 AI Bodyguard has paused 2 bots on Kraken due to high drawdown [View bots]
- ⚠️ VALR: API errors detected. Trading paused. Check keys or rate limits.

**Recent Events Timeline:**
```
Recent Capital Movements:
• +R 1,000 moved from Luno → Binance for new bot Aggressive-B3
• +R 500 profit from Binance bots (Aggressive-B1, Scalper-K2)
• -R 300 moved from VALR → Luno (rebalancing extra capital)
```

---

## 🔵 P3 - POLISH & OPTIMIZATION (Future)

### 11. Frontend Refactoring (Phase 10 - Final Major Task)
- **What:** Split monolithic Dashboard.js into smaller components
- **Status:** Postponed until all features working
- **Components to Extract:**
  - BotCard
  - WalletOverview
  - TradeTable
  - SystemStatus
  - AdminPanel
  - etc.

### 12. Trading Math & Safety
- **What:** Implement daily trade caps and max exposure limits
- **Where:** `risk_engine.py`
- **Status:** Backend partially implemented, needs verification

### 13. Real-time Updates
- **What:** Ensure bot status/mode changes pushed via WebSockets
- **Status:** WebSocket infrastructure exists, needs verification

### 14. Fetch.ai & FLOKx Integration
- **What:** Replace mock data with real API calls
- **Status:** Infrastructure in place, mock fallback working, real APIs need debugging

### 15. 24h Price Change Calculation
- **What:** Replace simulated random value with real calculation
- **Status:** Low priority cosmetic fix

---

## ✅ COMPLETED WORK (This Session)

1. ✅ Show/Hide Admin Backend Block - Added explicit check to prevent AI from intercepting command
2. ✅ Wallet Hub Frontend Integration - Replaced old Luno Wallet with new WalletHub component
3. ✅ Wallet Endpoints Fixed - Fixed parameter issues, API key error handling, field normalization
4. ✅ Wallet Navigation - User can click "Wallet Hub" to see new section

---

## 📋 TESTING CHECKLIST

### Critical Tests (Must Pass Before User Approval):
- [ ] Show/hide admin command with password flow
- [ ] Bot Management section loads without errors
- [ ] Bot creation shows success (not error) when bots are created
- [ ] Wallet Hub displays correctly
- [ ] System reset clears all data including profit stats
- [ ] AI feature buttons trigger actions
- [ ] Flokx section loads without crash
- [ ] Trades don't duplicate in UI

### Integration Tests (Use Testing Agent):
- [ ] End-to-end bot creation flow
- [ ] End-to-end wallet flow (view balances, requirements, funding plans)
- [ ] End-to-end system reset flow
- [ ] 7-day paper mode → live transition flow
- [ ] Multi-exchange bot creation and management

### UX Tests (Manual):
- [ ] Dashboard responsive on mobile
- [ ] All navigation links work
- [ ] Chat AI responds correctly
- [ ] WebSocket real-time updates work
- [ ] Profit graphs display correctly
- [ ] Admin panel accessible and functional

---

## 🚀 DEPLOYMENT READINESS CHECKLIST

### Code Quality:
- [ ] No console errors in frontend
- [ ] No backend errors in logs
- [ ] All endpoints return correct data
- [ ] All WebSocket events handled
- [ ] No hardcoded URLs or credentials

### Features Complete:
- [ ] All P0 issues fixed
- [ ] All P1 issues fixed
- [ ] Wallet redesign implemented per spec
- [ ] Bot management fully functional
- [ ] AI commands working
- [ ] Multi-exchange support verified

### User Experience:
- [ ] Clear visual hierarchy
- [ ] Consistent styling across sections
- [ ] Helpful error messages
- [ ] Loading states for async operations
- [ ] Mobile responsive
- [ ] Accessible (keyboard navigation, screen readers)

### Security & Safety:
- [ ] API keys stored securely
- [ ] No sensitive data in logs
- [ ] Rate limiting implemented
- [ ] Circuit breakers active
- [ ] Emergency stop functional
- [ ] Paper mode default for new users
- [ ] Live mode requires explicit confirmation

### Documentation:
- [ ] README with setup instructions
- [ ] API documentation
- [ ] User guide for wallet setup
- [ ] Troubleshooting guide
- [ ] VPS deployment instructions

---

## 📊 CURRENT STATUS SUMMARY

**Working:**
- ✅ Backend API endpoints (most)
- ✅ Bot creation (backend)
- ✅ Trading engines (paper & live)
- ✅ Risk management system
- ✅ Capital tracking
- ✅ Wallet backend infrastructure
- ✅ AI chat system
- ✅ WebSocket real-time updates
- ✅ User authentication

**Broken:**
- ❌ Show/hide admin (P0)
- ❌ Bot management UI (P0)
- ❌ Bot creation success message (P0)
- ❌ System reset (profit stats don't clear)
- ❌ AI feature buttons
- ❌ Wallet UX incomplete

**Needs Verification:**
- ⚠️ Flokx section crash fix
- ⚠️ Duplicate trade display fix
- ⚠️ Bot creation HTTPException fix

**Incomplete:**
- 🔄 Wallet Hub redesign (partially done)
- 🔄 Emergency stop UI (endpoint exists)
- 🔄 System health LEDs (endpoint exists)
- 🔄 7-day paper mode UX flow
- 🔄 Multi-exchange onboarding

---

## 🎯 RECOMMENDED NEXT STEPS

1. **Fix P0 Issues** (blocking user)
   - Show/hide admin
   - Bot management error
   - Bot creation success message

2. **Test & Verify** (use testing agent)
   - System reset flow
   - Flokx section
   - Trade duplication

3. **Implement Wallet UX** (per detailed spec above)
   - Dashboard wallet card
   - Dedicated wallet section
   - Exchange drill-downs
   - Capital movement graph

4. **Finish P1 Features**
   - AI feature buttons
   - Emergency stop UI
   - System health LEDs

5. **Polish & Test**
   - Testing agent for end-to-end flows
   - Manual UX testing
   - Fix any remaining bugs

6. **Deploy to VPS**
   - Follow deployment checklist
   - Test in production environment
   - Monitor for issues
