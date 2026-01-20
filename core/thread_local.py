import threading

_thread_locals = threading.local()


def set_current_db(db_name: str) -> None:
    _thread_locals.db_name = db_name


def get_current_db(default: str = 'insurance') -> str:
    return getattr(_thread_locals, 'db_name', default)


def clear_current_db() -> None:
    if hasattr(_thread_locals, 'db_name'):
        del _thread_locals.db_name


