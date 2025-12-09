from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'amarktai_trading')]

# Collections
users_collection = db.users
api_keys_collection = db.api_keys
bots_collection = db.bots
trades_collection = db.trades
learning_data_collection = db.learning_data
alerts_collection = db.alerts
audit_log_collection = db.audit_log
chat_messages_collection = db.chat_messages
system_modes_collection = db.system_modes

# Phase 2 Collections
learning_logs_collection = db.learning_logs
autopilot_actions_collection = db.autopilot_actions
rogue_detections_collection = db.rogue_detections

async def init_db():
    """Initialize database indexes"""
    # User indexes
    await users_collection.create_index("email", unique=True)
    await users_collection.create_index("id", unique=True)
    
    # API Keys indexes
    await api_keys_collection.create_index(["user_id", "provider"])
    
    # Bots indexes
    await bots_collection.create_index("user_id")
    await bots_collection.create_index("id", unique=True)
    await bots_collection.create_index("created_at")
    await bots_collection.create_index([("user_id", 1), ("mode", 1)])  # For promotion queries
    
    # Trades indexes
    await trades_collection.create_index("bot_id")
    await trades_collection.create_index("user_id")
    await trades_collection.create_index("timestamp")
    
    # Learning data indexes
    await learning_data_collection.create_index("user_id")
    await learning_data_collection.create_index("date")
    
    # Alerts indexes
    await alerts_collection.create_index("user_id")
    await alerts_collection.create_index("timestamp")
    
    # Audit log indexes
    await audit_log_collection.create_index("user_id")
    await audit_log_collection.create_index("timestamp")
    
    # Chat messages indexes
    await chat_messages_collection.create_index("user_id")
    await chat_messages_collection.create_index("timestamp")
    
    # System modes indexes
    await system_modes_collection.create_index("user_id", unique=True)
    
    # Phase 2 indexes
    await learning_logs_collection.create_index("user_id")
    await learning_logs_collection.create_index("timestamp")
    await learning_logs_collection.create_index("bot_id")
    
    await autopilot_actions_collection.create_index("user_id")
    await autopilot_actions_collection.create_index("timestamp")
    await autopilot_actions_collection.create_index("action_type")
    
    await rogue_detections_collection.create_index("user_id")
    await rogue_detections_collection.create_index("bot_id")
    await rogue_detections_collection.create_index("timestamp")

async def close_db():
    """Close database connection"""
    client.close()
