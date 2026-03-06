"""
ChatGPT platform handler
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
            "display_name": "ChatGPT",
            "handler_class": "CodexHandler",
            "description": "OpenAI ChatGPT/Codex usage plan from local session logs",
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
                "执行 llm-balance plan --platform=chatgpt"
            ],
            "notes": [
                "数据来源为 ~/.codex/sessions 下最近会话日志",
                "读取 5h 与 weekly 两个限额窗口",
                "若日志中存在审查独立限额，会额外显示 review_session/review_weekly",
                "兼容平台别名 codex",
                "仅支持 plan，不支持 cost/package"
            ],
            "enabled": False
        }

    def __init__(self, config: PlatformConfig, browser: str = 'chrome'):
        super().__init__(browser)
        self.config = config

    def get_platform_name(self) -> str:
        return "ChatGPT"

    def get_balance(self) -> CostInfo:
        raise NotImplementedError("Codex balance check not implemented; only plan is supported.")

    def get_coding_plan(self) -> CodingPlanInfo:
        snapshot = self._load_latest_rate_limit_snapshot()
        main_rate_limits = snapshot.get("main_rate_limits", {})
        review_rate_limits = snapshot.get("review_rate_limits", {})
        has_review_activity = bool(snapshot.get("has_review_activity"))
        review_rate_limits_from_main = False
        if not review_rate_limits and has_review_activity and main_rate_limits:
            review_rate_limits = main_rate_limits
            review_rate_limits_from_main = True
        source_event = snapshot.get("source_event", {})
        quotas = []
        quotas.extend(self._build_standard_quotas(main_rate_limits, ""))
        quotas.extend(self._build_standard_quotas(review_rate_limits, "review_"))

        status = "Running" if quotas else "Stopped"
        update_time = self._format_event_time(source_event.get("timestamp"))

        return CodingPlanInfo(
            platform=self.get_platform_name(),
            status=status,
            quotas=quotas,
            update_time=update_time,
            raw_data={
                "source": "codex_session_log",
                "event": source_event,
                "main_rate_limits": main_rate_limits,
                "review_rate_limits": review_rate_limits,
                "has_review_activity": has_review_activity,
                "review_rate_limits_from_main": review_rate_limits_from_main
            }
        )

    def _build_standard_quotas(self, rate_limits: Dict[str, Any], level_prefix: str) -> List[CodingPlanQuota]:
        if not isinstance(rate_limits, dict):
            return []

        quotas = []
        if isinstance(rate_limits.get("primary"), dict) or isinstance(rate_limits.get("secondary"), dict):
            primary_quota = self._to_quota(f"{level_prefix}session", rate_limits.get("primary", {}))
            if primary_quota:
                quotas.append(primary_quota)

            secondary_quota = self._to_quota(f"{level_prefix}weekly", rate_limits.get("secondary", {}))
            if secondary_quota:
                quotas.append(secondary_quota)
            return quotas

        legacy_primary = self._to_legacy_quota(
            level=f"{level_prefix}session",
            percent_key="primary_used_percent",
            reset_key="primary_resets_at",
            source=rate_limits
        )
        if legacy_primary:
            quotas.append(legacy_primary)

        legacy_secondary = self._to_legacy_quota(
            level=f"{level_prefix}weekly",
            percent_key="secondary_used_percent",
            reset_key="secondary_resets_at",
            source=rate_limits
        )
        if legacy_secondary:
            quotas.append(legacy_secondary)
        return quotas

    def _to_quota(self, level: str, data: Dict[str, Any]) -> Optional[CodingPlanQuota]:
        if not isinstance(data, dict):
            return None
        if "used_percent" not in data and "resets_at" not in data:
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

    def _to_legacy_quota(self, level: str, percent_key: str, reset_key: str, source: Dict[str, Any]) -> Optional[CodingPlanQuota]:
        if not isinstance(source, dict):
            return None
        if percent_key not in source:
            return None

        used_percent = self._normalize_percent(source.get(percent_key, 0))
        reset_timestamp = int(source.get(reset_key, -1) or -1)
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

    def _load_latest_rate_limit_snapshot(self) -> Dict[str, Any]:
        session_files = self._resolve_session_files()
        if not session_files:
            raise ValueError("No Codex session file found. Run Codex CLI at least once.")

        latest_main_event = None
        latest_main_rate_limits = None
        latest_review_event = None
        latest_review_rate_limits = None
        latest_token_event = None
        latest_review_activity_event = None

        for session_file in session_files:
            in_review_mode = False
            file_main_event = None
            file_main_rate_limits = None
            file_review_event = None
            file_review_rate_limits = None
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
                        payload_type = payload.get("type")
                        if payload_type == "entered_review_mode":
                            in_review_mode = True
                            latest_review_activity_event = item
                            continue
                        if payload_type == "exited_review_mode":
                            in_review_mode = False
                            continue
                        if payload_type != "token_count":
                            continue

                        latest_token_event = item
                        if in_review_mode:
                            latest_review_activity_event = item
                        rate_limits = payload.get("rate_limits")
                        if not isinstance(rate_limits, dict):
                            continue
                        limit_id = str(rate_limits.get("limit_id") or "").strip().lower()
                        limit_name = str(rate_limits.get("limit_name") or "").strip().lower()
                        is_review_limit = (
                            "review" in limit_id or
                            "review" in limit_name or
                            in_review_mode
                        )

                        if is_review_limit:
                            file_review_event = item
                            file_review_rate_limits = rate_limits
                            continue

                        file_main_event = item
                        file_main_rate_limits = rate_limits
            except OSError:
                continue

            if latest_main_event is None and file_main_event is not None:
                latest_main_event = file_main_event
                latest_main_rate_limits = file_main_rate_limits

            if latest_review_event is None and file_review_event is not None:
                latest_review_event = file_review_event
                latest_review_rate_limits = file_review_rate_limits

            if latest_main_event and latest_review_event:
                break

        if not latest_main_event and not latest_token_event:
            raise ValueError("No codex token_count event found in local session files.")

        return {
            "source_event": latest_main_event or latest_token_event,
            "main_rate_limits": latest_main_rate_limits or {},
            "review_rate_limits": latest_review_rate_limits or {},
            "has_review_activity": latest_review_activity_event is not None
        }

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
