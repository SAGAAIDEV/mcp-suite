"""Tests for the module_utils module."""

from unittest.mock import MagicMock, patch

import pytest

from mcp_qa.utils.module_utils import get_reinitalized_mcp


@pytest.fixture
def mock_mcp():
    """Fixture for a mock MCP instance."""
    return MagicMock()


@pytest.fixture
def mock_file():
    """Fixture for a mock file path."""
    return "test_file.py"


@pytest.fixture
def mock_module_with_mcp():
    """Fixture for a mock module with an mcp attribute."""
    mock_module = MagicMock()
    mock_module.mcp = MagicMock()
    return mock_module


@pytest.fixture
def mock_module_without_mcp():
    """Fixture for a mock module without an mcp attribute."""
    mock_module = MagicMock()
    # Ensure no mcp attribute exists
    if hasattr(mock_module, "mcp"):
        delattr(mock_module, "mcp")
    return mock_module


@pytest.fixture
def mock_spec():
    """Fixture for a mock spec."""
    return MagicMock()


@pytest.mark.parametrize(
    "module_fixture,expected_result",
    [
        ("mock_module_with_mcp", "module_mcp"),  # Test with module having mcp attribute
        ("mock_module_without_mcp", "original_mcp"),  # Test without mcp attribute
    ],
)
def test_get_reinitalized_mcp_scenarios(
    module_fixture, expected_result, mock_mcp, mock_file, mock_spec, request
):
    """Test different scenarios for get_reinitalized_mcp function."""
    # Get the module fixture
    mock_module = request.getfixturevalue(module_fixture)

    # Setup patches
    with patch(
        "importlib.util.spec_from_file_location", return_value=mock_spec
    ) as mock_spec_from_file:
        with patch(
            "importlib.util.module_from_spec", return_value=mock_module
        ) as mock_module_from_spec:
            # Call the function
            result = get_reinitalized_mcp(mock_mcp, mock_file)

            # Common assertions
            mock_spec_from_file.assert_called_once()
            mock_module_from_spec.assert_called_once_with(mock_spec)
            mock_spec.loader.exec_module.assert_called_once_with(mock_module)

            # Check the expected result
            if expected_result == "module_mcp":
                assert result == mock_module.mcp
            else:
                assert result == mock_mcp


def test_get_reinitalized_mcp_exception(mock_mcp, mock_file):
    """Test handling of exceptions during reinitialization."""
    # Setup patch with side effect
    with patch(
        "importlib.util.spec_from_file_location",
        side_effect=Exception("Test exception"),
    ) as mock_spec_from_file:
        # Call the function and check for exception
        with pytest.raises(Exception):
            get_reinitalized_mcp(mock_mcp, mock_file)

        # Verify the mock was called
        mock_spec_from_file.assert_called_once()


if __name__ == "__main__":  # pragma: no cover
    pytest.main()
