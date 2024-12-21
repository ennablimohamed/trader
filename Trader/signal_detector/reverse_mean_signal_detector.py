import logging
import queue
import threading
from decimal import Decimal

import pandas as pd

from signal_detector.abstract_signal_detector import AbstractSignalDetector


class ReverseMeanSignalDetector(AbstractSignalDetector):

    def __init__(self, app_config, symbol):
        super().__init__(app_config=app_config, symbol=symbol, type='ReverseMeanSignalDetector')
        self.klines_queue = queue.Queue(maxsize=1000)

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
                self.detect_signal(message)
            except queue.Empty:
                continue
            except Exception as e:
                logging.error(
                    f"process_klines_update : Error processing klines update message for symbol {self.symbol}: {e}",
                    exc_info=True)
                self.klines_queue.task_done()

    def detect_signal(self, data):
        logging.debug("detect_signal : Start detecting signal")
        try:
            klines = self.compute_klines(data)
            bollinger_data = self.update_bollinger_bands(klines, window=20, num_std=2)

            last_row = bollinger_data.iloc[-1]
            last_close = Decimal(str(last_row['close']))
            lower_band = Decimal(str(last_row['Lower_Band']))
            middle_band = Decimal(str(last_row['MA']))

            detected_signal_type = None
            if last_close < lower_band:
                detected_signal_type = "BUY"
            elif last_close > middle_band:
                detected_signal_type = "SELL"
            if detected_signal_type is not None:
                message = {"detector": "ReverseMeanSignalDetector",
                           "symbol": self.symbol,
                           "type": detected_signal_type,
                           "price": self.last_price}
                self.__notify_consumers(message)
        except Exception as e:
            logging.error(f"An error occurred while detecting reverse mean signal for symbol {self.symbol}")

    def update_bollinger_bands(self, data: pd.DataFrame, window: int = 20, num_std: int = 2):

        data['MA'] = data['close'].rolling(window=window).mean()
        data['STD'] = data['close'].rolling(window=window).std()
        data['Upper_Band'] = data['MA'] + (data['STD'] * num_std)
        data['Lower_Band'] = data['MA'] - (data['STD'] * num_std)
        return data

    def compute_klines(self, data):
        columns = [
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_asset_volume', 'trades',
            'taker_base_vol', 'taker_quote_vol', 'ignore'
        ]
        data = pd.DataFrame(data, columns=columns)

        # Convert relevant columns to numeric
        for col in ['open', 'high', 'low', 'close', 'volume']:
            data[col] = pd.to_numeric(data[col])

        # Use timestamp as datetime index
        data['timestamp'] = pd.to_datetime(data['timestamp'], unit='ms')
        data.set_index('timestamp', inplace=True)

        return data[['open', 'high', 'low', 'close', 'volume']]

    def add_signal_consumer(self, signal_queue):
        self.signal_consumers.append(signal_queue)

    def __notify_consumers(self, message):

        logging.info(f"__notify_consumers : Start notifying consumers about detected signal {message}")
        for q in self.signal_consumers:
            try:
                q.put_nowait(message)
            except queue.Full:
                logging.warning(
                    f"Signal queue is full for symbol {self.symbol} and detector {self.type}. Dropping message.")
