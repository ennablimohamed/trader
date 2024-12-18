import logging
import queue
import threading
from abc import ABC


class AbstractSignalDetector(ABC):

    def __init__(self, app_config, symbol):
        self.last_price = None
        self.app_config = app_config
        self.symbol = symbol
        self.price_queue = queue.Queue(maxsize=1000)
        self.stop_event = threading.Event()
        self.threads = []

    def start(self):
        self.init_price_handling()

    def process_price_update_message(self):

        while not self.stop_event.is_set():
            try:
                message = self.price_queue.get(timeout=1)
                if message is None:
                    break
                self.last_price = message['last_price']
                print(f"price updated for {message['symbol']} with value {self.last_price}")
                self.price_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                logging.error(f"process_price_update_message : Error processing price message for symbol {self.symbol}: {e}", exc_info=True)
                self.price_queue.task_done()

    def init_price_handling(self):
        t = threading.Thread(
            target=self.process_price_update_message,
            args=(),
            daemon=True
        )
        t.start()
        self.threads.append(t)
