# tests/test_gui.py
import pytest
from PySide6.QtWidgets import QApplication

# Import the class we want to test
from smart_classifier.gui.main_window import MainWindow


# pytest fixture to create a QApplication instance, required for any Qt widget tests.
@pytest.fixture(scope="session")
def qapp():
    """Creates a QApplication instance for the test session."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_main_window_creation(qapp):
    """
    Test that the MainWindow can be created without crashing.
    This is a basic sanity check.
    """
    try:
        window = MainWindow()
        assert window is not None
        assert window.windowTitle() == " Smart File Classifier v3.0"
        # Check if a key widget was created
        assert hasattr(window, 'start_button')
        assert window.start_button.isEnabled() == True  # Should be enabled on start
    except Exception as e:
        pytest.fail(f"MainWindow creation failed with an exception: {e}")


def test_initial_button_states(qapp):
    """
    Test that the initial enabled/disabled state of buttons is correct.
    """
    window = MainWindow()

    # Should be enabled when IDLE
    assert window.start_button.isEnabled() == True
    assert window.dry_run_button.isEnabled() == True
    assert window.undo_button.isEnabled() == True

    # Should be disabled when IDLE
    assert window.pause_button.isEnabled() == False
    assert window.resume_button.isEnabled() == False
    assert window.cancel_button.isEnabled() == False