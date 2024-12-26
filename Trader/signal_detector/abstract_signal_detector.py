import logging
import queue
import threading
from abc import ABC


class AbstractSignalDetector(ABC):

    def __init__(self, app_config, symbol, type):
        self.last_price = None
        self.app_config = app_config
        self.symbol = symbol
        self.price_queue = queue.Queue(maxsize=1000)
        self.stop_event = threading.Event()
        self.threads = []
        self.type = type
        self.signal_consumers = []

    def start(self):
        self.init_price_handling()

    def process_price_update_message(self):

        while not self.stop_event.is_set():
            try:
                message = self.price_queue.get(timeout=1)
                if message is None:
                    break
                self.last_price = message['last_price']
                self.price_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                logging.error(
                    f"process_price_update_message : Error processing price message for symbol {self.symbol}: {e}",
                    exc_info=True)
                self.price_queue.task_done()

    def init_price_handling(self):
        t = threading.Thread(
            target=self.process_price_update_message,
            args=(),
            daemon=True
        )
        t.start()
        self.threads.append(t)

    def notify_consumers(self, message):

        logging.debug(f"__notify_consumers : Start notifying consumers about detected signal {message}")
        for q in self.signal_consumers:
            try:
                q.put_nowait(message)
            except queue.Full:
                logging.warning(
                    f"Signal queue is full for symbol {self.symbol} and detector {self.type}. Dropping message.")

    def add_signal_consumer(self, signal_queue):
        self.signal_consumers.append(signal_queue)
