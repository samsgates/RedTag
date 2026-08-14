"""Google Cloud Model Armor integration.

The baseline regex detector remains useful for deterministic local tests. When Model Armor is enabled,
this adapter performs the cloud policy check and returns a normalized result to the security layer.
"""

import base64
from dataclasses import dataclass

from google.api_core.client_options import ClientOptions
from google.cloud import modelarmor_v1

from app.core.config import get_settings


@dataclass(frozen=True)
class ArmorResult:
    blocked: bool
    match_state: str
    invocation_result: str
    filters: tuple[str, ...]


class ModelArmorGuard:
    def __init__(self) -> None:
        self.settings = get_settings()
        location = self.settings.model_armor_location
        self.client = modelarmor_v1.ModelArmorClient(
            transport="rest",
            client_options=ClientOptions(api_endpoint=f"modelarmor.{location}.rep.googleapis.com"),
        )
        self.name = (
            f"projects/{self.settings.google_cloud_project}/locations/{location}/templates/"
            f"{self.settings.model_armor_template}"
        )

    @staticmethod
    def _normalize(response) -> ArmorResult:
        result = response.sanitization_result
        state = result.filter_match_state
        invocation = result.invocation_result
        blocked = state == modelarmor_v1.FilterMatchState.MATCH_FOUND
        state_name = getattr(state, "name", str(state))
        invocation_name = getattr(invocation, "name", str(invocation))
        return ArmorResult(
            blocked=blocked,
            match_state=state_name,
            invocation_result=invocation_name,
            filters=tuple(sorted(result.filter_results.keys())),
        )

    def inspect_text(self, text: str) -> ArmorResult:
        request = modelarmor_v1.SanitizeUserPromptRequest(
            name=self.name,
            user_prompt_data=modelarmor_v1.DataItem(text=text),
        )
        return self._normalize(self.client.sanitize_user_prompt(request=request))

    def inspect_bytes(self, content: bytes, byte_type: str) -> ArmorResult:
        try:
            item_type = getattr(modelarmor_v1.ByteDataItem.ByteItemType, byte_type)
        except AttributeError as exc:
            raise ValueError(f"Unsupported Model Armor byte type: {byte_type}") from exc
        request = modelarmor_v1.SanitizeUserPromptRequest(
            name=self.name,
            user_prompt_data=modelarmor_v1.DataItem(
                byte_item=modelarmor_v1.ByteDataItem(
                    byte_data_type=item_type,
                    byte_data=base64.b64encode(content),
                )
            ),
        )
        return self._normalize(self.client.sanitize_user_prompt(request=request))

    def inspect_pdf(self, content: bytes) -> ArmorResult:
        return self.inspect_bytes(content, "PDF")
