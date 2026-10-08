from datetime import datetime
from typing import Literal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, AwareDatetime, model_validator

class Strict(BaseModel):
    model_config = ConfigDict(extra='forbid')

class Credentials(Strict):
    email: str = Field(min_length=3, max_length=254, pattern=r'^[^\s@]+@[^\s@]+\.[^\s@]+$')
    password: str = Field(min_length=12, max_length=128)

class PairRequest(Strict):
    installation_id: UUID
    profile_id: str = Field(min_length=1, max_length=64, pattern=r'^[a-zA-Z0-9_-]+$')
    profile_label: str = Field(min_length=1, max_length=80)

class Code(Strict):
    code: str = Field(pattern=r'^[A-Z2-9]{4}-[A-Z2-9]{4}$')

class Approval(Code):
    pairing_id: UUID
    physical_possession: Literal[True]

class Poll(Strict):
    device_code: str = Field(min_length=32, max_length=128)

class Trophy(Strict):
    title_id: str = Field(min_length=1, max_length=64)
    title: str = Field(min_length=1, max_length=200)
    trophy_id: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=200)
    grade: Literal['bronze', 'silver', 'gold', 'platinum', 'unknown']
    unlocked: bool
    unlocked_at: AwareDatetime | None = None

    @model_validator(mode='after')
    def timestamp(self):
        if not self.unlocked and self.unlocked_at is not None:
            raise ValueError('A locked trophy cannot have an unlock timestamp')
        return self

class Activity(Strict):
    event_id: str = Field(min_length=1, max_length=100)
    title_id: str = Field(min_length=1, max_length=64)
    title: str = Field(min_length=1, max_length=200)
    started_at: AwareDatetime | None = None
    ended_at: AwareDatetime | None = None
    duration_seconds: int | None = Field(default=None, ge=0, le=604800)
    complete: bool
    clock: Literal['trusted', 'uncertain', 'unknown']

    @model_validator(mode='after')
    def interval(self):
        if self.started_at and self.ended_at and self.ended_at < self.started_at:
            raise ValueError('Session end precedes start')
        if not self.complete and self.duration_seconds is not None:
            raise ValueError('Incomplete sessions must retain unknown duration')
        return self

class Snapshot(Strict):
    schema_version: Literal[1]
    batch_id: UUID
    source: Literal['ps5_native', 'ps4_bc']
    mock: bool
    trophies: list[Trophy] = Field(default_factory=list, max_length=2000)
    activities: list[Activity] = Field(default_factory=list, max_length=2000)

    @model_validator(mode='after')
    def unique_keys(self):
        tk = [(t.title_id, t.trophy_id) for t in self.trophies]
        ak = [a.event_id for a in self.activities]
        if len(tk) != len(set(tk)) or len(ak) != len(set(ak)):
            raise ValueError('Duplicate source identities in snapshot')
        return self

class NativeObservation(Strict):
    raw_flags: int = Field(ge=0, le=4294967295)
    # Preserve both native year-1 microsecond fields as strings, including zero.
    first_raw: str = Field(pattern=r'^(0|[1-9][0-9]{0,19})$')
    second_raw: str = Field(pattern=r'^(0|[1-9][0-9]{0,19})$')

    @model_validator(mode='after')
    def bounded(self):
        if max(int(self.first_raw), int(self.second_raw)) > 18446744073709551615:
            raise ValueError('Native timestamp exceeds uint64')
        return self

class NativeTrophy(Trophy):
    unlocked: bool | None
    clock: Literal['uncertain', 'unknown']
    native_observation: NativeObservation

    @model_validator(mode='after')
    def observation(self):
        o = self.native_observation
        if self.unlocked is True:
            if o.raw_flags != 17 or not int(o.first_raw) or not int(o.second_raw):
                raise ValueError('Unsupported native earned evidence')
        elif self.unlocked is False:
            if o.raw_flags != 0 or int(o.first_raw) or int(o.second_raw):
                raise ValueError('Unsupported native locked evidence')
        if self.unlocked_at is not None and self.clock != 'uncertain':
            raise ValueError('Native candidate timestamps require uncertain clock')
        return self

class NativeSnapshot(Snapshot):
    schema_version: Literal[2]
    source: Literal['ps5_native']
    trophies: list[NativeTrophy] = Field(default_factory=list, max_length=2000)
    activities: list[Activity] = Field(default_factory=list, max_length=0)
    consistency: Literal['stable_read_not_atomic']
    profile_binding: Literal['foreground_user_path_scoped']

class NativeActivityObservation(Strict):
    application_title_id: str = Field(pattern=r'^PPSA[0-9]{5}$')
    session_digest: str = Field(pattern=r'^[0-9a-f]{64}$')
    # A native foreground counter is independent of wall-clock timestamps.
    foreground_seconds: int | None = Field(default=None, ge=0, le=604800)
    event: Literal['ApplicationSessionEnd', 'ApplicationSessionStart', 'ApplicationSessionCrash']

class NativeActivity(Activity):
    event_id: str = Field(pattern=r'^native-session:[0-9a-f]{64}$')
    duration_basis: Literal['native_foreground_seconds']
    clock: Literal['uncertain', 'unknown']
    native_observation: NativeActivityObservation

    @model_validator(mode='after')
    def native_duration(self):
        observation=self.native_observation
        if self.event_id!='native-session:'+observation.session_digest:
            raise ValueError('Native session identity mismatch')
        if self.title_id!=observation.application_title_id:
            raise ValueError('Native application identity mismatch')
        if self.complete:
            if observation.event!='ApplicationSessionEnd' or self.duration_seconds is None or self.duration_seconds!=observation.foreground_seconds:
                raise ValueError('Complete duration requires matching native end evidence')
        elif observation.foreground_seconds is not None:
            raise ValueError('Incomplete native activity has unknown duration')
        return self

class NativeActivitySnapshot(Snapshot):
    schema_version: Literal[3]
    source: Literal['ps5_native']
    mock: Literal[False]
    trophies: list[Trophy] = Field(default_factory=list,max_length=0)
    activities: list[NativeActivity] = Field(default_factory=list,max_length=128)
    consistency: Literal['sqlite_read_transaction']
    profile_binding: Literal['activity_header_single_local_user']
