import unittest
import time
from datetime import datetime, timedelta
from bots import AnthropicBot
from bots.events import BotEventSystem


def example_flow(bot, context=None):
    """Example flow that returns its context"""
    return bot.respond(f'Received event with data: {context}')


def error_example_flow(bot, context=None):
    """Example flow that raises an error"""
    raise ValueError('Test error')


def counting_example_flow(bot, context=None):
    """Example flow that counts executions"""
    if not hasattr(counting_example_flow, 'count'):
        counting_example_flow.count = 0
    counting_example_flow.count += 1
    return bot.respond(f'Execution {counting_example_flow.count}')
