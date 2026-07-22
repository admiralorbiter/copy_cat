import sys
import asyncio
from PySide6.QtWidgets import QApplication
import qasync

from copycat.services.edge_tts_provider import EdgeTTSSpeechProvider
from copycat.services.qt_audio_output import QtAudioPlayerService
from copycat.controller.main_controller import MainController
from copycat.ui.main_window import MainWindow

def main() -> None:
    app = QApplication(sys.argv)
    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)

    speech_provider = EdgeTTSSpeechProvider()
    audio_output = QtAudioPlayerService()
    controller = MainController(speech_provider=speech_provider, audio_output=audio_output)

    window = MainWindow(controller=controller)
    window.show()

    with loop:
        loop.run_forever()

if __name__ == "__main__":
    main()
