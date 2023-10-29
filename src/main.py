import asyncio
import sys

from PyQt6 import QtWidgets
from qasync import QEventLoop

from src.window import MainWindow

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)

    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)
    window = MainWindow()
    window.show()

    loop.run_forever()
