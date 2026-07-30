"""Package initialization for regression module."""

try:
    from regression.generator import (
        generate_regression_test,
        generate_regression_test_dict,
        generate_regression_test_json,
    )
except ImportError:
    from backend.regression.generator import (
        generate_regression_test,
        generate_regression_test_dict,
        generate_regression_test_json,
    )

__all__ = [
    "generate_regression_test",
    "generate_regression_test_dict",
    "generate_regression_test_json",
]
