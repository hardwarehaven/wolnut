from wolnut import wol


def test_send_wol_packet(mocker):
    # [ TODO - Issue #24 ] - Write tests that assert the appropriate exceptions were raised

    # Patch send_magic_packet where it's used: in the wolnut.wol module.
    mock_send_magic_packet = mocker.patch("wolnut.wol.send_magic_packet")

    # Intentionally using invalid values so an exception will be raised if the mock is wrong.
    wol.send_wol_packet("testing", broadcast_ip="555.555")
    mock_send_magic_packet.assert_called_once_with("testing", ip_address="555.555")
