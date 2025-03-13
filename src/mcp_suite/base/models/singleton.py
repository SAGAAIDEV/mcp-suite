"""
Singleton base class for MCP Suite.

This module provides a base class for singleton Pydantic models.
"""

from typing import Any, ClassVar, Dict, Type, TypeVar

from loguru import logger
from pydantic import BaseModel

T = TypeVar("T", bound="Singleton")


class Singleton(BaseModel):
    """
    Base class for singleton Pydantic models.

    This class ensures that only one instance of a model exists in memory.
    Subclasses will always return the same instance for the same class.

    Example:
        ```python
        from mcp_suite.models.singleton import Singleton

        class Config(Singleton):
            debug: bool = False
            timeout: int = 30

        # Create an instance
        config1 = Config(debug=True)

        # Get the same instance
        config2 = Config()
        print(config2.debug)  # Prints "True"

        # They are the same object
        assert config1 is config2  # True
        ```
    """

    # Class variables
    _instances: ClassVar[Dict[Type, Any]] = {}
    model_config = {"arbitrary_types_allowed": True}

    def __new__(cls, **kwargs):
        """
        Create a new instance or return the existing one.

        If an instance already exists in memory, return it.
        Otherwise, create a new instance.
        """
        # Check if we already have an instance in memory for this exact class
        if cls not in cls._instances:
            # Create a new instance
            instance = super().__new__(cls)
            # Initialize with default values first
            BaseModel.__init__(instance)
            cls._instances[cls] = instance
            logger.debug(f"Created new singleton instance of {cls.__name__}")
        else:
            # Return the existing instance
            instance = cls._instances[cls]
            logger.debug(f"Returning existing singleton instance of {cls.__name__}")

        return instance

    def __init__(self, **data):
        """
        Initialize the singleton instance.

        This method is called after __new__ and will initialize the instance
        with the provided data. If the instance already exists and data is provided,
        it will update the instance with the new data.
        """
        # If data is provided, update the instance
        if data:
            # We need to call model_copy to update the instance with new values
            # This is the proper way to update a Pydantic model
            updated_instance = self.model_copy(update=data)

            # Copy all attributes from the updated instance to self
            for key, value in updated_instance.model_dump().items():
                setattr(self, key, value)

            logger.debug(
                f"Updated singleton instance of {self.__class__.__name__} with new data"
            )

    @classmethod
    def get_instance(cls: Type[T]) -> T:
        """
        Get the singleton instance of this class.

        If an instance doesn't exist yet, it will be created with default values.

        Returns:
            The singleton instance
        """
        return cls()

    @classmethod
    def reset_instance(cls) -> None:
        """
        Reset the singleton instance of this class.

        This will remove the current instance from the instances dictionary,
        allowing a new instance to be created next time.
        """
        if cls in cls._instances:
            del cls._instances[cls]
            logger.debug(f"Reset singleton instance of {cls.__name__}")
            return True
        return False
