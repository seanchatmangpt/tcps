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
    pre_receipt: str
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
            "pre_receipt": self.pre_receipt,
            "consequence": self.consequence,
            "verification": self.verification,
            "receipt_id": self.receipt_id,
        }


def make_pre_receipt(
    *,
    sequence: int,
    previous: str | None,
    subject: str,
    authority: str,
    intent: str,
    plan_digest: str,
    root: str,
    operation: dict[str, Any],
    before: dict[str, Any],
    expected: dict[str, Any],
) -> dict[str, Any]:
    """Create the durable intent record that must exist before DO."""
    body = {
        "schema": "tcps.pre-receipt.v1",
        "sequence": sequence,
        "previous": previous,
        "subject": subject,
        "authority": authority,
        "intent": intent,
        "plan_digest": plan_digest,
        "root": root,
        "operation": operation,
        "before": before,
        "expected": expected,
    }
    return {**body, "pre_receipt_id": digest_object(body)}


def verify_pre_receipt(item: dict[str, Any]) -> str:
    if item.get("schema") != "tcps.pre-receipt.v1":
        raise TCPSRefused(
            Refusal(
                "PRE_RECEIPT_SCHEMA_UNSUPPORTED",
                str(item.get("schema")),
                "pending execution is represented by the admitted pre-receipt schema",
                item.get("schema"),
                "tcps.pre-receipt.v1",
                "restore or migrate the pending record",
            )
        )
    body = {key: value for key, value in item.items() if key != "pre_receipt_id"}
    computed = digest_object(body)
    if item.get("pre_receipt_id") != computed:
        raise TCPSRefused(
            Refusal(
                "PRE_RECEIPT_DIGEST_MISMATCH",
                str(item.get("pre_receipt_id")),
                "pre-receipt identity equals BLAKE3(canonical pre-receipt body)",
                item.get("pre_receipt_id"),
                computed,
                "restore the original pending record",
            )
        )
    return computed


def make_receipt(
    *,
    sequence: int,
    previous: str | None,
    subject: str,
    authority: str,
    intent: str,
    pre_receipt: str,
    consequence: dict[str, Any],
    verification: dict[str, Any],
) -> Receipt:
    """Close one prepared actuation with observed consequence evidence."""
    body = {
        "schema": "tcps.receipt.v1",
        "sequence": sequence,
        "previous": previous,
        "subject": subject,
        "authority": authority,
        "intent": intent,
        "pre_receipt": pre_receipt,
        "consequence": consequence,
        "verification": verification,
    }
    return Receipt(receipt_id=digest_object(body), **body)


def verify_chain(receipts: Iterable[dict[str, Any]]) -> str | None:
    previous: str | None = None
    expected_sequence = 1
    for item in receipts:
        if item.get("schema") != "tcps.receipt.v1":
            raise TCPSRefused(
                Refusal(
                    "RECEIPT_SCHEMA_UNSUPPORTED",
                    str(item.get("schema")),
                    "final receipts use the admitted receipt schema",
                    item.get("schema"),
                    "tcps.receipt.v1",
                    "restore or migrate the receipt",
                )
            )
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
                    "restore the original receipt",
                )
            )
        if item.get("sequence") != expected_sequence:
            raise TCPSRefused(
                Refusal(
                    "RECEIPT_SEQUENCE_GAP",
                    str(item.get("receipt_id")),
                    "receipt sequence is contiguous across all plans in one ledger",
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
                    "receipt chain binds the previous final receipt identity",
                    item.get("previous"),
                    previous,
                    "restore the original predecessor edge",
                )
            )
        if not isinstance(item.get("pre_receipt"), str):
            raise TCPSRefused(
                Refusal(
                    "PRE_RECEIPT_REFERENCE_MISSING",
                    str(item.get("receipt_id")),
                    "every final receipt closes one durable pre-receipt",
                    item.get("pre_receipt"),
                    "blake3:<digest>",
                    "restore the pre-receipt reference",
                )
            )
        previous = computed
        expected_sequence += 1
    return previous
