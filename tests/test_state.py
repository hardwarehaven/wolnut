from wolnut import state

# [ TODO ] - These tests aren't really checking much of anything, and should
#            just be thought of as a scaffold to write real tests.

def test__load_state(mocker):
  mock_path_exists = mocker.patch("state.os.path.exists")
  mock_path_exists.return_value = False

  s = state.ClientStateTracker([])
  mock_path_exists.assert_called_once()

def test__save_state(mocker):
  mock_file = mocker.patch("builtins.open")
  s = state.ClientStateTracker([])
  s._save_state()
  mock_file.assert_called_once()

def test_update(mocker):
  mock_file = mocker.patch("builtins.open")
  s = state.ClientStateTracker([])
  s.update('no such client', False)
  mock_file.assert_called_once()

def test_mark_wol_sent(mocker):
  mock_file = mocker.patch("builtins.open")
  s = state.ClientStateTracker([])
  s.mark_wol_sent('no such client')
  mock_file.assert_called_once()

def test_mark_skip(mocker):
  mock_file = mocker.patch("builtins.open")
  s = state.ClientStateTracker([])
  s.mark_skip('no such client')
  mock_file.assert_called_once()

def test_mark_all_online_clients(mocker):
  mock_file = mocker.patch("builtins.open")
  s = state.ClientStateTracker([])
  s.mark_all_online_clients()
  mock_file.assert_called_once()

def test_is_online():
  s = state.ClientStateTracker([])
  assert not s.is_online('no such client')

def test_was_online_before_shutdown():
  s = state.ClientStateTracker([])
  assert not s.was_online_before_shutdown('no such client')

def test_has_been_wol_sent():
  s = state.ClientStateTracker([])
  assert not s.has_been_wol_sent('no such client')

def test_should_attempt_wol():
  s = state.ClientStateTracker([])
  assert s.should_attempt_wol('no such client', 0)
  assert s.should_attempt_wol('no such client', 100000)
  assert s.should_attempt_wol('no such client', -5)

def test_should_skip():
  s = state.ClientStateTracker([])
  assert not s.should_skip('no such client')

def test_set_ups_on_battery(mocker):
  mock_file = mocker.patch("builtins.open")
  s = state.ClientStateTracker([])
  s.set_ups_on_battery(True, 9001)
  assert s._meta_state["ups_on_battery"]
  assert s._meta_state["battery_percent_at_shutdown"] > 9000   # this should _really_ test for equality (`==`) but, its_over_9000.jpeg
  mock_file.assert_called_once()

def test_was_ups_on_battery():
  s = state.ClientStateTracker([])
  assert not s._meta_state["ups_on_battery"]

def test_reset(mocker):
  mock_file = mocker.patch("builtins.open")
  s = state.ClientStateTracker([])
  s.reset()
  for client_state in s._client_states.values():
    for key in ["was_online_before_battery", "wol_sent", "skip"]:
      assert not client_state[key]
  mock_file.assert_called_once()
