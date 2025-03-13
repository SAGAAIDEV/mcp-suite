from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict


class BranchCoverage(BaseModel):
    model_config = ConfigDict(frozen=False)

    source: Union[int, str]
    target: Union[int, str]

    def __str__(self) -> str:
        return f"{self.source} -> {self.target}"

    @classmethod
    def from_list(cls, branch_list: List[Union[int, str]]) -> "BranchCoverage":
        """Create a BranchCoverage object from a list [source, target]."""
        if len(branch_list) != 2:
            raise ValueError("Branch list must have exactly 2 elements")
        return cls(source=branch_list[0], target=branch_list[1])

    def to_list(self) -> List[Union[int, str]]:
        """Convert to list format [source, target]."""
        return [self.source, self.target]


class CoverageIssue(BaseModel):
    model_config = ConfigDict(frozen=False)

    file_path: str
    section_name: str
    missing_lines: Optional[List[int]] = None
    missing_branches: Optional[List[BranchCoverage]] = None

    def __str__(self) -> str:
        result = f"{self.file_path}:{self.section_name}\n"
        if self.missing_lines:
            result += f"  Missing lines: {self.missing_lines}\n"
        if self.missing_branches:
            # Safely get the length of missing_branches
            branch_count = len(self.missing_branches) if self.missing_branches else 0
            result += f"  Missing branches: {branch_count}\n"
            for branch in self.missing_branches:
                result += f"    {branch}\n"
        return result

    def __len__(self) -> int:
        """
        Return the total number of issues (missing lines + missing branches).
        This makes the CoverageIssue object compatible with len().
        """
        line_count = len(self.missing_lines) if self.missing_lines else 0
        branch_count = len(self.missing_branches) if self.missing_branches else 0
        return line_count + branch_count

    @classmethod
    def from_dict(cls, key: str, data: Dict[str, Any]) -> "CoverageIssue":
        """Create a CoverageIssue from a dictionary entry in the coverage JSON."""
        file_path, section_name = key.split(":", 1)

        # Convert branch lists to BranchCoverage objects
        missing_branches = None
        if "missing_branches" in data and data["missing_branches"]:
            missing_branches = [
                BranchCoverage.from_list(branch) if isinstance(branch, list) else branch
                for branch in data["missing_branches"]
            ]

        return cls(
            file_path=file_path,
            section_name=section_name,
            missing_lines=data.get("missing_lines"),
            missing_branches=missing_branches,
        )

    def to_dict_entry(self) -> tuple[str, Dict[str, Any]]:
        """Convert to a key-value pair for the coverage JSON dictionary."""
        key = f"{self.file_path}:{self.section_name}"
        value = {}

        if self.missing_lines:
            value["missing_lines"] = self.missing_lines

        if self.missing_branches:
            value["missing_branches"] = [
                branch.to_list() for branch in self.missing_branches
            ]

        return key, value
