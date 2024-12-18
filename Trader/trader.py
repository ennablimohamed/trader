import logging
from logging.handlers import RotatingFileHandler

from manager.app_manager import AppManager
from config.config_util import load_current_config


def init_logger():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    handler = RotatingFileHandler('trader.log', maxBytes=5 * 1024 * 1024,
                                  backupCount=5)  # 5MB par fichier, 5 fichiers de sauvegarde
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

def start():
    init_logger()
    app_config = load_current_config()
    app_manager = AppManager(app_config=app_config)
    app_manager.start()


















if __name__ == '__main__':
    start()