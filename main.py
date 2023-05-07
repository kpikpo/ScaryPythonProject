import logging
import time
import traceback
from pathlib import Path
from ui.chat_app import ChatApp

Path("logs").mkdir(parents=True, exist_ok=True)
console = logging.StreamHandler()
console.setLevel(logging.INFO)
# add the handler to the root logger
logging.basicConfig(
    filename=f'logs/{time.time()}.log',
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')
logging.getLogger('').addHandler(console)

# Log uncaught exceptions
try:
    app = ChatApp()
    exit(app.exec())
except Exception as e:
    logging.critical(traceback.format_exc())
