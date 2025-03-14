import importlib
from pathlib import Path
from typing import Any

# Import logging configuration
from mcp_suite.servers.saagalint import logger


def get_reinitalized_mcp(mcp_instance: Any, file: str) -> Any:
    """Reinitialize the module and extract the MCP instance.

    This function reloads the current module to get the latest changes.
    It handles relative imports correctly by using the existing module's
    package context.

    Args:
        mcp_instance: The current MCP instance to return as fallback
        file: The file path of the module to reload

    Returns:
        The MCP instance from the reinitialized module
    """
    logger.info("Reinitializing module")

    try:
        # Get the current module
        current_module_name = "reinit_saagalint"

        # Get the module file path
        module_path = Path(file).resolve()
        logger.info(f"Loading module from path: {module_path}")
        spec = importlib.util.spec_from_file_location(
            current_module_name,
            module_path,
        )
        module_obj = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module_obj)

        logger.info(f"Successfully loaded module: {module_obj}")

        # Return the MCP instance from the newly loaded module
        if hasattr(module_obj, "mcp"):
            logger.info("Found mcp instance in reloaded module")
            return module_obj.mcp
        else:
            logger.warning("No mcp instance found in reloaded module")
            return mcp_instance

    except Exception as e:
        logger.error(f"Error reinitializing module: {e}", exc_info=True)
        raise
