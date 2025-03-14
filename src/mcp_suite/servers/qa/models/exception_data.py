import traceback
from typing import List

from pydantic import BaseModel


class TracebackEntry(BaseModel):
    file_path: str
    lineno: int
    name: str


class ExceptionData(BaseModel):
    traceback: List[TracebackEntry]
    error_type: str
    error: str

    @classmethod
    def from_exception(cls, exc_type, exc_value, exc_traceback):
        return cls(
            traceback=[
                TracebackEntry(
                    file_path=frame.filename,
                    lineno=frame.lineno,
                    name=frame.name,
                )
                for frame in traceback.extract_tb(exc_traceback)
            ],
            error_type=exc_type.__name__,
            error=str(exc_value),
        )

    def __eq__(self, other):
        if not isinstance(other, ExceptionData):
            return False
        return self.error_type == other.error_type and self.error == other.error

    def __ne__(self, other):
        return not self.__eq__(other)
