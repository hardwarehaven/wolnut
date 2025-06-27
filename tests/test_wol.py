def test_send_wol_packet(mocker):
  # [ TODO ] - Write tests that assert the appropriate exceptions were raised

  # Normally, you'd patch an object. The funky order here is so that
  # we can successfully patch a function. There's probably a better way to do this.
  mock_send_magic_packet = mocker.patch("wakeonlan.send_magic_packet")
  import wol

  # Intentionally using invalid values so an exception will be raised if the mock is wrong.
  wol.send_wol_packet('testing', broadcast_ip='555.555')
  mock_send_magic_packet.assert_called_once_with('testing', ip_address='555.555')
