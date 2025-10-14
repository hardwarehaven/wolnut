import pytest
from unittest.mock import MagicMock, patch

from wolnut.monitor import get_ups_status, is_client_online
from wolnut.config import NutConfig


@pytest.fixture
def sample_nut_config():
    """Sample NutConfig for testing"""
    return NutConfig(
        ups="myups",
        host="localhost",
        port=3493,
        timeout=5,
        username=None,
        password=None
    )


@pytest.fixture
def sample_nut_config_with_auth():
    """Sample NutConfig with authentication"""
    return NutConfig(
        ups="secureups",
        host="nut-server",
        port=3493,
        timeout=5,
        username="monitor",
        password="secret"
    )


class TestGetUpsStatus:
    """Tests for get_ups_status function"""

    def test_get_ups_status_success(self, mocker, sample_nut_config):
        """Test successful UPS status retrieval via PyNUTClient"""
        mock_client = MagicMock()
        mock_client.GetUPSVars.return_value = {
            b'battery.charge': b'95.5',
            b'ups.status': b'OL',
            b'input.voltage': b'120.0',
            b'ups.model': b'Smart UPS 1000'
        }
        mock_pynut_class = mocker.patch('wolnut.monitor.PyNUTClient', return_value=mock_client)

        result = get_ups_status(sample_nut_config)

        assert result['battery.charge'] == '95.5'
        assert result['ups.status'] == 'OL'
        assert result['input.voltage'] == '120.0'
        assert result['ups.model'] == 'Smart UPS 1000'

        mock_pynut_class.assert_called_once_with(
            host='localhost',
            port=3493,
            login=None,
            password=None,
            timeout=5
        )
        mock_client.GetUPSVars.assert_called_once_with('myups')

    def test_get_ups_status_with_authentication(self, mocker, sample_nut_config_with_auth):
        """Test UPS status retrieval with username and password"""
        mock_client = MagicMock()
        mock_client.GetUPSVars.return_value = {
            b'battery.charge': b'100',
            b'ups.status': b'OL'
        }
        mock_pynut_class = mocker.patch('wolnut.monitor.PyNUTClient', return_value=mock_client)

        result = get_ups_status(sample_nut_config_with_auth)

        assert result['battery.charge'] == '100'
        mock_pynut_class.assert_called_once_with(
            host='nut-server',
            port=3493,
            login='monitor',
            password='secret',
            timeout=5
        )

    def test_get_ups_status_with_string_values(self, mocker, sample_nut_config):
        """Test handling of non-byte string values (some versions may return strings)"""
        mock_client = MagicMock()
        mock_client.GetUPSVars.return_value = {
            'battery.charge': '85.0',
            'ups.status': 'OB'
        }
        mocker.patch('wolnut.monitor.PyNUTClient', return_value=mock_client)

        result = get_ups_status(sample_nut_config)

        assert result['battery.charge'] == '85.0'
        assert result['ups.status'] == 'OB'

    def test_get_ups_status_mixed_types(self, mocker, sample_nut_config):
        """Test handling of mixed byte strings and regular strings"""
        mock_client = MagicMock()
        mock_client.GetUPSVars.return_value = {
            b'battery.charge': b'75.0',
            'ups.status': 'OB',
            b'input.voltage': '118.5'
        }
        mocker.patch('wolnut.monitor.PyNUTClient', return_value=mock_client)

        result = get_ups_status(sample_nut_config)

        assert result['battery.charge'] == '75.0'
        assert result['ups.status'] == 'OB'
        assert result['input.voltage'] == '118.5'

    def test_get_ups_status_pynut_error(self, mocker, sample_nut_config):
        """Test handling of PyNUTError exceptions"""
        from wolnut.monitor import PyNUTError

        mock_client = MagicMock()
        mock_client.GetUPSVars.side_effect = PyNUTError("Connection refused")
        mocker.patch('wolnut.monitor.PyNUTClient', return_value=mock_client)

        result = get_ups_status(sample_nut_config)

        assert result == {}

    def test_get_ups_status_connection_error(self, mocker, sample_nut_config):
        """Test handling of connection errors"""
        mocker.patch('wolnut.monitor.PyNUTClient', side_effect=ConnectionError("Network unreachable"))

        result = get_ups_status(sample_nut_config)

        assert result == {}

    def test_get_ups_status_generic_exception(self, mocker, sample_nut_config):
        """Test handling of generic exceptions"""
        mock_client = MagicMock()
        mock_client.GetUPSVars.side_effect = Exception("Unexpected error")
        mocker.patch('wolnut.monitor.PyNUTClient', return_value=mock_client)

        result = get_ups_status(sample_nut_config)

        assert result == {}

    def test_get_ups_status_invalid_ups_name(self, mocker, sample_nut_config):
        """Test handling of invalid UPS name"""
        from wolnut.monitor import PyNUTError

        mock_client = MagicMock()
        mock_client.GetUPSVars.side_effect = PyNUTError("UNKNOWN-UPS")
        mocker.patch('wolnut.monitor.PyNUTClient', return_value=mock_client)

        result = get_ups_status(sample_nut_config)

        assert result == {}

    def test_get_ups_status_pynutclient_not_available(self, mocker, sample_nut_config):
        """Test handling when PyNUTClient is not installed"""
        # Simulate PyNUTClient not being available
        mocker.patch('wolnut.monitor.PyNUTClient', None)

        result = get_ups_status(sample_nut_config)

        assert result == {}

    def test_get_ups_status_empty_response(self, mocker, sample_nut_config):
        """Test handling of empty UPS variables response"""
        mock_client = MagicMock()
        mock_client.GetUPSVars.return_value = {}
        mocker.patch('wolnut.monitor.PyNUTClient', return_value=mock_client)

        result = get_ups_status(sample_nut_config)

        assert result == {}

    def test_get_ups_status_custom_port(self, mocker):
        """Test connection with custom port"""
        config = NutConfig(ups="myups", host="custom-host", port=9999)
        mock_client = MagicMock()
        mock_client.GetUPSVars.return_value = {b'ups.status': b'OL'}
        mock_pynut_class = mocker.patch('wolnut.monitor.PyNUTClient', return_value=mock_client)

        result = get_ups_status(config)

        mock_pynut_class.assert_called_once_with(
            host='custom-host',
            port=9999,
            login=None,
            password=None,
            timeout=5
        )
        assert result['ups.status'] == 'OL'

    def test_get_ups_status_custom_timeout(self, mocker):
        """Test connection with custom timeout"""
        config = NutConfig(ups="myups", timeout=10)
        mock_client = MagicMock()
        mock_client.GetUPSVars.return_value = {b'ups.status': b'OL'}
        mock_pynut_class = mocker.patch('wolnut.monitor.PyNUTClient', return_value=mock_client)

        result = get_ups_status(config)

        mock_pynut_class.assert_called_once_with(
            host='localhost',
            port=3493,
            login=None,
            password=None,
            timeout=10
        )
        assert result['ups.status'] == 'OL'


class TestIsClientOnline:
    """Tests for is_client_online function"""

    def test_is_client_online_success(self, mocker):
        """Test successful ping to online host"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mocker.patch('subprocess.run', return_value=mock_result)

        result = is_client_online("192.168.1.100")

        assert result is True

    def test_is_client_online_failure(self, mocker):
        """Test ping to offline host"""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mocker.patch('subprocess.run', return_value=mock_result)

        result = is_client_online("192.168.1.100")

        assert result is False

    def test_is_client_online_exception(self, mocker):
        """Test handling of exceptions during ping"""
        mocker.patch('subprocess.run', side_effect=Exception("Network error"))

        result = is_client_online("192.168.1.100")

        assert result is False

    @patch('wolnut.monitor.platform.system')
    def test_is_client_online_windows(self, mock_platform, mocker):
        """Test ping command on Windows"""
        mock_platform.return_value = "Windows"
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run = mocker.patch('subprocess.run', return_value=mock_result)

        result = is_client_online("192.168.1.100")

        assert result is True
        # Verify Windows flag (-n) is used
        args = mock_run.call_args[0][0]
        assert "-n" in args

    @patch('wolnut.monitor.platform.system')
    def test_is_client_online_linux(self, mock_platform, mocker):
        """Test ping command on Linux/Unix"""
        mock_platform.return_value = "Linux"
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run = mocker.patch('subprocess.run', return_value=mock_result)

        result = is_client_online("192.168.1.100")

        assert result is True
        # Verify Unix flag (-c) is used
        args = mock_run.call_args[0][0]
        assert "-c" in args
