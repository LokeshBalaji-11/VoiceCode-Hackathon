'''Minimal stub for pytest to allow test imports without the real package.'''

def fixture(_func=None, **_kwargs):
    """A no-op decorator mimicking pytest.fixture.

    It simply returns the original function unchanged, allowing test fixtures
    to be defined without requiring the actual pytest library.
    """
    def decorator(func):
        return func

    if _func is None:
        return decorator
    return _func


# --- Agent Auto-Patch ---
def fixture(_func=None, **kwargs):
    """Simple stub for pytest.fixture.

    Returns the original function unchanged. Accepts any keyword arguments
    to mimic the real decorator signature.
    """
    def decorator(func):
        return func
    if _func is None:
        return decorator
    return _func

# Expose the fixture name at module level
__all__ = ["fixture"]


# --- Agent Auto-Patch ---
def fixture(_func=None, **kwargs):
    """A minimal stub for pytest.fixture.

    It returns the original function unchanged, allowing test code that uses
    @pytest.fixture to work without the real pytest package.
    """
    if _func is None:
        def wrapper(func):
            return func
        return wrapper
    return _func
