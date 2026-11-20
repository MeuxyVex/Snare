"""Data contracts for analysis artifacts."""

from typing import Annotated, Literal, Self

from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    JsonValue,
    model_validator,
)

RunMode = Literal["baseline", "cheat"]
NetworkMode = Literal["cut", "sim", "vpn"]
EventSource = Literal[
    "memory", "kernel", "process", "network", "analyst", "orchestrator"
]
Severity = Literal["info", "low", "medium", "high", "critical"]
NonEmptyStr = Annotated[str, Field(min_length=1)]
MonotonicTime = Annotated[int, Field(ge=0)]
DottedType = Annotated[str, Field(pattern=r"^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)+$")]
# Forward-slash paths with no absolute, drive, or parent directory segments.
EvidenceRef = Annotated[
    str,
    Field(pattern=r"^(timeline#[0-9]+|[^/\\:#.][^/\\:#]*(/[^/\\:#.][^/\\:#]*)*)$"),
]


class Artifact(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Run(Artifact):
    run_id: Annotated[
        str, Field(pattern=r"^[0-9]{8}-[0-9]{6}-(baseline|cheat)-[0-9a-f]{8}$")
    ]
    profile: NonEmptyStr
    mode: RunMode
    network: NetworkMode
    sample_sha256: Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")] | None = None
    started_at: AwareDatetime
    ended_at: AwareDatetime | None = None
    snare_version: NonEmptyStr
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_run(self) -> Self:
        if self.run_id.split("-")[2] != self.mode:
            raise ValueError("run_id must match the run mode")
        if self.ended_at is not None and self.ended_at < self.started_at:
            raise ValueError("ended_at must not be earlier than started_at")
        return self


class Event(Artifact):
    t_ns: MonotonicTime
    wall_time: AwareDatetime
    source: EventSource
    kind: NonEmptyStr
    data: dict[str, JsonValue]


class Finding(Artifact):
    id: NonEmptyStr
    type: DottedType
    severity: Severity
    target: dict[str, JsonValue]
    destination: dict[str, JsonValue] | None
    behaviour: NonEmptyStr | None
    first_seen: AwareDatetime
    evidence: list[EvidenceRef]
    source: NonEmptyStr
    confidence: Annotated[float, Field(ge=0, le=1)]


class Marker(Artifact):
    t_ns: MonotonicTime
    wall_time: AwareDatetime
    text: NonEmptyStr

    def to_event(self) -> Event:
        """Represent this marker in the unified timeline."""
        return Event(
            t_ns=self.t_ns,
            wall_time=self.wall_time,
            source="analyst",
            kind="marker",
            data={"text": self.text},
        )
