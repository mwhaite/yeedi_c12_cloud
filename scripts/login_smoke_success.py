"""Quick smoke-test script for validating a successful Yeedi login."""

from __future__ import annotations

from custom_components.yeedi_c12_cloud.const import (
    CONF_ACCOUNT,
    CONF_COUNTRY,
    CONF_PASSWORD,
)
from scripts.login_test_utils import (
    exit_with_result,
    load_from_env,
    run_async,
    validate_login,
)


def main() -> None:
    creds = load_from_env()
    result = run_async(
        validate_login(
            account=creds[CONF_ACCOUNT],
            password=creds[CONF_PASSWORD],
            country=creds[CONF_COUNTRY],
            expect_success=True,
        )
    )
    exit_with_result(result)


if __name__ == "__main__":
    main()
