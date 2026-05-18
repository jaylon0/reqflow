"""Runtime registry for managing multiple runtime configs."""

import yaml
from pathlib import Path
from .runtime_config import RuntimeConfig, Capabilities, ToolMapping, ContextFormat, RuntimePaths


class RuntimeRegistry:
    def __init__(self, providers_dir: str = None):
        if providers_dir is None:
            providers_dir = str(Path(__file__).parent.parent / "runtime" / "providers")
        self.providers_dir = Path(providers_dir)
        self._configs: dict[str, RuntimeConfig] = {}
        self._load_all()

    def _load_all(self):
        for yaml_file in self.providers_dir.glob("*.yaml"):
            with open(yaml_file) as f:
                data = yaml.safe_load(f)
            config = self._from_dict(data)
            self._configs[config.name] = config

    def _from_dict(self, data: dict) -> RuntimeConfig:
        caps = Capabilities(**data.get("capabilities", {}))
        tools = ToolMapping(**data.get("tool_mapping", {}))
        fmt = ContextFormat(**data.get("context_format", {}))
        paths = RuntimePaths(**data.get("paths", {}))
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
