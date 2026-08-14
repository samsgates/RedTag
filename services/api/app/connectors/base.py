from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ConnectorResult:
    success: bool
    external_reference: str | None
    before: dict[str, Any] | None
    after: dict[str, Any] | None
    error: str | None = None


class Connector(ABC):
    name: str

    @abstractmethod
    def health(self) -> dict[str, Any]: ...

    @abstractmethod
    def execute(self, action: str, target_id: str, payload: dict[str, Any]) -> ConnectorResult: ...

    @abstractmethod
    def verify(self, action: str, target_id: str, expected: dict[str, Any]) -> dict[str, Any]: ...
