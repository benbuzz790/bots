import asyncio
from bot_manager import BotManager

async def test_bot_methods():
    bm = BotManager()
    bot_id = await bm.create_bot('Test')
    print(f"Created bot: {bot_id}")
    
    # Check what methods exist
    methods = [method for method in dir(bm) if not method.startswith('_')]
    print(f"Available methods: {methods}")
    
    # Test send_message
    try:
        state = await bm.send_message(bot_id, 'test')
        print('✅ send_message works')
    except Exception as e:
        print(f'❌ send_message error: {e}')

asyncio.run(test_bot_methods())
