"""Tests for ApiGatekeeper and RateLimitConfig."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import anthropic
import pytest

from src.agents.gatekeeper import ApiGatekeeper, RateLimitConfig

_CONFIG_PATH = Path(__file__).parents[1] / "config" / "rate_limits.json"


class TestRateLimitConfig:
    def test_loads_from_real_config(self):
        cfg = RateLimitConfig(_CONFIG_PATH)
        assert cfg.requests_per_minute > 0
        assert cfg.retry_after_seconds > 0
        assert cfg.max_retries > 0
        assert cfg.concurrent_max > 0

    def test_loads_anthropic_service(self):
        cfg = RateLimitConfig(_CONFIG_PATH)
        assert cfg.max_retries == 3
        assert cfg.retry_after_seconds == 30

    def test_invalid_path_raises(self):
        with pytest.raises(FileNotFoundError):
            RateLimitConfig("/nonexistent/rate_limits.json")


class TestApiGatekeeper:
    def _gatekeeper(self) -> ApiGatekeeper:
        cfg = RateLimitConfig(_CONFIG_PATH)
        return ApiGatekeeper(cfg)

    def test_execute_success_returns_result(self):
        gk = self._gatekeeper()
        api_call = MagicMock(return_value="ok")
        result = gk.execute(api_call, "arg1", key="val")
        assert result == "ok"
        api_call.assert_called_once_with("arg1", key="val")

    def test_queue_status_reflects_calls(self):
        gk = self._gatekeeper()
        api_call = MagicMock(return_value="ok")
        gk.execute(api_call)
        gk.execute(api_call)
        status = gk.get_queue_status()
        assert status["total_calls"] == 2
        assert status["successes"] == 2
        assert status["failures"] == 0

    def test_rate_limit_error_retries_then_returns_none(self):
        gk = self._gatekeeper()
        error = anthropic.RateLimitError.__new__(anthropic.RateLimitError)
        api_call = MagicMock(side_effect=error)
        with patch("time.sleep"):
            result = gk.execute(api_call)
        assert result is None
        assert gk.get_queue_status()["failures"] == gk.config.max_retries

    def test_api_status_500_retries(self):
        gk = self._gatekeeper()
        ok_response = MagicMock()
        exc = anthropic.APIStatusError.__new__(anthropic.APIStatusError)
        exc.status_code = 500
        api_call = MagicMock(side_effect=[exc, ok_response])
        with patch("time.sleep"):
            result = gk.execute(api_call)
        assert result is ok_response

    def test_api_status_400_raises_immediately(self):
        gk = self._gatekeeper()
        exc = anthropic.APIStatusError.__new__(anthropic.APIStatusError)
        exc.status_code = 400
        exc.message = "Bad request"
        exc.response = MagicMock()
        exc.body = {}
        api_call = MagicMock(side_effect=exc)
        with pytest.raises(anthropic.APIStatusError):
            gk.execute(api_call)

    def test_default_config_loaded_when_none(self):
        gk = ApiGatekeeper()
        assert gk.config.max_retries == 3

    def test_recent_log_capped_at_ten(self):
        gk = self._gatekeeper()
        api_call = MagicMock(return_value="x")
        for _ in range(15):
            gk.execute(api_call)
        assert len(gk.get_queue_status()["recent_log"]) == 10
