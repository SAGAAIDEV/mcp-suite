# Unit Testing Guidelines

## Getting Started

The first step in writing a unit test is to create the appropriate test file using our MCP utilities:

### 1. Check if Test File Exists

First, check if a test file already exists using mcp tool `source_to_test_path`:

### 2. Create Test File if Needed

If the test file doesn't exist, create it using mcp tool `create_test_file`:

This approach ensures test files are created in the correct location following our project structure.

### 3. Plan the test write the test.

## Core Testing Principles

1. **Maximum Coverage, Minimum Code**: Write tests that cover all code paths with the least possible testing code.
2. **One Class Per Function**: Every function should have its own test class for clear organization.
3. **Multiple Test Methods**: Test different scenarios and edge cases as separate methods.
4. **Descriptive Test Names**: Use clear, descriptive names that explain what is being tested.
5. **Isolated Tests**: Each test should be independent and not rely on other tests.

## Project Structure

## Test Organization

### Class Naming Convention

```python
def test_function_name(self):
    """Test that function_name works as expected."""
    pass

class TestClassName:
    """Tests for ClassName."""
    
    def test_method_name(self):
        """Test that method_name works as expected."""
        pass
```

### Method Naming Convention

- `test_function_does_x`
- `test_function_raises_when_y`
- `test_function_returns_z_when_condition`

## Fixtures and Setup

### When to Use Fixtures

1. **Common Test Data**: Reuse test data across multiple tests.
2. **Complex Setup**: When setup is complex and shared between tests.
3. **Resources**: Database connections, API clients, etc.

### Fixture Scope

```python
@pytest.fixture(scope="function")  # Default - recreated for each test
@pytest.fixture(scope="class")     # Created once per test class
@pytest.fixture(scope="module")    # Created once per module
@pytest.fixture(scope="session")   # Created once per test session
```

### Example Fixture

```python
@pytest.fixture
def sample_data():
    """Provide sample data for tests."""
    return {"key": "value", "number": 42}

def test_process_data(sample_data):
    """Test that process_data handles the data correctly."""
    result = process_data(sample_data)
    assert result == expected_result
```

## Mocking

### When to Mock

1. **External Dependencies**: APIs, databases, file systems
2. **Hard-to-Setup Components**: Complex objects or systems
3. **Slow Resources**: Things that would slow down tests
4. **Non-deterministic Behavior**: Random functions, time-dependent code

### Mocking Approaches

#### Using unittest.mock

```python
from unittest.mock import patch, Mock, MagicMock

@patch('module.ClassName')
def test_function(mock_class):
    mock_class.return_value.method.return_value = 'mocked_value'
    result = function_under_test()
    mock_class.assert_called_once()
    assert result == 'expected_result'
```

#### Using pytest-mock

```python
def test_function(mocker):
    mock_obj = mocker.patch('module.ClassName')
    mock_obj.method.return_value = 'mocked_value'
    result = function_under_test()
    mock_obj.method.assert_called_once()
    assert result == 'expected_result'
```

### Mock Return Values

```python
# Simple return value
mock_obj.method.return_value = 'value'

# Return different values on consecutive calls
mock_obj.method.side_effect = ['first_value', 'second_value']

# Raise an exception
mock_obj.method.side_effect = Exception('error message')

# Custom function behavior
mock_obj.method.side_effect = lambda x: x * 2
```

## Testing Exceptions

### Testing Exceptions with pytest

```python
def test_function_raises_value_error():
    """Test that function raises ValueError when given invalid input."""
    with pytest.raises(ValueError) as excinfo:
        function_under_test(invalid_input)
    
    # Optionally check the exception message
    assert "Invalid input" in str(excinfo.value)
```

### Testing Multiple Exceptions

```python
def test_function_raises_appropriate_exceptions():
    """Test function raises correct exceptions for different inputs."""
    with pytest.raises(ValueError):
        function_under_test(invalid_value)
    
    with pytest.raises(TypeError):
        function_under_test(wrong_type)
    
    with pytest.raises(KeyError):
        function_under_test(missing_key)
```

## Parameterized Tests

Use parameterized tests to test multiple inputs with the same logic:

```python
@pytest.mark.parametrize("input_value,expected_result", [
    (1, 2),
    (2, 4),
    (3, 6),
    (4, 8),
])
def test_double_function(input_value, expected_result):
    """Test that double function returns correct values for various inputs."""
    assert double(input_value) == expected_result
```

## Coverage Testing

### Running Coverage

Use our mcp tools for running tests with coverage:

```python
# Don't run pytest directly from command line
# Instead use our mcp tools
```

### Coverage Pragmas

Exclude code that shouldn't be covered:

```python
if __name__ == "__main__":  # pragma: no cover
    main()
```

## Project Testing Utilities

Our project provides utility functions to help with test creation:

### Test Path Conversion

```python
from src.utils import source_to_test_path, create_test_file

# Convert a source file path to its test file path
test_path = source_to_test_path("src/mcp_suite/module/file.py")
# Result: src/tests/unit/test_module/test_file.py

# Create a test file with directories automatically
created_path = create_test_file("src/mcp_suite/module/file.py", test_type="unit")
```

## Example Complete Test

```python
import pytest
from unittest.mock import patch, MagicMock

from src.mcp_suite.module import function_under_test


class TestFunctionUnderTest:
    """Tests for function_under_test."""
    
    @pytest.fixture
    def mock_dependency(self):
        """Fixture providing a mock dependency."""
        mock = MagicMock()
        mock.get_data.return_value = {"key": "value"}
        return mock
    
    def test_function_success(self, mock_dependency):
        """Test function_under_test succeeds with valid input."""
        with patch("src.mcp_suite.module.Dependency", return_value=mock_dependency):
            result = function_under_test({"input": "data"})
            assert result == "expected output"
            mock_dependency.get_data.assert_called_once()
    
    def test_function_empty_input(self, mock_dependency):
        """Test function_under_test handles empty input."""
        with patch("src.mcp_suite.module.Dependency", return_value=mock_dependency):
            result = function_under_test({})
            assert result == "default output"
    
    def test_function_raises_for_invalid_input(self, mock_dependency):
        """Test function_under_test raises ValueError for invalid input."""
        with patch("src.mcp_suite.module.Dependency", return_value=mock_dependency):
            with pytest.raises(ValueError) as excinfo:
                function_under_test(None)
            assert "Invalid input" in str(excinfo.value)
    
    @pytest.mark.parametrize("input_data,expected", [
        ({"type": "A"}, "result A"),
        ({"type": "B"}, "result B"),
        ({"type": "C"}, "result C"),
    ])
    def test_function_with_different_types(self, mock_dependency, input_data, expected):
        """Test function_under_test handles different input types correctly."""
        with patch("src.mcp_suite.module.Dependency", return_value=mock_dependency):
            result = function_under_test(input_data)
            assert result == expected
```

## Best Practices for Maximizing Coverage

1. **Test Edge Cases**: Null/empty inputs, boundary conditions, large values
2. **Test Error Paths**: Ensure all exception paths are tested
3. **Test All Branches**: Cover all if/else branches in the code
4. **Use Coverage Reports**: Review and address coverage gaps
5. **Combine Similar Tests**: Use parameterized tests for similar test logic
6. **Test Private Methods Indirectly**: Through public interfaces when possible
7. **Mock Complex Dependencies**: But validate interaction with those dependencies
8. **Avoid Over-Mocking**: Test real integration when practical

Remember: the goal is to achieve maximum coverage with the minimum amount of testing code, while ensuring tests remain readable and maintainable. 