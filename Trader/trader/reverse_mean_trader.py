from trader.abstract_basic_trader import AbstractBasicTrader
from trader.abstract_trader import STATUS_FILLED


class ReverserMeanTrader(AbstractBasicTrader):

    def __init__(self, api_config, database_manager, trader):
        super().__init__(
            api_config=api_config,
            name='ReverserMeanTrader-'+trader.symbol,
            database_manager=database_manager,
            trader=trader
        )

    def handle_sell_signal_logic(self, signal):
        for trade in self.current_trades:
            if trade.status == STATUS_FILLED:
                self.close_position(trade=trade)

    def handle_buy_signal_logic(self, signal):
        if len(self.current_trades) == 0:
            self.open_position()
