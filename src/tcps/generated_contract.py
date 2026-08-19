"""Generated from ontology/tcps.ttl by ggen. Do not hand-edit."""
SYSTEM_NAME = "Toyota Code Production System 1979"
VERSION = "1979.1.1"
CYCLE = (
    "OBSERVE",
    "ADMIT",
    "MODEL",
    "SELECT",
    "AUTHORIZE",
    "PREPARE",
    "ACTUATE",
    "VERIFY",
    "RECEIPT",
    "REOBSERVE",
)
ROLES = {
    "EVE": "en",
    "WIZARD": "zh-CN",
    "TELCO": "ja-JP",
    "ROBOT": "ko-KR",
}
DFCM = {
    "maximize": tuple("value,urgency,evidence".split(",")),
    "minimize": tuple("risk,cost,cycle_time".split(",")),
    "max_frontier": int("64"),
    "selection": "deterministic-reversible",
    "irreversible_selections": int("0"),
    "planner_authority": "SELECT",
    "actuation": "NONE",
    "class_order": tuple("expedite,fixed_date,standard,debt".split(",")),
    "max_expedite_in_row": int("1"),
    "one_piece_pull": "true" == "true",
}
