import logging
import queue
from abc import abstractmethod

from signal_detector.model.signal_type import SIGNAL_TYPE_BUY, SIGNAL_TYPE_SELL
from trader.abstract_trader import AbstractTrader


class AbstractBasicTrader(AbstractTrader):

    def __init__(self, api_config, name, database_manager, trader):
        super().__init__(api_config, name=name, database_manager=database_manager, trader=trader)

    def process_signal_message(self):

        while not self.stop_event.is_set():
            try:
                signal = self.signal_queue.get(timeout=1)
                if signal is None:
                    break
                if signal.type == SIGNAL_TYPE_BUY:
                    self.handle_buy_signal_logic(signal)
                elif signal.type == SIGNAL_TYPE_SELL:
                    self.handle_sell_signal_logic(signal)

                self.signal_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                logging.error(
                    f"process_signal_message : Error processing signal message for symbol {self.trader_config.symbol}: {e}",
                    exc_info=True)
                self.signal_queue.task_done()

    @abstractmethod
    def handle_buy_signal_logic(self, signal):
        pass

    @abstractmethod
    def handle_sell_signal_logic(self, signal):
        pass
