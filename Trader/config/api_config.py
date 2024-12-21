
class ApiConfig:

    def __init__(self, credentials, websocket_base_url, base_url, trades_config):
        self.credentials = credentials
        self.websocket_base_url = websocket_base_url
        self.base_url = base_url
        self.trades_config = trades_config
