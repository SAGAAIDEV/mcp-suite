"""
Tests for the Singleton base class.

This module tests the functionality of the Singleton base class.
"""

import pytest

from mcp_suite.base.models.singleton import Singleton


@pytest.fixture(autouse=True)
def reset_singleton():
    """Reset all singleton instances before and after each test."""
    # Clear the _instances and _initialized dictionaries before the test
    Singleton._instances = {}
    Singleton._initialized = {}

    # Run the test
    yield

    # Clear the dictionaries after the test as well
    Singleton._instances = {}
    Singleton._initialized = {}


class TestSingleton:
    """Test cases for the Singleton base class."""

    def test_singleton_instance(self):
        """Test that a singleton class returns the same instance."""

        # Define a test singleton class
        class TestConfig(Singleton):
            value: int = 0
            model_config = {"arbitrary_types_allowed": True}

        # Create first instance with a value
        config1 = TestConfig(value=42)

        # Create second instance without parameters
        config2 = TestConfig()

        # They should be the same object
        assert config1 is config2

        # The value should be preserved from the first initialization
        assert config2.value == 42

    def test_singleton_update(self):
        """Test that updating a singleton updates the shared instance."""

        # Define a test singleton class
        class TestSettings(Singleton):
            name: str = "default"
            timeout: int = 30
            model_config = {"arbitrary_types_allowed": True}

        # Create first instance
        settings1 = TestSettings(name="test", timeout=60)

        # Create second instance
        settings2 = TestSettings()

        # They should be the same object
        assert settings1 is settings2

        # Second instance should reflect the values from initialization
        assert settings2.name == "test"
        assert settings2.timeout == 60

        # Update the second instance
        settings2.timeout = 120

        # First instance should reflect the change
        assert settings1.timeout == 120

    def test_get_instance(self):
        """Test the get_instance class method."""

        # Define a test singleton class
        class TestLogger(Singleton):
            enabled: bool = False
            level: str = "INFO"
            model_config = {"arbitrary_types_allowed": True}

        # Create an instance with custom values
        logger1 = TestLogger(enabled=True, level="DEBUG")

        # Get instance using class method
        logger2 = TestLogger.get_instance()

        # They should be the same object
        assert logger1 is logger2

        # The values should be preserved
        assert logger2.enabled is True
        assert logger2.level == "DEBUG"

    def test_reset_instance(self):
        """Test the reset_instance class method."""

        # Define a test singleton class
        class TestCache(Singleton):
            size: int = 100
            model_config = {"arbitrary_types_allowed": True}

        # Create an instance
        cache1 = TestCache(size=200)

        # Verify the size is set
        assert cache1.size == 200

        # Reset the instance
        TestCache.reset_instance()

        # Create a new instance
        cache2 = TestCache()

        # They should be different objects
        assert cache1 is not cache2

        # The new instance should have default values
        assert cache2.size == 100

    def test_multiple_singleton_classes(self):
        """Test that different singleton classes have separate instances."""

        # Define two test singleton classes
        class TestConfigA(Singleton):
            value: str = "A"
            model_config = {"arbitrary_types_allowed": True}

        class TestConfigB(Singleton):
            value: str = "B"
            model_config = {"arbitrary_types_allowed": True}

        # Create instances
        config_a = TestConfigA()
        config_b = TestConfigB()

        # They should be different objects
        assert config_a is not config_b

        # They should have their own values
        assert config_a.value == "A"
        assert config_b.value == "B"

        # Modifying one shouldn't affect the other
        config_a.value = "Modified A"
        assert config_b.value == "B"

    def test_inheritance(self):
        """Test that singleton behavior works with inheritance."""

        # Define a base singleton class
        class BaseConfig(Singleton):
            debug: bool = False
            model_config = {"arbitrary_types_allowed": True}

        # Define a subclass
        class DerivedConfig(BaseConfig):
            verbose: bool = False
            model_config = {"arbitrary_types_allowed": True}

        # Create instances
        base = BaseConfig(debug=True)
        derived = DerivedConfig(verbose=True)

        # They should be different objects
        assert base is not derived

        # Create another instance of each
        base2 = BaseConfig()
        derived2 = DerivedConfig()

        # Each should match its own previous instance
        assert base is base2
        assert derived is derived2

        # Values should be preserved
        assert base2.debug is True
        assert derived2.verbose is True

    def test_initialization_with_kwargs(self):
        """Test that initialization with kwargs works for the first instance only."""

        # Define a test singleton class
        class TestConfig(Singleton):
            name: str = "default"
            value: int = 0
            model_config = {"arbitrary_types_allowed": True}

        # Create first instance with kwargs
        config1 = TestConfig(name="test", value=42)

        # Values should be set from kwargs
        assert config1.name == "test"
        assert config1.value == 42

        # Reset and create a new instance
        TestConfig.reset_instance()

        # Create first instance without kwargs
        config2 = TestConfig()

        # Should have default values
        assert config2.name == "default"
        assert config2.value == 0

        # Create another instance with kwargs
        config3 = TestConfig(name="another", value=100)

        # Should be the same instance as config2
        assert config2 is config3

        # Values should be updated from kwargs on existing instance
        # This is the expected behavior with our new implementation
        assert config3.name == "another"
        assert config3.value == 100
