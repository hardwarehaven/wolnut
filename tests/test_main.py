import runpy
import pytest


def test_main_dunder(mocker):
    """
    Tests that running the __main__.py script calls the wolnut() function from the cli module.
    """
    mock_wolnut = mocker.patch("wolnut.cli.wolnut", return_value=99)
    # Configure the mock to also raise SystemExit, just like the real sys.exit()
    mock_exit = mocker.patch("sys.exit", side_effect=SystemExit)

    with pytest.raises(SystemExit):
        runpy.run_module("wolnut.__main__", run_name="__main__")

    mock_wolnut.assert_called_once()
    mock_exit.assert_called_once_with(status=99)
