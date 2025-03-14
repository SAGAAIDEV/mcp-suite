from typing import List

from mcp_suite.base.base_service import BaseService


class {{cookiecutter.project_slug}}Credentials:
    pass

class {{cookiecutter.project_slug}}Account:
    pass


class {{cookiecutter.project_slug}}Service(BaseService):

    accounts: List[{{cookiecutter.project_slug}}Account] = Field(default_factory=[{{cookiecutter.project_slug}}Account()])

