"""
Tests for the Singleton base class.

This module contains tests for the Singleton class in mcp_suite.base.models.singleton.
"""

import pytest

from ..singleton import Singleton


class TestSingleton:
    """Tests for the Singleton base class."""

    def test_singleton_instance_creation(self):
        """Test that a singleton instance is created correctly."""

        # Define a test class that inherits from Singleton
        class TestConfig(Singleton):
            debug: bool = False
            timeout: int = 30

        # Create an instance
        config1 = TestConfig(debug=True)

        # Verify the instance was created with the provided values
        assert config1.debug is True
        assert config1.timeout == 30

    def test_singleton_returns_same_instance(self):
        """Test that the same instance is returned for the same class."""

        # Define a test class that inherits from Singleton
        class TestConfig(Singleton):
            debug: bool = False
            timeout: int = 30

        # Create an instance
        config1 = TestConfig(debug=True)

        # Get another instance
        config2 = TestConfig()

        # Verify they are the same object
        assert config1 is config2
        assert config1.debug is True  # The value from the first instance should persist

    def test_singleton_update_instance(self):
        """Test that updating a singleton instance works correctly."""

        # Define a test class that inherits from Singleton
        class TestConfig(Singleton):
            debug: bool = False
            timeout: int = 30

        # Create an instance
        config1 = TestConfig(debug=True)

        # Update the instance
        config2 = TestConfig(timeout=60)

        # Verify the instance was updated
        assert config1 is config2
        assert config1.debug is True  # Original value should persist
        assert config1.timeout == 60  # New value should be applied

    def test_get_instance_method(self):
        """Test the get_instance class method."""

        # Define a test class that inherits from Singleton
        class TestConfig(Singleton):
            debug: bool = False
            timeout: int = 30

        # Create an instance
        config1 = TestConfig(debug=True)

        # Get the instance using get_instance
        config2 = TestConfig.get_instance()

        # Verify they are the same object
        assert config1 is config2
        assert config2.debug is True

    def test_reset_instance_method(self):
        """Test the reset_instance class method."""

        # Define a test class that inherits from Singleton
        class TestConfig(Singleton):
            debug: bool = False
            timeout: int = 30

        # Create an instance
        config1 = TestConfig(debug=True)

        # Reset the instance
        result = TestConfig.reset_instance()

        # Verify the reset was successful
        assert result is True

        # Create a new instance
        config2 = TestConfig()

        # Verify it's a different instance with default values
        assert config1 is not config2
        assert config2.debug is False
        assert config2.timeout == 30

    def test_reset_nonexistent_instance(self):
        """Test resetting a non-existent instance."""

        # Define a test class that inherits from Singleton
        class TestConfig(Singleton):
            debug: bool = False
            timeout: int = 30

        # Reset without creating an instance first
        result = TestConfig.reset_instance()

        # Verify the reset failed
        assert result is False

    def test_multiple_singleton_classes(self):
        """Test that different singleton classes have different instances."""

        # Define two test classes that inherit from Singleton
        class TestConfig1(Singleton):
            value: str = "config1"

        class TestConfig2(Singleton):
            value: str = "config2"

        # Create instances
        config1 = TestConfig1()
        config2 = TestConfig2()

        # Verify they are different objects with different values
        assert config1 is not config2
        assert config1.value == "config1"
        assert config2.value == "config2"

    def test_singleton_with_inheritance(self):
        """Test that singleton works correctly with inheritance."""

        # Define a base class that inherits from Singleton
        class BaseConfig(Singleton):
            debug: bool = False
            timeout: int = 30

        # Define a subclass that inherits from BaseConfig
        class SubConfig(BaseConfig):
            extra: str = "default"

        # Create instances
        base_config = BaseConfig(debug=True)
        sub_config = SubConfig(extra="custom")

        # Verify they are different objects
        assert base_config is not sub_config
        assert base_config.debug is True
        assert sub_config.debug is False  # Should have default value
        assert sub_config.extra == "custom"

    def test_singleton_with_pydantic_validation(self):
        """Test that Pydantic validation works with Singleton."""

        # Define a test class with validation
        class ValidatedConfig(Singleton):
            port: int = (
                0  # Provide a default value to avoid validation error during __new__
            )

            model_config = {
                "arbitrary_types_allowed": True,
            }

        # Reset any existing instance to ensure clean test
        ValidatedConfig.reset_instance()

        # Create an instance with valid data
        config = ValidatedConfig(port=8080)
        assert config.port == 8080

        # Test validation by creating a separate class
        # This avoids the singleton pattern returning the existing instance
        class AnotherValidatedConfig(Singleton):
            port: int

            model_config = {
                "arbitrary_types_allowed": True,
            }

        # Try to create an instance with invalid data
        with pytest.raises(Exception) as excinfo:
            AnotherValidatedConfig(port="invalid")

        # Check that the error is related to validation
        assert "validation error" in str(excinfo.value).lower()
