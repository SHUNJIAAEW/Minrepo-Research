from dataclasses import dataclass, field, asdict
from typing import Any, Optional


@dataclass
class ToolResult:
    """
    Hermes ツール呼び出しの構造化結果。
    LLMエージェント・外部基盤・CLIのいずれから呼ばれても同じ形で返る。
    """
    ok: bool
    tool: str
    detail: str = ""
    data: dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class StepResult:
    name: str
    status: str           # success / partial / failed / skipped
    detail: str = ""
    duration_seconds: float = 0.0

    def to_dict(self) -> dict:
        return asdict(self)
