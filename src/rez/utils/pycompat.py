__all__ = ['read_text', 'read_binary']


try:
    from importlib.resources import read_text, read_binary
except ImportError:
    from rez.vendor.importlib_resources import read_text, read_binary
