from trader.abstract_trader import AbstractTrader, STATUS_FILLED


class ReverserMeanTrader(AbstractTrader):

    def __init__(self, api_config, trader_config):
        super().__init__(
            api_config=api_config,
            trader_config=trader_config
        )

    def handle_sell_signal_logic(self, signal):
        for trade in self.current_trades:
            if trade.status == STATUS_FILLED:
                self.close_position()

    def handle_buy_signal_logic(self, signal):
        if len(self.current_trades) == 0:
            self.open_position()



