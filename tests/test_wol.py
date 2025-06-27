def test_send_wol_packet(mocker):
  # [ TODO ] - Write tests that assert the appropriate exceptions were raised
  # Normally, you'd patch an object. The funky order here is so that
  # we can successfully patch a function.
  mock_send_magic_packet = mocker.patch("wakeonlan.send_magic_packet")
  from wolnut import wol

  wol.send_wol_packet('testing', broadcast_ip='555.555')
  mock_send_magic_packet.assert_called_once_with('testing', ip_address='555.555')
