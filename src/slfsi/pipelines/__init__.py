"""Pipeline entrypoints for SL-FSI workflows."""

from slfsi.pipelines.analyze import run as analyze
from slfsi.pipelines.build_panel import run as build_panel
from slfsi.pipelines.download_external import run as download_external
from slfsi.pipelines.fetch_historical import run as fetch_historical
from slfsi.pipelines.leading_indicators import run as leading_indicators
from slfsi.pipelines.mercado import run as mercado
from slfsi.pipelines.combine import run as combine
from slfsi.pipelines.theory import run as theory
from slfsi.pipelines.train_hmm import run as train_hmm
from slfsi.pipelines.validate import run as validate

__all__ = [
    "analyze",
    "build_panel",
    "combine",
    "download_external",
    "fetch_historical",
    "leading_indicators",
    "mercado",
    "theory",
    "train_hmm",
    "validate",
]
