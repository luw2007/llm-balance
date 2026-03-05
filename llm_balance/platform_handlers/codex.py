"""
Codex platform handler
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from .base import BasePlatformHandler, CostInfo, CodingPlanInfo, CodingPlanQuota
from ..config import PlatformConfig


class CodexHandler(BasePlatformHandler):
    @classmethod
    def get_default_config(cls) -> dict:
        return {
            "display_name": "Codex",
            "handler_class": "CodexHandler",
            "description": "OpenAI Codex usage plan from local session logs",
            "api_url": "",
            "method": "GET",
            "auth_type": "local_file",
            "env_var": None,
            "headers": {},
            "params": {},
            "data": {},
            "setup_steps": [
                "安装并登录 Codex CLI",
                "运行一次 codex 会话以生成本地日志",
                "执行 llm-balance plan --platform=codex"
            ],
            "notes": [
                "数据来源为 ~/.codex/sessions 下最近会话日志",
                "读取 5h 与 weekly 两个限额窗口",
                "仅支持 plan，不支持 cost/package"
            ],
            "enabled": False
        }

    def __init__(self, config: PlatformConfig, browser: str = 'chrome'):
        super().__init__(browser)
        self.config = config

    def get_platform_name(self) -> str:
        return "Codex"

    def get_balance(self) -> CostInfo:
        raise NotImplementedError("Codex balance check not implemented; only plan is supported.")

    def get_coding_plan(self) -> CodingPlanInfo:
        event = self._load_latest_token_event()
        payload = event.get("payload", {})
        if not isinstance(payload, dict):
            payload = {}
        rate_limits = payload.get("rate_limits")
        if not isinstance(rate_limits, dict):
            rate_limits = {}
        quotas = []

        primary = rate_limits.get("primary", {})
        secondary = rate_limits.get("secondary", {})

        primary_quota = self._to_quota("session", primary)
        if primary_quota:
            quotas.append(primary_quota)

        secondary_quota = self._to_quota("weekly", secondary)
        if secondary_quota:
            quotas.append(secondary_quota)

        status = "Running" if quotas else "Stopped"
        update_time = self._format_event_time(event.get("timestamp"))

        return CodingPlanInfo(
            platform=self.get_platform_name(),
            status=status,
            quotas=quotas,
            update_time=update_time,
            raw_data={
                "source": "codex_session_log",
                "event": event
            }
        )

    def _to_quota(self, level: str, data: Dict[str, Any]) -> Optional[CodingPlanQuota]:
        if not isinstance(data, dict):
            return None

        used_percent = self._normalize_percent(data.get("used_percent", 0))
        reset_timestamp = int(data.get("resets_at", -1) or -1)
        reset_time = None
        if reset_timestamp > 0:
            reset_time = datetime.fromtimestamp(reset_timestamp).strftime('%Y-%m-%d %H:%M:%S')

        return CodingPlanQuota(
            level=level,
            percent=used_percent,
            reset_timestamp=reset_timestamp,
            reset_time=reset_time
        )

    def _normalize_percent(self, value: Any) -> float:
        try:
            number = float(value)
        except (ValueError, TypeError):
            return 0.0
        return max(0.0, min(100.0, number))


    def _format_event_time(self, value: Optional[str]) -> Optional[str]:
        if not value:
            return None
        try:
            dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
            return dt.astimezone().strftime('%Y-%m-%d %H:%M:%S')
        except Exception:
            return None

    def _load_latest_token_event(self) -> Dict[str, Any]:
        session_files = self._resolve_session_files()
        if not session_files:
            raise ValueError("No Codex session file found. Run Codex CLI at least once.")

        for session_file in session_files:
            latest_event = None
            try:
                with session_file.open('r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            item = json.loads(line)
                        except json.JSONDecodeError:
                            continue

                        if item.get("type") != "event_msg":
                            continue
                        payload = item.get("payload", {})
                        if not isinstance(payload, dict):
                            continue
                        if payload.get("type") != "token_count":
                            continue
                        rate_limits = payload.get("rate_limits")
                        if not isinstance(rate_limits, dict):
                            continue
                        if rate_limits.get("limit_id") != "codex":
                            continue
                        latest_event = item
            except OSError:
                continue

            if latest_event:
                return latest_event

        raise ValueError("No codex token_count event found in local session files.")

    def _resolve_session_files(self) -> Optional[List[Path]]:
        env_path = os.getenv("CODEX_SESSION_FILE")
        if env_path:
            path = Path(env_path).expanduser()
            if path.exists() and path.is_file():
                return [path]

        sessions_dir = Path.home() / ".codex" / "sessions"
        if not sessions_dir.exists():
            return None

        candidates = list(sessions_dir.rglob("rollout-*.jsonl"))
        if not candidates:
            return None

        return sorted(candidates, key=lambda p: p.stat().st_mtime, reverse=True)
