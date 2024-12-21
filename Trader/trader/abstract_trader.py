import logging
import queue
import threading
from abc import ABC


class AbstractTrader(ABC):

    def __init__(self, symbol, capital, signal_detector):
        self.last_price = None
        self.price_queue = queue.Queue(maxsize=1000)
        self.stop_event = threading.Event()
        self.threads = []
        self.symbol = symbol
        self.signal_queue = queue.Queue(maxsize=1000)
        self.capital = capital
        self.signal_detector = signal_detector

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
