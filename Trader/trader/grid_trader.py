import logging
import queue
import uuid
from decimal import Decimal

from signal_detector.model.signal_type import SIGNAL_TYPE_GRID_CONFIG
from trader.abstract_trader import AbstractTrader, STATUS_FILLED
from trader.model.grid import Grid


class GridTrader(AbstractTrader):

    def __init__(self, api_config, trader_config):
        super().__init__(api_config, trader_config, name='GridTrader-'+trader_config.symbol)
        self.grids = []
        self.min_price = None
        self.max_price = None
        self.trade_grid = {}
        self.max_trades = 20

    def process_signal_message(self):

        while not self.stop_event.is_set():
            try:
                signal = self.signal_queue.get(timeout=1)
                if signal is None:
                    break
                if signal.type == SIGNAL_TYPE_GRID_CONFIG:
                    self.create_or_update_grids(signal.min_price, signal.max_price)
                self.signal_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                logging.error(
                    f"process_signal_message : Error processing signal message for symbol {self.trader_config.symbol}: {e}",
                    exc_info=True)
                self.signal_queue.task_done()

    def create_or_update_grids(self, min_price, max_price):
        if self.min_price is None or self.max_price is None or self.min_price < min_price or self.max_price < max_price:
            self.min_price = min_price
            self.max_price = max_price
            self.recompute_grid()

    def recompute_grid(self):
        current_max_level = self.max_price
        self.grids.clear()
        gap = self.trader_config.grid_gap
        while current_max_level > self.min_price:
            grid_id = str(uuid.uuid4())
            grid = Grid(grid_id, start=current_max_level - gap, end=current_max_level)
            current_max_level -= gap
            self.grids.append(grid)
        logging.info(
            f'recompute_grid : Grid config recomputed successfully by trader {self.name} for symbol {self.trader_config.symbol}')

    def process_price_update_message(self):

        while not self.stop_event.is_set():
            try:
                message = self.price_queue.get(timeout=1)
                if message is None:
                    break
                self.last_price = message['last_price']
                self.update_orders()
                self.update_grid_in_range()
                self.price_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                logging.error(
                    f"process_price_update_message : Error processing price message for symbol {self.trader_config.symbol}: {e}",
                    exc_info=True)
                self.price_queue.task_done()

    def update_orders(self):
        if len(self.current_trades) < self.max_trades and len(self.grids) > 0:
            for grid in self.grids:
                if grid.in_price_range:
                    if self.last_price < grid.start:
                        if self.trade_grid.get(grid.id) is None:
                            trade = self.open_position()
                            self.trade_grid[grid.id] = trade
                    if self.last_price > grid.end:
                        trade = self.trade_grid.get(grid.id, None)
                        if trade is not None and trade.status == STATUS_FILLED:
                            self.close_position(trade=trade)
                            self.trade_grid[grid.id] = None

    def update_grid_in_range(self):
        for grid in self.grids:
            if grid.start <= self.last_price <= grid.end:
                grid.in_price_range = True
            else:
                grid.in_price_range = False
