from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List


@dataclass
class WorkspaceState:
    messages: List[Dict[str, Any]] = field(default_factory=list)
    current_workspace_state: Dict[str, Any] = field(default_factory=dict)
    error_logs: List[str] = field(default_factory=list)

    def add_message(self, role: str, content: str) -> None:
        self.messages.append({"role": role, "content": content})

    def add_error(self, message: str) -> None:
        self.error_logs.append(message)

    def snapshot(self, root_dir: str = "/projects") -> Dict[str, Any]:
        self.current_workspace_state = self._filesystem_snapshot(root_dir)
        return self.current_workspace_state

    def _filesystem_snapshot(self, root_dir: str) -> Dict[str, Any]:
        root = Path(root_dir)
        snapshot: Dict[str, Any] = {}
        if not root.exists():
            return snapshot

        for path in root.rglob("*"):
            try:
                if path.is_file():
                    snapshot[str(path.relative_to(root))] = {
                        "size": path.stat().st_size,
                        "mtime": path.stat().st_mtime,
                    }
            except OSError:
                snapshot[str(path)] = "error"
        return snapshot
