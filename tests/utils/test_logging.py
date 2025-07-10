"""Test module for preservationeval.utils.logging."""

import logging
from pathlib import Path

import pytest

from preservationeval.utils.logging import (
    Environment,
    LogConfig,
    LogLevel,
    StructuredLogger,
    get_default_config,
    setup_logging,
)


@pytest.mark.unit
class TestEnvironmentEnum:
    """Tests for the Environment enum and related methods."""

    def test_environment_enum(self) -> None:
        """Test the string values of Environment enum members."""
        assert Environment.DEVELOPMENT.value == "development"
        assert Environment.PRODUCTION.value == "production"
        assert Environment.TEST.value == "test"
        assert Environment.INSTALL.value == "install"

    def test_environment_default(self) -> None:
        """Test the default environment value."""
        assert Environment.default() == Environment.DEVELOPMENT

    def test_environment_from_string(self) -> None:
        """Test conversion from string to Environment enum."""
        assert Environment.from_string("development") == Environment.DEVELOPMENT
        assert Environment.from_string("production") == Environment.PRODUCTION
        assert Environment.from_string("test") == Environment.TEST
        assert Environment.from_string("install") == Environment.INSTALL

    def test_environment_from_string_invalid(self) -> None:
        """Test handling of invalid environment string."""
        with pytest.raises(ValueError):
            Environment.from_string("invalid")

    def test_setup_logging_invalid_environment(self) -> None:
        """Test setup_logging with an invalid environment value."""
        with pytest.raises(ValueError, match=r"invalid_environment"):
            setup_logging(env="invalid_environment")


@pytest.mark.unit
class TestLogConfig:
    """Tests for the LogConfig class."""

    def test_log_config_defaults(self) -> None:
        """Test default values of LogConfig."""
        log_config = LogConfig()
        assert log_config.level == LogLevel.DEBUG
        assert (
            log_config.format
            == "%(asctime)s - %(levelname)s - %(name)s - %(funcName)s - %(message)s"
        )
        assert log_config.date_format == "%Y-%m-%d %H:%M:%S"
        assert log_config.console_output is True
        assert log_config.file_output is False
        assert log_config.log_dir is None
        assert log_config.file_name == "preservationeval.log"
        assert log_config.propagate is False
        assert log_config.capture_warnings is True

    def test_log_config_customization(self) -> None:
        """Test custom values of LogConfig."""
        log_config = LogConfig(
            level=LogLevel.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            date_format="%Y-%m-%d",
            console_output=False,
            file_output=True,
            log_dir=Path("/path/to/log/dir"),
            file_name="custom_log_file.log",
            propagate=True,
            capture_warnings=False,
        )
        assert log_config.level is LogLevel.INFO
        assert log_config.format == "%(asctime)s - %(levelname)s - %(message)s"
        assert log_config.date_format == "%Y-%m-%d"
        assert not log_config.console_output
        assert log_config.file_output
        assert log_config.log_dir == Path("/path/to/log/dir")
        assert log_config.file_name == "custom_log_file.log"
        assert log_config.propagate
        assert not log_config.capture_warnings


@pytest.mark.unit
class TestGetLogFilepath:
    """Test get_log_file_path() method of LogConfig."""

    def test_get_log_file_path_enabled(self) -> None:
        """Test get_log_file_path when file output is enabled."""
        log_config = LogConfig(file_output=True, log_dir=Path("/path/to/log/dir"))
        assert log_config.get_log_file_path() == Path(
            "/path/to/log/dir/preservationeval.log"
        )

    def test_get_log_file_path_disabled(self) -> None:
        """Test get_log_file_path when file output is disabled."""
        log_config = LogConfig(file_output=False)
        assert log_config.get_log_file_path() is None

    def test_get_log_file_path_custom_file_name(self) -> None:
        """Test get_log_file_path when a custom file name is used."""
        log_config = LogConfig(
            file_output=True,
            log_dir=Path("/path/to/log/dir"),
            file_name="custom_log_file.log",
        )
        assert log_config.get_log_file_path() == Path(
            "/path/to/log/dir/custom_log_file.log"
        )


@pytest.mark.unit
class TestStructuredLogger:
    """Tests for the StructuredLogger class."""

    def test_log_structured_valid_input(self) -> None:
        """Test logging with valid input."""
        logger = StructuredLogger("test_logger")
        logger._log_structured(logging.INFO, "Test message", {"key": "value"})

    def test_log_structured_extra_kwargs(self) -> None:
        """Test logging with extra kwargs."""
        logger = StructuredLogger("test_logger")
        logger._log_structured(
            logging.INFO, "Test message", {"key": "value"}, foo="bar"
        )

    def test_log_structured_with_valid_data(self) -> None:
        """Test logging with valid data."""
        logger = StructuredLogger("test_logger")
        logger._log_structured(logging.INFO, "Test message", {"temp": 20, "rh": 50})


@pytest.mark.unit
def test_get_default_config_development() -> None:
    default_config = get_default_config(Environment.DEVELOPMENT)
    assert isinstance(default_config, LogConfig)


@pytest.mark.unit
def test_get_default_config_none() -> None:
    default_config = get_default_config(None)
    assert isinstance(default_config, LogConfig)


@pytest.mark.unit
def test_get_default_config_production() -> None:
    default_config = get_default_config(Environment.PRODUCTION)
    assert isinstance(default_config, LogConfig)
