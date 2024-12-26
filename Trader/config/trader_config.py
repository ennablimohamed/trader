
class TraderConfig:

    def __init__(self, symbol, capital, detector, trade_quantity, grid_gap):
        self.symbol = symbol
        self.capital = capital
        self.detector = detector
        self.trade_quantity = trade_quantity
        self.grid_gap = grid_gap
