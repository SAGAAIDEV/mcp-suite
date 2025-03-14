# Testing Guidelines for Pydantic Models

This guide outlines a systematic approach for creating comprehensive tests for python files.

## Test Directory Structure

Tests should be organized in a `tests` directory that mirrors the structure of the code being tested. For example:

```
.
├── __init__.py
├── coverage_models.py
├── exception_data.py
└── tests
    ├── __init__.py
    ├── test_coverage_models.py
    └── test_exception_data.py
```

Each module should have its own test file with a matching name prefixed with `test_`. The `tests` directory should be a sibling to the files being tested, not a child directory of them.

## 1. Analyze the Model Structure
- Identify all classes in the file
- Understand the attributes and their types
- Note any special methods (e.g., `__eq__`, `from_*`, `to_*`)
- Identify class methods and instance methods

## 2. Create Test File Structure
- Create a test file with the naming convention `test_<original_file_name>.py` in the `tests` directory
- Import the necessary modules (pytest, typing, the models to test)
- Create a test class for each model class (`TestClassName` for each `ClassName`)
- Add docstrings to describe what's being tested
- Ensure the `tests` directory has an `__init__.py` file to make it a proper package

## 3. Test Basic Functionality
- Test initialization with valid parameters
- Verify all attributes are correctly set
- Test default values if applicable

## 4. Test Special Methods
- For `__str__` or `__repr__`: Test string representation
- For `__eq__` and `__ne__`: Test equality and inequality with identical, similar, and different objects
- For comparison methods: Test ordering operations

## 5. Test Conversion Methods
- For `from_*` methods: Test conversion from different formats
- For `to_*` methods: Test conversion to different formats
- Test with valid and invalid inputs

## 6. Test Error Handling
- Use `pytest.raises` to test that appropriate exceptions are raised
- Test edge cases and boundary conditions
- Test with invalid inputs

## 7. Test Complex Scenarios
- For methods that interact with external systems, use mocks
- For methods with complex logic, test different paths through the code
- For methods that handle nested data structures, test with various levels of nesting

## 8. Verify Coverage
- Run tests with coverage to identify any untested code
- Add tests for any uncovered lines or branches
- Aim for 100% coverage

## Example Patterns

### Basic Test Method
```python
def test_method_name(self):
    """Clear description of what's being tested."""
    # Setup - create necessary objects
    obj = ClassName(param1=value1, param2=value2)
    
    # Exercise - call the method being tested
    result = obj.method_to_test()
    
    # Verify - check that the result is as expected
    assert result == expected_value
    
    # Additional verifications as needed
    assert obj.attribute == expected_attribute
```

### Exception Testing
```python
def test_method_raises_exception(self):
    """Test that method raises appropriate exception."""
    with pytest.raises(ExpectedException, match="Expected error message"):
        # Code that should raise the exception
        obj.method_that_should_raise()
```

### Testing Class Methods
```python
def test_class_method(self):
    """Test a class method."""
    # Setup - prepare input data
    input_data = [value1, value2]
    
    # Exercise - call the class method
    result = ClassName.from_list(input_data)
    
    # Verify - check that the result is as expected
    assert isinstance(result, ClassName)
    assert result.attribute1 == value1
    assert result.attribute2 == value2
```

### Testing Equality
```python
def test_equality(self):
    """Test equality comparison."""
    # Create objects for comparison
    obj1 = ClassName(param1=value1, param2=value2)
    obj2 = ClassName(param1=value1, param2=value2)  # Same values
    obj3 = ClassName(param1=different_value, param2=value2)  # Different value
    
    # Test equality
    assert obj1 == obj2  # Should be equal
    assert obj1 != obj3  # Should not be equal
    
    # Test inequality with other types
    assert obj1 != "not a class instance"
    assert obj1 != None
```

## Running Tests and Coverage

When running tests, use the MCP tool for pytest as specified in the cursor rules:

```
# Run tests for a specific file
mcp__run_pytest file_path="path/to/tests/test_file.py"

# Run all tests in a module
mcp__run_pytest file_path="path/to/module/tests/"

# Run all tests in the project
mcp__run_pytest file_path="."
```

After running tests, check coverage for specific files:

```
# Check coverage for a specific file
mcp__run_coverage file_path="path/to/module/file.py"
```

Remember to add the `# pragma: no cover` comment for `if __name__ == "__main__"` blocks:

```python
if __name__ == "__main__":  # pragma: no cover
    # Code that runs when the file is executed directly
    pass
```

## Import Paths in Tests

When importing the modules to test, use the relative import path from the project root:

```python
# In test_coverage_models.py
from ..coverage_models import (
    BranchCoverage,
    CoverageIssue,
)
```

This ensures that the tests are running against the installed package rather than a local copy, which helps catch import-related issues.

By following these guidelines, you can create thorough tests for Pydantic models that verify all functionality and achieve 100% code coverage. 