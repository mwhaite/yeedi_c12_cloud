"""Negative smoke-test script ensuring invalid logins are rejected."""

from __future__ import annotations

import os

from scripts.login_test_utils import (
    exit_with_result,
    run_async,
    validate_login,
)


def main() -> None:
    account = os.getenv("YEEDI_ACCOUNT", "invalid@example.com")
    country = os.getenv("YEEDI_COUNTRY", "US")
    bad_password = os.getenv("YEEDI_BAD_PASSWORD", "not_the_real_password")

    result = run_async(
        validate_login(
            account=account,
            password=bad_password,
            country=country,
            expect_success=False,
        )
    )
    exit_with_result(result)


if __name__ == "__main__":
    main()
