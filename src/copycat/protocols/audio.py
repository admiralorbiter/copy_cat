from typing import Protocol, Callable

class AudioOutput(Protocol):
    def play(self, chunk: "AudioChunk") -> None:
        ...

    def pause(self) -> None:
        ...

    def resume(self) -> None:
        ...

    def stop(self) -> None:
        ...
