import asyncio
import json
import logging
import queue
import threading
from decimal import Decimal

from manager.abstract_manager import AbstractManager
import websockets


class PriceManager(AbstractManager):

    def __init__(self, app_config, symbol, consumers_queues):
        super().__init__(app_config)
        self.threads = []
        self.__last_price = None
        self.__consumers_queues = consumers_queues
        self.symbol = symbol

    def start(self):
        api_config = self.app_config.api_config
        websocket_base_url = api_config.websocket_base_url
        self.__add_price_handler(websocket_base_url=websocket_base_url)

    def __add_price_handler(self, websocket_base_url):
        try:
            lower_symbol = self.symbol.lower()
            websocket_url = websocket_base_url + '/stream?streams=' + lower_symbol + '@trade'
            self.__add_websocket_handler(websocket_url)
        except Exception as e:
            logging.error(f"add_price_handler : An error occurred while adding websocket handler for {self.symbol} {e}")

    def __add_websocket_handler(self, websocket_url):
        logging.info(f"__add_websocket_handler : Start adding websocket handler for {websocket_url}")

        def run():
            asyncio.set_event_loop(asyncio.new_event_loop())
            loop = asyncio.get_event_loop()
            loop.run_until_complete(handler())

        async def handler():
            while True:
                try:
                    async with websockets.connect(websocket_url) as websocket:
                        logging.info(f'Connected to WebSocket {websocket_url}')
                        while True:
                            message = await websocket.recv()
                            if isinstance(message, bytes):
                                await websocket.pong(message)
                            else:
                                self.__update_price(message)
                except (websockets.ConnectionClosedError, websockets.ConnectionClosed):
                    logging.error(f"Connection lost. Try to reconnect")
                    await asyncio.sleep(5)
                except Exception as e:
                    logging.error(f"Unexpected error occurred", exc_info=True)
                    await asyncio.sleep(5)

        t = threading.Thread(target=run, daemon=True)
        t.start()
        self.threads.append(t)

    def __update_price(self, message):

        data = json.loads(message)
        payload = data['data']
        symbol = payload['s']
        received_price = Decimal(payload['p'])
        if received_price != self.__last_price:
            self.__last_price = received_price
            self.__notify_consumers(symbol)

    def __notify_consumers(self, symbol):

        logging.debug("__notify_consumers : Start notifying consumers about price update")
        payload = {"last_price": self.__last_price, "symbol":self.symbol}
        for q in self.__consumers_queues:
            try:
                q.put_nowait(payload)
            except queue.Full:
                logging.warning(f"Price queue is full for symbol {symbol}. Dropping message.")
