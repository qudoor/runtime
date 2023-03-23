#!/usr/bin/env python
import time
import threading
import logging
from queue import Queue
from django.conf import settings

from .models import ApiRecord

logger = logging.getLogger(__name__)
error = logger.exception if settings.DEBUG else logger.error
WORKER_NAME = "LogWorker"


class LogThreadWorker(threading.Thread):
    INTERVAL = 10
    QUEUE_MAX_SIZE = 50
    DB_ALIAS = 'default'

    def __init__(self, **options):
        super().__init__(**options)
        self._queue = Queue(maxsize=self.QUEUE_MAX_SIZE)

    def run(self) -> None:
        while True:
            time.sleep(self.INTERVAL)
            self.try_insert()

    def push(self, data: dict):
        self._queue.put(ApiRecord(**data))

        if self._queue.qsize() >= self.QUEUE_MAX_SIZE:
            self.try_insert()

    def try_insert(self):
        items = []
        while not self._queue.empty():
            items.append(self._queue.get())

        if items:
            try:
                ApiRecord.objects.using(self.DB_ALIAS).bulk_create(items)
            except Exception as e:
                error(f"Tracking error", e)


def create_worker():
    for t in threading.enumerate():
        if t.name == WORKER_NAME:
            return t

    worker = LogThreadWorker(name=WORKER_NAME, daemon=True)
    worker.start()
    return worker


logger_worker = create_worker()
