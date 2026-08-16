from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from .canonical import digest_object
from .model import Refusal, TCPSRefused


@dataclass(frozen=True)
class Receipt:
    schema: str
    sequence: int
    previous: str | None
    subject: str
    authority: str
    intent: str
    consequence: dict[str, Any]
    verification: dict[str, Any]
    receipt_id: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "sequence": self.sequence,
            "previous": self.previous,
            "subject": self.subject,
            "authority": self.authority,
            "intent": self.intent,
            "consequence": self.consequence,
            "verification": self.verification,
            "receipt_id": self.receipt_id,
        }


def make_receipt(
    *,
    sequence: int,
    previous: str | None,
    subject: str,
    authority: str,
    intent: str,
    consequence: dict[str, Any],
    verification: dict[str, Any],
) -> Receipt:
    body = {
        "schema": "tcps.receipt.v1",
        "sequence": sequence,
        "previous": previous,
        "subject": subject,
        "authority": authority,
        "intent": intent,
        "consequence": consequence,
        "verification": verification,
    }
    receipt_id = digest_object(body)
    return Receipt(receipt_id=receipt_id, **body)


def verify_chain(receipts: Iterable[dict[str, Any]]) -> str | None:
    previous: str | None = None
    expected_sequence = 1
    for item in receipts:
        body = {key: value for key, value in item.items() if key != "receipt_id"}
        computed = digest_object(body)
        if item.get("receipt_id") != computed:
            raise TCPSRefused(
                Refusal(
                    "RECEIPT_DIGEST_MISMATCH",
                    str(item.get("receipt_id")),
                    "receipt identity must equal BLAKE3(canonical receipt body)",
                    item.get("receipt_id"),
                    computed,
                    "restore the original receipt or regenerate it from observed consequence",
                )
            )
        if item.get("sequence") != expected_sequence:
            raise TCPSRefused(
                Refusal(
                    "RECEIPT_SEQUENCE_GAP",
                    str(item.get("receipt_id")),
                    "receipt sequence is contiguous",
                    item.get("sequence"),
                    expected_sequence,
                    "restore missing receipts; never renumber history",
                )
            )
        if item.get("previous") != previous:
            raise TCPSRefused(
                Refusal(
                    "RECEIPT_PREDECESSOR_MISMATCH",
                    str(item.get("receipt_id")),
                    "receipt chain must bind the previous receipt identity",
                    item.get("previous"),
                    previous,
                    "restore the original predecessor edge",
                )
            )
        previous = computed
        expected_sequence += 1
    return previous
