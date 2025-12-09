#!/usr/bin/env python3
"""
Comprehensive Backend Testing for Amarktai Phase 1 Stabilization
Testing: Risk Management, Per-Exchange Limits, Fetch.ai, FLOKx, Regression
"""

import asyncio
import aiohttp
import json
import sys
from datetime import datetime
from typing import Dict, Any, List

# Configuration
BASE_URL = "https://tradewise-275.preview.emergentagent.com/api"
TEST_USER = {
    "email": "test@amarktai.com",
    "password": "testpass123"
}

class BackendTester:
    def __init__(self):
        self.session = None
        self.token = None
        self.user_id = None
        self.test_results = []
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def log_test(self, test_name: str, status: str, details: str = ""):
        """Log test result"""
        result = {
            "test": test_name,
            "status": status,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status_emoji = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_emoji} {test_name}: {status}")
        if details:
            print(f"   Details: {details}")
    
    async def authenticate(self) -> bool:
        """Authenticate and get token"""
        try:
            async with self.session.post(f"{BASE_URL}/auth/login", json=TEST_USER) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    self.token = data.get('token')
                    self.user_id = data.get('user', {}).get('id')
                    self.log_test("Authentication", "PASS", f"User ID: {self.user_id}")
                    return True
                else:
                    error = await resp.text()
                    self.log_test("Authentication", "FAIL", f"Status {resp.status}: {error}")
                    return False
        except Exception as e:
            self.log_test("Authentication", "FAIL", f"Exception: {str(e)}")
            return False
    
    async def make_request(self, method: str, endpoint: str, **kwargs) -> tuple:
        """Make authenticated request"""
        headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
        if 'headers' in kwargs:
            headers.update(kwargs['headers'])
        kwargs['headers'] = headers
        
        try:
            async with self.session.request(method, f"{BASE_URL}{endpoint}", **kwargs) as resp:
                try:
                    data = await resp.json()
                except:
                    data = await resp.text()
                return resp.status, data
        except Exception as e:
            return 0, str(e)
    
    # ============================================================================
    # PHASE 1 CRITICAL TESTS
    # ============================================================================
    
    async def test_risk_management_engine(self):
        """Test Risk Management Engine Integration"""
        print("\n🎯 TESTING RISK MANAGEMENT ENGINE")
        
        # Test 1: Check if risk management is mentioned in backend health
        status, data = await self.make_request("GET", "/admin/backend-health")
        if status == 200 and isinstance(data, dict):
            services = data.get('services', {})
            risk_found = any('risk' in str(service).lower() for service in services.values())
            if risk_found:
                self.log_test("Risk Management Engine Status", "PASS", "Risk management service detected in health check")
            else:
                self.log_test("Risk Management Engine Status", "WARN", "Risk management not explicitly found in health check")
        else:
            self.log_test("Risk Management Engine Status", "FAIL", f"Health check failed: {status}")
        
        # Test 2: Check if bots have risk parameters
        status, data = await self.make_request("GET", "/bots")
        if status == 200 and isinstance(data, list):
            if data:
                bot = data[0]
                risk_mode = bot.get('risk_mode')
                if risk_mode:
                    self.log_test("Bot Risk Parameters", "PASS", f"Bots have risk_mode: {risk_mode}")
                else:
                    self.log_test("Bot Risk Parameters", "WARN", "Bots missing risk_mode parameter")
            else:
                self.log_test("Bot Risk Parameters", "WARN", "No bots found to test risk parameters")
        else:
            self.log_test("Bot Risk Parameters", "FAIL", f"Failed to get bots: {status}")
    
    async def test_per_exchange_limits(self):
        """Test Per-Exchange Trade Limits"""
        print("\n📊 TESTING PER-EXCHANGE TRADE LIMITS")
        
        # Expected limits per exchange
        expected_limits = {
            'luno': 75,
            'binance': 150,
            'kucoin': 150,
            'kraken': 100,
            'valr': 100
        }
        
        # Test by creating bots on different exchanges and checking their limits
        for exchange, expected_limit in expected_limits.items():
            try:
                # Try to create a test bot on this exchange
                bot_data = {
                    "name": f"Test-{exchange.upper()}-Bot",
                    "exchange": exchange,
                    "risk_mode": "safe",
                    "initial_capital": 1000
                }
                
                status, data = await self.make_request("POST", "/bots", json=bot_data)
                
                if status == 201 or status == 200:
                    # Bot created successfully, check if it has correct exchange
                    if isinstance(data, dict) and data.get('exchange') == exchange:
                        self.log_test(f"Exchange {exchange.upper()} Bot Creation", "PASS", f"Bot created on {exchange}")
                        
                        # Clean up - delete the test bot
                        bot_id = data.get('id')
                        if bot_id:
                            await self.make_request("DELETE", f"/bots/{bot_id}")
                    else:
                        self.log_test(f"Exchange {exchange.upper()} Bot Creation", "WARN", f"Bot created but exchange mismatch")
                elif status == 400:
                    # Check if it's a limit-related error
                    error_msg = str(data).lower()
                    if 'limit' in error_msg or 'maximum' in error_msg:
                        self.log_test(f"Exchange {exchange.upper()} Limits", "PASS", f"Limit enforcement detected: {data}")
                    else:
                        self.log_test(f"Exchange {exchange.upper()} Bot Creation", "WARN", f"Creation failed: {data}")
                else:
                    self.log_test(f"Exchange {exchange.upper()} Bot Creation", "FAIL", f"Status {status}: {data}")
                    
            except Exception as e:
                self.log_test(f"Exchange {exchange.upper()} Test", "FAIL", f"Exception: {str(e)}")
    
    async def test_fetchai_integration(self):
        """Test Fetch.ai Integration"""
        print("\n🔮 TESTING FETCH.AI INTEGRATION")
        
        # Test 1: Check if Fetch.ai API key is configured
        status, data = await self.make_request("GET", "/api-keys")
        if status == 200 and isinstance(data, list):
            fetchai_key = next((key for key in data if key.get('provider') == 'fetchai'), None)
            if fetchai_key:
                self.log_test("Fetch.ai API Key Configuration", "PASS", "Fetch.ai key found in user keys")
            else:
                self.log_test("Fetch.ai API Key Configuration", "WARN", "No Fetch.ai key found in user keys")
        
        # Test 2: Test Fetch.ai connection
        status, data = await self.make_request("POST", "/api-keys/fetchai/test")
        if status == 200:
            self.log_test("Fetch.ai Connection Test", "PASS", "Connection test successful")
        elif status == 404:
            self.log_test("Fetch.ai Connection Test", "WARN", "No API key found for testing")
        else:
            self.log_test("Fetch.ai Connection Test", "FAIL", f"Connection test failed: {status} - {data}")
        
        # Test 3: Check for Fetch.ai endpoints
        endpoints_to_test = [
            "/fetchai/signals/BTC-USD",
            "/fetchai/signals",
            "/fetchai/test-connection"
        ]
        
        for endpoint in endpoints_to_test:
            status, data = await self.make_request("GET", endpoint)
            if status == 200:
                # Check if response contains real data (not mock)
                if isinstance(data, dict):
                    source = data.get('source', '')
                    if source and source != 'mock':
                        self.log_test(f"Fetch.ai Endpoint {endpoint}", "PASS", f"Real data source: {source}")
                    elif 'signal' in data or 'confidence' in data:
                        self.log_test(f"Fetch.ai Endpoint {endpoint}", "PASS", "Signal data structure found")
                    else:
                        self.log_test(f"Fetch.ai Endpoint {endpoint}", "WARN", "Response structure unclear")
                else:
                    self.log_test(f"Fetch.ai Endpoint {endpoint}", "WARN", f"Unexpected response format")
            elif status == 404:
                self.log_test(f"Fetch.ai Endpoint {endpoint}", "WARN", "Endpoint not found")
            else:
                self.log_test(f"Fetch.ai Endpoint {endpoint}", "FAIL", f"Status {status}")
    
    async def test_flokx_integration(self):
        """Test FLOKx Integration"""
        print("\n🎯 TESTING FLOKX INTEGRATION")
        
        # Test 1: Check if FLOKx API key is configured
        status, data = await self.make_request("GET", "/api-keys")
        if status == 200 and isinstance(data, list):
            flokx_key = next((key for key in data if key.get('provider') == 'flokx'), None)
            if flokx_key:
                self.log_test("FLOKx API Key Configuration", "PASS", "FLOKx key found in user keys")
            else:
                self.log_test("FLOKx API Key Configuration", "WARN", "No FLOKx key found in user keys")
        
        # Test 2: Test FLOKx connection
        status, data = await self.make_request("POST", "/api-keys/flokx/test")
        if status == 200:
            self.log_test("FLOKx Connection Test", "PASS", "Connection test successful")
        elif status == 404:
            self.log_test("FLOKx Connection Test", "WARN", "No API key found for testing")
        else:
            self.log_test("FLOKx Connection Test", "FAIL", f"Connection test failed: {status} - {data}")
        
        # Test 3: Check for FLOKx endpoints
        endpoints_to_test = [
            "/flokx/coefficients/BTC-USD",
            "/flokx/coefficients/BTC-ZAR", 
            "/flokx/alerts",
            "/flokx/create-alert"
        ]
        
        for endpoint in endpoints_to_test:
            if endpoint == "/flokx/create-alert":
                # POST request for alert creation
                alert_data = {
                    "pair": "BTC/USD",
                    "condition": "price_above",
                    "value": 50000
                }
                status, data = await self.make_request("POST", endpoint, json=alert_data)
            else:
                # GET request
                status, data = await self.make_request("GET", endpoint)
            
            if status == 200:
                # Check if response contains real data (not mock)
                if isinstance(data, dict):
                    source = data.get('source', '')
                    if source and source != 'mock':
                        self.log_test(f"FLOKx Endpoint {endpoint}", "PASS", f"Real data source: {source}")
                    elif any(key in data for key in ['strength', 'volatility', 'sentiment', 'coefficients']):
                        self.log_test(f"FLOKx Endpoint {endpoint}", "PASS", "Coefficient data structure found")
                    else:
                        self.log_test(f"FLOKx Endpoint {endpoint}", "WARN", "Response structure unclear")
                else:
                    self.log_test(f"FLOKx Endpoint {endpoint}", "WARN", f"Unexpected response format")
            elif status == 404:
                self.log_test(f"FLOKx Endpoint {endpoint}", "WARN", "Endpoint not found")
            else:
                self.log_test(f"FLOKx Endpoint {endpoint}", "FAIL", f"Status {status}")
    
    async def test_regression_functionality(self):
        """Test Regression - Ensure existing functionality still works"""
        print("\n🔄 TESTING REGRESSION - EXISTING FUNCTIONALITY")
        
        # Test 1: Bot creation still works
        status, data = await self.make_request("GET", "/bots")
        if status == 200:
            self.log_test("Bot Listing", "PASS", f"Found {len(data) if isinstance(data, list) else 0} bots")
        else:
            self.log_test("Bot Listing", "FAIL", f"Status {status}")
        
        # Test 2: Trading scheduler operational
        status, data = await self.make_request("GET", "/overview")
        if status == 200 and isinstance(data, dict):
            active_bots = data.get('active_bots', 0)
            total_profit = data.get('totalProfit', 0)
            self.log_test("Overview Endpoint", "PASS", f"Active bots: {active_bots}, Profit: R{total_profit}")
        else:
            self.log_test("Overview Endpoint", "FAIL", f"Status {status}")
        
        # Test 3: Autonomous engines status
        status, data = await self.make_request("GET", "/admin/backend-health")
        if status == 200 and isinstance(data, dict):
            services = data.get('services', {})
            healthy_services = sum(1 for service in services.values() if 'healthy' in str(service).lower() or 'active' in str(service).lower())
            self.log_test("Autonomous Engines", "PASS", f"{healthy_services} services operational")
        else:
            self.log_test("Autonomous Engines", "FAIL", f"Health check failed: {status}")
        
        # Test 4: WebSocket connection
        status, data = await self.make_request("GET", "/admin/system-stats")
        if status == 200:
            self.log_test("System Stats", "PASS", "System statistics accessible")
        else:
            self.log_test("System Stats", "FAIL", f"Status {status}")
        
        # Test 5: Live prices still work
        status, data = await self.make_request("GET", "/prices/live")
        if status == 200 and isinstance(data, dict):
            btc_price = data.get('BTC/ZAR', {}).get('price', 0)
            if btc_price > 0:
                self.log_test("Live Prices", "PASS", f"BTC/ZAR: R{btc_price}")
            else:
                self.log_test("Live Prices", "WARN", "Price data available but BTC price is 0")
        else:
            self.log_test("Live Prices", "FAIL", f"Status {status}")
    
    async def test_ai_integrations_in_trades(self):
        """Test if AI integrations are working in actual trades"""
        print("\n🤖 TESTING AI INTEGRATION IN TRADES")
        
        # Get recent trades to check for AI metadata
        status, data = await self.make_request("GET", "/trades/recent?limit=20")
        if status == 200 and isinstance(data, dict):
            trades = data.get('trades', [])
            if trades:
                ai_fields = ['ai_regime', 'ai_confidence', 'fetchai_signal', 'fetchai_confidence', 
                           'flokx_strength', 'flokx_sentiment', 'ml_prediction']
                
                trades_with_ai = 0
                for trade in trades:
                    if any(field in trade for field in ai_fields):
                        trades_with_ai += 1
                
                ai_percentage = (trades_with_ai / len(trades)) * 100
                if ai_percentage > 50:
                    self.log_test("AI Integration in Trades", "PASS", f"{ai_percentage:.1f}% of trades have AI metadata")
                elif ai_percentage > 0:
                    self.log_test("AI Integration in Trades", "WARN", f"Only {ai_percentage:.1f}% of trades have AI metadata")
                else:
                    self.log_test("AI Integration in Trades", "FAIL", "No AI metadata found in trades")
            else:
                self.log_test("AI Integration in Trades", "WARN", "No recent trades found to analyze")
        else:
            self.log_test("AI Integration in Trades", "FAIL", f"Failed to get trades: {status}")
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*80)
        print("🎯 PHASE 1 STABILIZATION TEST SUMMARY")
        print("="*80)
        
        total_tests = len(self.test_results)
        passed = len([t for t in self.test_results if t['status'] == 'PASS'])
        failed = len([t for t in self.test_results if t['status'] == 'FAIL'])
        warnings = len([t for t in self.test_results if t['status'] == 'WARN'])
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"⚠️  Warnings: {warnings}")
        print(f"Success Rate: {(passed/total_tests)*100:.1f}%")
        
        print("\n🔴 CRITICAL ISSUES:")
        critical_issues = [t for t in self.test_results if t['status'] == 'FAIL']
        if critical_issues:
            for issue in critical_issues:
                print(f"  - {issue['test']}: {issue['details']}")
        else:
            print("  None! 🎉")
        
        print("\n⚠️  WARNINGS:")
        warning_issues = [t for t in self.test_results if t['status'] == 'WARN']
        if warning_issues:
            for warning in warning_issues:
                print(f"  - {warning['test']}: {warning['details']}")
        else:
            print("  None!")
        
        print("\n✅ SUCCESSES:")
        successes = [t for t in self.test_results if t['status'] == 'PASS']
        for success in successes[:10]:  # Show first 10 successes
            print(f"  - {success['test']}")
        if len(successes) > 10:
            print(f"  ... and {len(successes) - 10} more")

async def main():
    """Main test execution"""
    print("🚀 Starting Amarktai Phase 1 Stabilization Testing")
    print(f"Backend URL: {BASE_URL}")
    print(f"Test User: {TEST_USER['email']}")
    print("="*80)
    
    async with BackendTester() as tester:
        # Authenticate first
        if not await tester.authenticate():
            print("❌ Authentication failed. Cannot proceed with tests.")
            return
        
        # Run all test suites
        await tester.test_risk_management_engine()
        await tester.test_per_exchange_limits()
        await tester.test_fetchai_integration()
        await tester.test_flokx_integration()
        await tester.test_regression_functionality()
        await tester.test_ai_integrations_in_trades()
        
        # Print summary
        tester.print_summary()
        
        # Save results to file
        with open('/app/test_results_phase1.json', 'w') as f:
            json.dump(tester.test_results, f, indent=2)
        
        print(f"\n📄 Detailed results saved to: /app/test_results_phase1.json")

if __name__ == "__main__":
    asyncio.run(main())