import logging
import queue
import threading

from trader.abstract_trader import AbstractTrader


class ReverserMeanTrader(AbstractTrader):

    def __init__(self, symbol, capital, signal_detector):
        super().__init__(symbol=symbol, capital=capital, signal_detector=signal_detector)
        
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
                message = self.signal_queue.get(timeout=1)
                if message is None:
                    break
                print(f'process_signal_message : New signal received {message}')
            except queue.Empty:
                continue
            except Exception as e:
                logging.error(f"process_signal_message : Error processing signal message for symbol {self.symbol}: {e}", exc_info=True)
                self.signal_queue.task_done()
