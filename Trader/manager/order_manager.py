import asyncio
import json
import logging
import queue
import threading
import time

import requests

from manager.abstract_manager import AbstractManager
import websockets


class OrderManager(AbstractManager):

    def __init__(self, app_config):
        super().__init__(app_config)
        self.threads = []
        self.order_queues = None
        self.listen_key = None

    def set_order_queues(self, order_queues):
        self.order_queues = order_queues

    def start(self):
        self.create_listen_key()
        self.schedule_listen_key_renew()
        self.monitor_orders()

    def create_listen_key(self):
        logging.debug("create_listen_key : Start creating listen key for orders update")
        try:
            api_config = self.app_config.api_config
            url = api_config.trades_config.base_url + '/api/v3/userDataStream'
            credentials = api_config.credentials
            headers = {
                'X-MBX-APIKEY': credentials.api_key
            }

            response = requests.post(url, headers=headers)
            data = response.json()

            if response.status_code == 200:
                listen_key = data['listenKey']
                logging.info(f"create_listen_key : Listen Key created : {listen_key}")
                self.listen_key = listen_key
            else:
                logging.error(f"create_listen_key : Error while creating the listen key : {data}")
        except Exception as e:
            logging.error('create_listen_key : An error occurred while creating a listen key')

    def monitor_orders(self):
        api_config = self.app_config.api_config
        trades_config = api_config.trades_config
        websocket_url = trades_config.websocket_base_url + f"/ws/{self.listen_key}"

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
                                data = json.loads(message)
                                for q in self.order_queues:
                                    try:
                                        q.put_nowait(data)
                                    except queue.Full:
                                        logging.warning("handler : order queue is full. Dropping message.")
                except (websockets.ConnectionClosedError, websockets.ConnectionClosed):
                    logging.error(f"handler : Connection lost for {websocket_url}. Try to reconnect")
                    await asyncio.sleep(5)
                except Exception as e:
                    logging.error(f"handler : An error occurred while processing order update message", exc_info=True)
                    await asyncio.sleep(5)

        monitor_orders_thread = threading.Thread(target=run, daemon=True)
        monitor_orders_thread.start()
        self.threads.append(monitor_orders_thread)

    def schedule_listen_key_renew(self):
        renew_listen_key_thread = threading.Thread(target=self.keep_alive_listen_key, args=(), daemon=True)
        renew_listen_key_thread.start()
        self.threads.append(renew_listen_key_thread)

    def keep_alive_listen_key(self):

        api_config = self.app_config.api_config
        url = api_config.trades_config.base_url + '/api/v3/userDataStream'
        credentials = api_config.credentials
        headers = {
            'X-MBX-APIKEY': credentials.api_key
        }

        params = {
            'listenKey': self.listen_key
        }

        while True:
            try:
                time.sleep(1800)
                response = requests.put(url, headers=headers, params=params)
                if response.status_code == 200:
                    logging.info("Listen Key renewed with success.")
                else:
                    logging.error(
                        f"keep_alive_listen_key : Error while trying to keep alive Listen Key : {response.json()}")
                    self.create_listen_key()
            except Exception as e:
                logging.error("An error occurred while trying to keep alive Listen Key")
                self.create_listen_key()

    def get_threads(self):

        return self.threads
