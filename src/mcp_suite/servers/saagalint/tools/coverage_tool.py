"""Coverage tool for the SaagaLint MCP server."""

import json

from mcp_suite.servers.saagalint import logger
from mcp_suite.servers.saagalint.service.coverage_service import process_coverage_json
from mcp_suite.servers.saagalint.utils.decorators import exception_handler
from mcp_suite.servers.saagalint.utils.git_utils import get_git_root


@exception_handler()
async def run_coverage(file_path):
    """
    file_path: THe file path you would like from the coverage report, make it relative
    """
    logger.info("Running coverage analysis")

    coverage_results_file = get_git_root() / "reports/coverage.json"
    result = process_coverage_json(coverage_results_file)
    # Log each coverage issue for debugging
    for issue in result:
        issue_data = issue.model_dump()
        logger.debug(f"Coverage issue details: {json.dumps(issue_data, indent=2)}")
    if file_path:
        result = next((item for item in result if item.file_path == file_path), None)
    else:
        result = str(result.values()[0])

    if result:
        logger.warning(f"Coverage issues found: {len(result)} issues")
        return {
            "Message": str(result),
            "Instructions": (
                "We're making great progress! Let's improve the test coverage "
                "for these areas. I'll help you understand what needs to be tested "
                "and how to write effective tests for the missing coverage. "
                "Once you've added the tests, run the pytest tool again. "
                "Remember, better test coverage means more reliable code!"
            ),
        }
    else:
        logger.info("Coverage is complete!")
        return {
            "Message": (
                "Outstanding job! Your test coverage is complete and comprehensive. "
                "You're doing excellent work!"
            ),
            "Instructions": (
                "You're on a roll! Let's continue with running the linting tools "
                "to make sure your code style is as perfect as your test coverage. "
                "Keep up the great work!"
            ),
        }
