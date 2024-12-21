
class SignalConfig:

    def __init__(self, symbol, detector, need_klines=None):
        self.symbol = symbol
        self.detector = detector
        self.need_klines = need_klines
