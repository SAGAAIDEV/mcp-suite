"""Tests for exception data models."""

from mcp_suite.servers.saagalint.models.exception_data import (
    ExceptionData,
    TracebackEntry,
)


class TestTracebackEntry:
    """Tests for the TracebackEntry class."""

    def test_init(self):
        """Test initialization of TracebackEntry."""
        entry = TracebackEntry(
            file_path="/path/to/file.py", lineno=42, name="some_function"
        )
        assert entry.file_path == "/path/to/file.py"
        assert entry.lineno == 42
        assert entry.name == "some_function"


class TestExceptionData:
    """Tests for the ExceptionData class."""

    def test_init(self):
        """Test initialization of ExceptionData."""
        traceback_entries = [
            TracebackEntry(
                file_path="/path/to/file1.py", lineno=42, name="some_function"
            ),
            TracebackEntry(
                file_path="/path/to/file2.py", lineno=24, name="another_function"
            ),
        ]
        exc_data = ExceptionData(
            traceback=traceback_entries, error_type="ValueError", error="Invalid value"
        )
        assert exc_data.traceback == traceback_entries
        assert exc_data.error_type == "ValueError"
        assert exc_data.error == "Invalid value"

    def test_from_exception(self):
        """Test creating from an actual exception."""
        try:
            # Create a simple exception
            raise ValueError("Test exception")
        except ValueError as e:
            exc_type, exc_value, exc_traceback = (type(e), e, e.__traceback__)
            exc_data = ExceptionData.from_exception(exc_type, exc_value, exc_traceback)

        # Verify the exception data
        assert exc_data.error_type == "ValueError"
        assert exc_data.error == "Test exception"
        assert isinstance(exc_data.traceback, list)
        assert len(exc_data.traceback) > 0

        # Check the first traceback entry
        first_entry = exc_data.traceback[-1]  # Last entry is where exception was raised
        assert isinstance(first_entry, TracebackEntry)
        assert "test_exception_data.py" in first_entry.file_path
        assert first_entry.name == "test_from_exception"

    def test_from_exception_nested(self):
        """Test creating from a nested exception."""

        def inner_function():
            raise ValueError("Inner exception")

        def outer_function():
            try:
                inner_function()
            except ValueError as e:
                raise RuntimeError("Outer exception") from e

        try:
            outer_function()
        except RuntimeError as e:
            exc_type, exc_value, exc_traceback = (type(e), e, e.__traceback__)
            exc_data = ExceptionData.from_exception(exc_type, exc_value, exc_traceback)

        # Verify the exception data
        assert exc_data.error_type == "RuntimeError"
        assert exc_data.error == "Outer exception"
        assert isinstance(exc_data.traceback, list)
        assert len(exc_data.traceback) >= 2  # At least 2 frames

        # Check that we have both function calls in the traceback
        function_names = [entry.name for entry in exc_data.traceback]
        assert "outer_function" in function_names
        assert "test_from_exception_nested" in function_names

    def test_equality(self):
        """Test equality comparison."""
        # Create two identical exception data objects
        traceback_entries1 = [
            TracebackEntry(
                file_path="/path/to/file.py", lineno=42, name="some_function"
            )
        ]
        exc_data1 = ExceptionData(
            traceback=traceback_entries1, error_type="ValueError", error="Invalid value"
        )

        traceback_entries2 = [
            TracebackEntry(
                file_path="/path/to/file.py", lineno=42, name="some_function"
            )
        ]
        exc_data2 = ExceptionData(
            traceback=traceback_entries2, error_type="ValueError", error="Invalid value"
        )

        # Different traceback but same error type and message
        traceback_entries3 = [
            TracebackEntry(
                file_path="/different/path.py", lineno=100, name="different_function"
            )
        ]
        exc_data3 = ExceptionData(
            traceback=traceback_entries3, error_type="ValueError", error="Invalid value"
        )

        # Different error type
        exc_data4 = ExceptionData(
            traceback=traceback_entries1, error_type="TypeError", error="Invalid value"
        )

        # Different error message
        exc_data5 = ExceptionData(
            traceback=traceback_entries1,
            error_type="ValueError",
            error="Different message",
        )

        # Test equality
        assert exc_data1 == exc_data2
        assert exc_data1 == exc_data3  # Should be equal despite different traceback
        assert exc_data1 != exc_data4  # Different error type
        assert exc_data1 != exc_data5  # Different error message

        # Test inequality with other types
        assert exc_data1 != "not an exception data"
        assert exc_data1 != 42
        assert exc_data1 is not None

    def test_inequality(self):
        """Test inequality operator."""
        exc_data1 = ExceptionData(
            traceback=[
                TracebackEntry(
                    file_path="/path/to/file.py", lineno=42, name="some_function"
                )
            ],
            error_type="ValueError",
            error="Invalid value",
        )

        exc_data2 = ExceptionData(
            traceback=[
                TracebackEntry(
                    file_path="/path/to/file.py", lineno=42, name="some_function"
                )
            ],
            error_type="ValueError",
            error="Invalid value",
        )

        exc_data3 = ExceptionData(
            traceback=[
                TracebackEntry(
                    file_path="/path/to/file.py", lineno=42, name="some_function"
                )
            ],
            error_type="TypeError",
            error="Invalid value",
        )

        # Test inequality operator
        assert not (exc_data1 != exc_data2)
        assert exc_data1 != exc_data3
