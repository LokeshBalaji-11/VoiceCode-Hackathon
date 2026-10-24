def fixture(_func=None, **kwargs):
    """Minimal stub for pytest.fixture decorator."""
    if _func is None:
        return lambda f: f
    return _func


# --- Agent Auto-Patch ---
def fixture(_func=None, **kwargs):
    """Simple stub for pytest.fixture decorator.
    It returns the original function unchanged, allowing test fixtures to work
    without the real pytest package.
    """
    if _func is None:
        # Used as @fixture()
        def wrapper(func):
            return func
        return wrapper
    # Used as @fixture
    return _func

__all__ = ["fixture"]
