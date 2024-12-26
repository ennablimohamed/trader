import logging
import queue
import threading
from decimal import Decimal

from signal_detector.abstract_signal_detector import AbstractSignalDetector
from signal_detector.model.GridSignal import GridSignal
from signal_detector.model.Signal import Signal
from signal_detector.model.signal_type import SIGNAL_TYPE_GRID_CONFIG


class GridSignalDetector(AbstractSignalDetector):

    def __init__(self, app_config, symbol):
        super().__init__(app_config=app_config, symbol=symbol, type='GridSignalDetector')
        self.klines_queue = queue.Queue(maxsize=1000)
        self.min_price = None
        self.max_price = None

    def start(self):

        super().start()
        self.init_klines_handling()

    def init_klines_handling(self):
        t = threading.Thread(
            target=self.process_klines_update,
            args=(),
            daemon=True
        )
        t.start()
        self.threads.append(t)

    def process_klines_update(self):
        while not self.stop_event.is_set():
            try:
                message = self.klines_queue.get(timeout=1)
                if message is None:
                    break
                logging.debug(f"process_klines_update : klines update received for symbol {self.symbol}")
                self.init_prices(message)
                self.build_and_send_message()
            except queue.Empty:
                continue
            except Exception as e:
                logging.error(
                    f"process_klines_update : Error processing klines update message for symbol {self.symbol}: {e}",
                    exc_info=True)
                self.klines_queue.task_done()

    def init_prices(self, data):
        if self.min_price is None and self.max_price is None:
            logging.debug("detect_signal : Start detecting signal")
            try:
                min_price = Decimal(data[0][3])
                max_price = Decimal(data[0][2])
                for item in data:
                    low_price = Decimal(item[3])
                    high_price = Decimal(item[2])
                    if low_price < min_price:
                        min_price = low_price
                    elif high_price > max_price:
                        max_price = high_price
                self.min_price = min_price
                self.max_price = max_price
            except Exception as e:
                logging.error(f"An error occurred while detecting reverse mean signal for symbol {self.symbol}")

    def process_price_update_message(self):

        while not self.stop_event.is_set():
            try:
                message = self.price_queue.get(timeout=1)
                if message is None:
                    break
                self.last_price = message['last_price']
                self.detect_signal()
                self.price_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                logging.error(
                    f"process_price_update_message : Error processing price message for symbol {self.symbol}: {e}",
                    exc_info=True)
                self.price_queue.task_done()

    def detect_signal(self):
        if (self.min_price is not None and self.max_price is not None and
                self.last_price < self.min_price or self.max_price < self.last_price):
            self.build_and_send_message()

    def build_and_send_message(self):
        message = GridSignal(
            detector=self.type,
            symbol=self.symbol,
            signal_type=SIGNAL_TYPE_GRID_CONFIG,
            min_price=self.min_price,
            max_price=self.max_price
        )
        self.notify_consumers(message)
