"""Technical Debt Estimator - Quantify technical debt in developer-hours."""

__version__ = "0.1.0"
__author__ = "Glue"
__email__ = "hello@glue.tools"
__license__ = "MIT"

from .analyzer import TechnicalDebtAnalyzer, DebtResult

__all__ = ["TechnicalDebtAnalyzer", "DebtResult", "__version__"]
