import logging
import queue
import threading

from signal_detector.model.signal_type import SIGNAL_TYPE_BUY
from trader.abstract_trader import AbstractTrader


class ReverserMeanTrader(AbstractTrader):

    def __init__(self, api_config, trader_config):
        super().__init__(
            api_config=api_config,
            trader_config=trader_config
        )
        
    def start(self):
        super().start()
        self.init_signal_handling()

    def init_signal_handling(self):
        t = threading.Thread(
            target=self.process_signal_message,
            args=(),
            daemon=True
        )
        t.start()
        self.threads.append(t)

    def process_signal_message(self):

        while not self.stop_event.is_set():
            try:
                signal = self.signal_queue.get(timeout=1)
                if signal is None:
                    break
                if signal.type == SIGNAL_TYPE_BUY:
                    print(f'process_signal_message : New signal received {signal}')
                    self.open_position()
            except queue.Empty:
                continue
            except Exception as e:
                logging.error(f"process_signal_message : Error processing signal message for symbol {self.trader_config.symbol}: {e}", exc_info=True)
                self.signal_queue.task_done()
