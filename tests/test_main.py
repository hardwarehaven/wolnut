import runpy
import pytest


def test_main_dunder(mocker):
    """
    Tests that running the __main__.py script calls the wolnut() function from the cli module.
    """
    mock_wolnut = mocker.patch("wolnut.cli.wolnut", side_effect=SystemExit)

    # The click entry point will raise a SystemExit, which is expected.
    with pytest.raises(SystemExit):
        runpy.run_module("wolnut.__main__", run_name="__main__")

    mock_wolnut.assert_called_once()
