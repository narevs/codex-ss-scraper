import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from header_state import default_header_state


def test_default_header_state_is_empty():
    state = default_header_state()
    assert state.rule == ""
    assert state.site == ""
    assert state.page_type == ""
    assert state.n == 0
    assert state.address == ""
