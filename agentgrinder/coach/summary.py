"""Render exportable observations from measured fields, never model prose."""


def evidence_summary(numbers, *, activity_only=False):
    def count(key):
        value = numbers.get(key)
        return "unknown" if value is None else str(value)

    if activity_only:
        return (f"Recorded activity: {count('turns_typed')} human turns and "
                f"{count('tool_calls')} tool calls. Claim verification is unavailable "
                "for this adapter. These counts do not establish success or productivity.")
    return (f"{count('claims_verified')} of {count('claims')} claims had matching evidence "
            f"under the transcript checks. {count('turns_typed')} human turns; "
            f"{count('artifacts_produced')} recorded artifacts currently exist; "
            f"{count('commits')} commits counted by the adapter. "
            "File existence does not establish who produced a file. "
            "These counts do not establish success or productivity.")
