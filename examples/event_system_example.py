from typing import Optional, Dict, Any
import time
import bots
from bots.events import BotEventSystem
from bots.foundation.base import Bot


def process_data_flow(bot: 'Bot', context: dict=None):
    """Flow that processes incoming data"""
    prompt = (
        f'New data received: {context}. Please analyze this data and provide insights.'
        )
    return bot.respond(prompt)


def check_status_flow(bot: 'Bot'):
    """Flow that runs periodic status checks"""
    prompt = 'Please check the current system status and report any issues.'
    return bot.respond(prompt)


def daily_analysis_flow(bot: 'Bot'):
    """Flow that runs daily analysis tasks"""
    prompt = (
        'Please perform the daily analysis of all accumulated data and provide a summary.'
        )
    return bot.respond(prompt)


bot = bots.AnthropicBot(name='event_bot')
event_system = BotEventSystem()
event_system.subscribe_bot('new_data', bot, process_data_flow.__name__)
event_system.schedule_bot('status_check', bot, check_status_flow.__name__,
    interval=30)
event_system.schedule_bot('daily_analysis', bot, daily_analysis_flow.
    __name__, cron='0 9 * * *')
event_system.start()
print('System started. Will emit events every 10 seconds for 1 minute...')
for i in range(6):
    time.sleep(10)
    print(f'Emitting event {i + 1}')
    event_system.listener.emit('new_data', {'count': i + 1, 'data': 'test'})
print(
    "Example complete. The scheduler would continue running if this wasn't just a demo."
    )
event_system.stop()
