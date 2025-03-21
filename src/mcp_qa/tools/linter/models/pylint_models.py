from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field


class PylintError(BaseModel):
    model_config = ConfigDict(frozen=False)

    path: Path
    line: int
    column: int
    message: str
    symbol: str
    message_id: str = Field(alias="message-id")
    type: str

    @property
    def group_key(self) -> str:
        """Computed field combining message_id and path for grouping."""
        return f"{self.path}:{self.message_id}"

    def format(self, include_column: bool = False, include_type: bool = False) -> str:
        """Format error details with optional components.

        Args:
            include_column: Include column number in output
            include_type: Include error type in output
        """
        location = f"Line {self.line}"
        if include_column:
            location += f", Col {self.column}"

        error_info = f"{self.message} ({self.symbol})"
        if include_type:
            error_info += f" [{self.type}]"

        return f"{location}: {error_info}"
