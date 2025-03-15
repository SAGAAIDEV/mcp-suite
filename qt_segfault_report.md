# Qt Segmentation Fault Report

## Issue Summary

When running tests for the `MCPSystemTrayApp` class in `src/mcp_suite/system_tray/core/tests/test_app.py`, a segmentation fault occurs. The error is consistently triggered when running tests that involve PyQt6 components.

The specific error message is:
```
Fatal Python error: Segmentation fault

Current thread 0x00000001eacfcf40 (most recent call first):
  File "/Users/andrew/saga/mcp-suite/.venv/lib/python3.13/site-packages/_pytest/python.py", line 159 in pytest_pyfunc_call
  ...
```

## Diagnosis

After multiple attempts to fix the issue, we've determined that:

1. The segmentation fault occurs even with minimal test code that uses PyQt6
2. The issue persists despite using the `@pytest.mark.qt` decorator from pytest-qt
3. The error happens even when using proper cleanup procedures for Qt objects
4. The segmentation fault is likely related to a compatibility issue between PyQt6 and Python 3.13

## Potential Causes

1. **Python 3.13 Compatibility**: The error occurs in a Python 3.13 environment, which is a relatively new version. PyQt6 might not be fully compatible with Python 3.13 yet.

2. **C Extension Issues**: The error mentions several C extensions being loaded, including PyQt6 modules. There might be memory management issues in these extensions.

3. **QApplication Lifecycle**: Qt has strict rules about QApplication creation and destruction. Multiple QApplication instances or improper cleanup can cause segmentation faults.

## Recommendations

1. **Downgrade Python**: Consider using Python 3.11 or 3.12 instead of 3.13 for testing Qt applications, as these versions have better established compatibility with PyQt6.

2. **Use PySide6 Instead**: PySide6 is an alternative Qt binding for Python that might have better compatibility with Python 3.13.

3. **Isolate Qt Tests**: Run Qt tests in isolation with a dedicated test runner that properly manages the QApplication lifecycle.

4. **Update PyQt6**: Ensure you're using the latest version of PyQt6 that might have fixes for Python 3.13 compatibility.

5. **Use Mock Objects**: For unit tests, consider using mock objects instead of real Qt components to avoid the need for a QApplication.

6. **Add Explicit Cleanup**: Add explicit cleanup code in pytest fixtures:

```python
@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app
    # Ensure proper cleanup
    app.quit()
    app.processEvents()
    # Force garbage collection
    import gc
    gc.collect()
```

7. **Run with Xvfb**: If testing on a headless server, ensure you're using Xvfb or a similar virtual framebuffer.

## Immediate Action Plan

1. Create a minimal reproducible example to report the issue to the PyQt6 maintainers
2. Try running the tests with Python 3.11 or 3.12 to confirm if it's a Python 3.13 specific issue
3. Update the test strategy to use more mocking and less real Qt objects
4. Consider adding a CI/CD pipeline that skips Qt tests on Python 3.13 until the compatibility issues are resolved

## Long-term Solutions

1. Refactor the application to make it more testable without requiring a full QApplication
2. Create a dedicated test harness for Qt components that properly manages the QApplication lifecycle
3. Monitor PyQt6 releases for Python 3.13 compatibility improvements
4. Consider migrating to PySide6 if PyQt6 compatibility issues persist 