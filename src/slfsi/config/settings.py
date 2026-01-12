"""Central settings for SL-FSI file layout."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from slfsi.config.paths import find_repo_root


@dataclass(frozen=True)
class Settings:
    """Filesystem settings for the SL-FSI project.

    Attributes:
        repo_root: Root directory of the repository.
        data_dir: Base data directory.
        processed_dir: Processed data location.
        external_dir: External data location.
        merged_dir: Merged panel outputs.
        outputs_dir: Analysis outputs (tables, reports).
        figures_dir: Visualization outputs.
        configs_dir: Configuration files directory.
    """

    repo_root: Path
    data_dir: Path
    processed_dir: Path
    external_dir: Path
    merged_dir: Path
    outputs_dir: Path
    figures_dir: Path
    configs_dir: Path

    @classmethod
    def from_repo_root(cls, repo_root: Path) -> "Settings":
        data_dir = repo_root / "data"
        return cls(
            repo_root=repo_root,
            data_dir=data_dir,
            processed_dir=data_dir / "processed",
            external_dir=data_dir / "external",
            merged_dir=data_dir / "merged",
            outputs_dir=repo_root / "outputs",
            figures_dir=repo_root / "figures",
            configs_dir=repo_root / "configs",
        )

    @classmethod
    def default(cls) -> "Settings":
        """Build settings relative to the detected repository root."""
        return cls.from_repo_root(find_repo_root())
