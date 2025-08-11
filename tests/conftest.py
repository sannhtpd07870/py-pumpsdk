import logging
import pathlib
import pytest

@pytest.fixture(scope="session", autouse=True)
def configure_logging():
    """Cấu hình log cho pytest: vừa in console vừa lưu file."""
    logs_dir = pathlib.Path("logs")
    logs_dir.mkdir(exist_ok=True)

    log_file = logs_dir / "pytest_run.log"

    # Format log
    log_format = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    # Xóa handler cũ
    root_logger = logging.getLogger()
    for h in root_logger.handlers[:]:
        root_logger.removeHandler(h)

    # Handler console
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(log_format, datefmt=date_format))
    root_logger.addHandler(console_handler)

    # Handler file
    file_handler = logging.FileHandler(log_file, mode="w", encoding="utf-8")
    file_handler.setFormatter(logging.Formatter(log_format, datefmt=date_format))
    root_logger.addHandler(file_handler)

    root_logger.setLevel(logging.DEBUG)  # Ghi đầy đủ vào file
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)

    logging.info("=== Pytest session started ===")
    yield
    logging.info("=== Pytest session finished ===")
