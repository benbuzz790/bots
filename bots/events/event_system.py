from typing import Callable, Dict, Any, Union, Optional
from datetime import datetime, timedelta
import threading
from queue import Queue, Empty
import logging
import time
from croniter import croniter
from dataclasses import dataclass
from bots.foundation.base import Bot


class EventListener:

    def __init__(self):
        self._handlers: Dict[str, list[Callable]] = {}
        self._running = False
        self._event_queue = Queue()
        self._thread = None

    def subscribe(self, event_name: str, handler: Callable):
        if event_name not in self._handlers:
            self._handlers[event_name] = []
        self._handlers[event_name].append(handler)

    def emit(self, event_name: str, data: Any=None):
        self._event_queue.put((event_name, data))

    def _process_events(self):
        while self._running:
            try:
                event_name, data = self._event_queue.get(timeout=1.0)
                if event_name in self._handlers:
                    for handler in self._handlers[event_name]:
                            try:
                                handler(data)
                            except Exception as e:
                                logging.error(f'Error in event handler: {e}')
            except Empty:
                continue

    def start(self):
        if self._thread is None:
            self._running = True
            self._thread = threading.Thread(target=self._process_events)
            self._thread.daemon = True
            self._thread.start()

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join()
            self._thread = None


class Scheduler:

    def __init__(self):
        self._tasks: Dict[str, ScheduledTask] = {}
        self._running = False
        self._thread = None

    def add_cron_task(self, name: str, cron_expr: str, handler: Callable):
        """Add a task using cron expression (e.g. '0 9 * * 1-5' for weekdays 9am)"""
        task = ScheduledTask(name=name, handler=handler, cron_expr=
            cron_expr, next_run=croniter(cron_expr, datetime.now()).
            get_next(datetime))
        self._tasks[name] = task

    def add_interval_task(self, name: str, interval: Union[timedelta, int],
        handler: Callable):
        """Add a task that runs on an interval (timedelta or seconds)"""
        if isinstance(interval, int):
            interval = timedelta(seconds=interval)
        task = ScheduledTask(name=name, handler=handler, interval=interval,
            next_run=datetime.now() + interval)
        self._tasks[name] = task

    def _run_scheduler(self):
        while self._running:
            now = datetime.now()
            for task in self._tasks.values():
                if now >= task.next_run:
                    try:
                        task.handler()
                    except Exception as e:
                        logging.error(
                            f'Error in scheduled task {task.name}: {e}')
                    finally:
                        task.update_next_run()
            time.sleep(1)

    def start(self):
        if self._thread is None:
            self._running = True
            self._thread = threading.Thread(target=self._run_scheduler)
            self._thread.daemon = True
            self._thread.start()

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join()
            self._thread = None


class BotEventSystem:

    def __init__(self):
        self.listener = EventListener()
        self.scheduler = Scheduler()

    def subscribe_bot(self, event_name: str, bot: 'Bot', flow_name: str):
        """Subscribe a bot's flow to an event"""

        def handler(data):
            bot.run_flow(flow_name, context=data)
        self.listener.subscribe(event_name, handler)

    def schedule_bot(self, name: str, bot: 'Bot', flow_name: str, cron:
        Optional[str]=None, interval: Optional[Union[timedelta, int]]=None):
        """Schedule a bot's flow to run on a schedule"""

        def handler():
            bot.run_flow(flow_name)
        if cron:
            self.scheduler.add_cron_task(name, cron, handler)
        elif interval:
            self.scheduler.add_interval_task(name, interval, handler)

    def start(self):
        """Start both the listener and scheduler"""
        self.listener.start()
        self.scheduler.start()

    def stop(self):
        """Stop both systems"""
        self.listener.stop()
        self.scheduler.stop()
