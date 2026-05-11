import re

import pytest

pytest_plugins = ("pytester",)


def test_mongo_fixtures_discoverable_via_entrypoint(pytester: pytest.Pytester) -> None:
    result = pytester.runpytest("--fixtures", "-q")
    assert result.ret == 0
    output = result.stdout.str()
    # pytest --fixtures lists each as `name [scope scope] -- path:line`.
    # Anchor on `name [` so e.g. "mongo" doesn't spuriously match `mongo_6_rs`.
    for name in (
        "mongo",
        "mongo_5",
        "mongo_6",
        "mongo_7",
        "mongo_8",
        "mongo_rs",
        "mongo_5_rs",
        "mongo_6_rs",
        "mongo_7_rs",
        "mongo_8_rs",
    ):
        pattern = rf"(?m)^{re.escape(name)}\s+\["
        assert re.search(pattern, output), f"fixture {name!r} not listed in `pytest --fixtures` output"


def test_pytest_mg_importable_in_subprocess(pytester: pytest.Pytester) -> None:
    pytester.makepyfile(
        test_import="""
        import pytest_mg


        def test_mongo_dataclass_constructible() -> None:
            m = pytest_mg.Mongo(host="example", port=27017)
            assert m.host == "example"
            assert m.port == 27017


        def test_run_mongo_callable() -> None:
            assert callable(pytest_mg.run_mongo)
            assert callable(pytest_mg.run_mongo_replicaset)
        """
    )
    result = pytester.runpytest_subprocess("-q")
    result.assert_outcomes(passed=2)
