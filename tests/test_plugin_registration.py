import pytest

pytest_plugins = ("pytester",)


def test_mongo_fixtures_discoverable_via_entrypoint(pytester: pytest.Pytester) -> None:
    result = pytester.runpytest("--fixtures", "-q")
    result.stdout.fnmatch_lines(
        [
            "*mongo*",
            "*mongo_5*",
            "*mongo_6*",
            "*mongo_7*",
            "*mongo_8*",
            "*mongo_rs*",
            "*mongo_6_rs*",
        ]
    )
    assert result.ret == 0


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
