"""Runtime registry for managing multiple runtime configs."""

import logging
import yaml
from dataclasses import fields as dataclass_fields
from pathlib import Path
from .runtime_config import RuntimeConfig, Capabilities, ToolMapping, ContextFormat, RuntimePaths

logger = logging.getLogger(__name__)


class RuntimeRegistry:
    def __init__(self, providers_dir: str = None):
        if providers_dir is None:
            providers_dir = str(Path(__file__).parent.parent / "runtime" / "providers")
        self.providers_dir = Path(providers_dir)
        self._configs: dict[str, RuntimeConfig] = {}
        self._errors: dict[str, str] = {}
        self._load_all()

    def _load_all(self):
        for yaml_file in self.providers_dir.glob("*.yaml"):
            try:
                with open(yaml_file) as f:
                    data = yaml.safe_load(f)
                if not data or not isinstance(data, dict):
                    continue
                config = self._from_dict(data)
                self._configs[config.name] = config
            except Exception as exc:
                name = yaml_file.stem
                self._errors[name] = str(exc)
                logger.warning("跳过不兼容的 runtime 配置 %s: %s", yaml_file.name, exc)

    def _from_dict(self, data: dict) -> RuntimeConfig:
        # Filter unknown fields to avoid TypeError
        cap_fields = {f.name for f in dataclass_fields(Capabilities)}
        caps = Capabilities(**{k: v for k, v in data.get("capabilities", {}).items() if k in cap_fields})

        tool_fields = {f.name for f in dataclass_fields(ToolMapping)}
        tools = ToolMapping(**{k: v for k, v in data.get("tool_mapping", {}).items() if k in tool_fields})

        fmt_fields = {f.name for f in dataclass_fields(ContextFormat)}
        fmt = ContextFormat(**{k: v for k, v in data.get("context_format", {}).items() if k in fmt_fields})

        path_fields = {f.name for f in dataclass_fields(RuntimePaths)}
        paths = RuntimePaths(**{k: v for k, v in data.get("paths", {}).items() if k in path_fields})

        return RuntimeConfig(
            name=data["name"],
            display_name=data["display_name"],
            capabilities=caps,
            tool_mapping=tools,
            context_format=fmt,
            paths=paths,
            api_key=data.get("api_key", ""),
            api_base=data.get("api_base", ""),
            model=data.get("model", ""),
            env_key=data.get("env_key", ""),
        )

    def get(self, name: str) -> RuntimeConfig:
        if name not in self._configs:
            raise ValueError(f"Unknown runtime: {name}. Available: {list(self._configs.keys())}")
        return self._configs[name]

    def list_runtimes(self) -> list[str]:
        return list(self._configs.keys())

    def list_errors(self) -> dict[str, str]:
        """Return configs that failed to load and why."""
        return dict(self._errors)

    def check_readiness(self, name: str) -> tuple[bool, str]:
        """Check if a runtime is ready to execute."""
        config = self.get(name)

        if config.name in ("manual", "host"):
            return True, ""

        if config.env_key:
            import os
            api_key = config.api_key or os.environ.get(config.env_key, "")
            if api_key:
                return True, ""
            return False, f"未配置 {config.display_name} API key (环境变量 {config.env_key})"

        if config.api_key:
            return True, ""

        if not config.env_key and not config.api_base:
            return True, ""

        return False, f"未配置 {config.display_name} 的 API 凭证"
