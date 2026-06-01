from __future__ import annotations

import math
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional


STATE_ORDER = ("T1", "T2", "A1", "A2", "B1", "B2")
TIME_PERIODS = ("morning", "afternoon_evening", "night")

TIME_OF_DAY_RAAGA_MAP: Dict[str, Dict[str, str]] = {
    "morning": {
        "T1": "Ahir Bhairav",
        "T2": "Todi",
        "A1": "Bhairav",
        "A2": "Alhaiya Bilawal",
        "B1": "Jaunpuri",
        "B2": "Hindol",
    },
    "afternoon_evening": {
        "T1": "Madhmad Sarang",
        "T2": "Bhimpalasi",
        "A1": "Shuddh Sarang",
        "A2": "Multani",
        "B1": "Kafi",
        "B2": "Marwa",
    },
    "night": {
        "T1": "Malkauns",
        "T2": "Darbari Kanada",
        "A1": "Yaman",
        "A2": "Bhopali",
        "B1": "Khamaj",
        "B2": "Shankara",
    },
}

STATE_DESCRIPTIONS: Dict[str, str] = {
    "T1": "Deep Meditation / Sleep Border",
    "T2": "Hypnagogic / Creative Drift",
    "A1": "Deep Relaxation / Calm",
    "A2": "Mindful Alertness",
    "B1": "Cognitive Focus / Work Mode",
    "B2": "High Alertness / Stress Peak",
}

STATE_GROUPS: Dict[str, str] = {
    "T1": "sleep",
    "T2": "sleep",
    "A1": "relaxed",
    "A2": "relaxed",
    "B1": "focused",
    "B2": "focused",
}


@dataclass(frozen=True)
class CognitiveState:
    code: str
    label: str

    def to_dict(self) -> Dict[str, str]:
        return {"code": self.code, "label": self.label}


COGNITIVE_STATES: Dict[str, CognitiveState] = {
    code: CognitiveState(code=code, label=STATE_DESCRIPTIONS[code]) for code in STATE_ORDER
}


@dataclass
class PlaylistEntry:
    index: int
    state: str
    raaga: str
    file_name: str
    file_path: str
    start_time: int
    end_time: int
    duration_seconds: int

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SessionPlan:
    source_state: str
    target_state: str
    time_period: str
    session_duration_seconds: int
    crossfade_seconds: int
    playlist: List[PlaylistEntry]
    generated_at: str
    playlist_version: int = 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_state": self.source_state,
            "target_state": self.target_state,
            "time_period": self.time_period,
            "session_duration_seconds": self.session_duration_seconds,
            "crossfade_seconds": self.crossfade_seconds,
            "generated_at": self.generated_at,
            "playlist_version": self.playlist_version,
            "playlist": [entry.to_dict() for entry in self.playlist],
        }


@dataclass
class StabilityState:
    accepted_state: Optional[str] = None
    accepted_since: Optional[datetime] = None
    pending_state: Optional[str] = None
    pending_since: Optional[datetime] = None


@dataclass
class ActiveTherapySession:
    target_state: str
    session_duration_seconds: int
    started_at: datetime
    current_source_state: str
    plan: SessionPlan
    last_transition_at: datetime
    playlist_version: int = 1
    status: Literal["idle", "ready", "active", "completed", "blocked"] = "ready"
    headset_message: str = ""


class AudioFileResolver:
    def __init__(self, audio_root: Optional[Path] = None) -> None:
        default_root = Path(__file__).resolve().parents[3] / "frontend" / "public" / "audio"
        self.audio_root = audio_root or default_root
        self._index = self._build_index()

    @staticmethod
    def normalize_raaga_name(name: str) -> str:
        safe = re.sub(r"[^A-Za-z0-9]+", "_", name.strip())
        return re.sub(r"_+", "_", safe).strip("_")

    @staticmethod
    def _search_key(value: str) -> str:
        return re.sub(r"[^a-z0-9]+", "", value.lower())

    def _build_index(self) -> Dict[str, str]:
        index: Dict[str, str] = {}
        if not self.audio_root.exists():
            return index
        for file_path in self.audio_root.glob("*.mp3"):
            index[self._search_key(file_path.stem)] = file_path.name
        return index

    def resolve(self, raaga: str) -> tuple[str, str]:
        canonical = f"{self.normalize_raaga_name(raaga)}.mp3"
        found = self._index.get(self._search_key(raaga), canonical)
        return found, f"/audio/{found}"


class RaagaTransitionEngine:
    def __init__(
        self,
        *,
        audio_root: Optional[Path] = None,
        stability_seconds: int = 30,
        default_crossfade_seconds: int = 12,
    ) -> None:
        self.audio_resolver = AudioFileResolver(audio_root)
        self.stability_seconds = stability_seconds
        self.default_crossfade_seconds = default_crossfade_seconds
        self.stability = StabilityState()
        self.session: Optional[ActiveTherapySession] = None

    def determine_time_period(self, now: Optional[datetime] = None) -> str:
        current = now or datetime.now()
        hour = current.hour
        if 6 <= hour < 12:
            return "morning"
        if 12 <= hour < 18:
            return "afternoon_evening"
        return "night"

    def resolve_state_path(self, source_state: str, target_state: str) -> List[str]:
        source_idx = STATE_ORDER.index(source_state)
        target_idx = STATE_ORDER.index(target_state)
        step = 1 if target_idx >= source_idx else -1
        return [STATE_ORDER[idx] for idx in range(source_idx, target_idx + step, step)]

    def raaga_for_state(self, state: str, time_period: str) -> str:
        return TIME_OF_DAY_RAAGA_MAP[time_period][state]

    def build_playlist(
        self,
        source_state: str,
        target_state: str,
        session_duration_seconds: int,
        *,
        now: Optional[datetime] = None,
        playlist_version: int = 1,
    ) -> SessionPlan:
        time_period = self.determine_time_period(now)
        state_path = self.resolve_state_path(source_state, target_state)
        per_track_duration = max(1, session_duration_seconds // len(state_path))
        remainder = max(0, session_duration_seconds - (per_track_duration * len(state_path)))

        playlist: List[PlaylistEntry] = []
        cursor = 0
        for index, state in enumerate(state_path):
            bonus = 1 if index < remainder else 0
            duration_seconds = per_track_duration + bonus
            raaga = self.raaga_for_state(state, time_period)
            file_name, file_path = self.audio_resolver.resolve(raaga)
            entry = PlaylistEntry(
                index=index,
                state=state,
                raaga=raaga,
                file_name=file_name,
                file_path=file_path,
                start_time=cursor,
                end_time=cursor + duration_seconds,
                duration_seconds=duration_seconds,
            )
            playlist.append(entry)
            cursor += duration_seconds

        return SessionPlan(
            source_state=source_state,
            target_state=target_state,
            time_period=time_period,
            session_duration_seconds=session_duration_seconds,
            crossfade_seconds=min(self.default_crossfade_seconds, max(3, per_track_duration // 4)),
            playlist=playlist,
            generated_at=(now or datetime.utcnow()).isoformat(),
            playlist_version=playlist_version,
        )

    def start_session(
        self,
        *,
        current_state: str,
        target_state: str,
        duration_minutes: int,
        headset_ready: bool,
        now: Optional[datetime] = None,
    ) -> SessionPlan:
        if not headset_ready:
            raise ValueError("Adjust Headband Position")

        started_at = now or datetime.utcnow()
        session_duration_seconds = duration_minutes * 60
        plan = self.build_playlist(
            current_state,
            target_state,
            session_duration_seconds,
            now=started_at,
            playlist_version=1,
        )
        self.session = ActiveTherapySession(
            target_state=target_state,
            session_duration_seconds=session_duration_seconds,
            started_at=started_at,
            current_source_state=current_state,
            plan=plan,
            last_transition_at=started_at,
            playlist_version=1,
            status="active",
        )
        return plan

    def stop_session(self) -> None:
        self.session = None

    def update_stability(self, detected_state: str, *, observed_at: Optional[datetime] = None) -> Dict[str, Any]:
        now = observed_at or datetime.utcnow()
        stable = self.stability

        if stable.accepted_state is None:
            stable.accepted_state = detected_state
            stable.accepted_since = now
            stable.pending_state = None
            stable.pending_since = None
            return {
                "accepted": True,
                "state_changed": True,
                "accepted_state": detected_state,
                "pending_state": None,
                "stable_for_seconds": 0,
            }

        if detected_state == stable.accepted_state:
            stable.pending_state = None
            stable.pending_since = None
            stable_for = int((now - (stable.accepted_since or now)).total_seconds())
            return {
                "accepted": False,
                "state_changed": False,
                "accepted_state": stable.accepted_state,
                "pending_state": None,
                "stable_for_seconds": stable_for,
            }

        if stable.pending_state != detected_state:
            stable.pending_state = detected_state
            stable.pending_since = now
            return {
                "accepted": False,
                "state_changed": False,
                "accepted_state": stable.accepted_state,
                "pending_state": detected_state,
                "stable_for_seconds": 0,
            }

        stable_for = int((now - (stable.pending_since or now)).total_seconds())
        if stable_for < self.stability_seconds:
            return {
                "accepted": False,
                "state_changed": False,
                "accepted_state": stable.accepted_state,
                "pending_state": detected_state,
                "stable_for_seconds": stable_for,
            }

        stable.accepted_state = detected_state
        stable.accepted_since = now
        stable.pending_state = None
        stable.pending_since = None
        return {
            "accepted": True,
            "state_changed": True,
            "accepted_state": detected_state,
            "pending_state": None,
            "stable_for_seconds": stable_for,
        }

    def derive_state(
        self,
        *,
        alpha: Optional[float] = None,
        beta: Optional[float] = None,
        theta: Optional[float] = None,
        focus: Optional[float] = None,
        relaxation: Optional[float] = None,
        fatigue: Optional[float] = None,
        stress: Optional[float] = None,
        classifier_state: Optional[str] = None,
    ) -> str:
        def norm(value: Optional[float]) -> float:
            if value is None:
                return 0.0
            value = float(value)
            return max(0.0, min(1.0, value / 100.0 if value > 1 else value))

        alpha_value = max(0.0, float(alpha or 0.0))
        beta_value = max(0.0, float(beta or 0.0))
        theta_value = max(0.0, float(theta or 0.0))
        total = alpha_value + beta_value + theta_value

        focus_score = norm(focus)
        relaxation_score = norm(relaxation)
        fatigue_score = norm(fatigue)
        stress_score = norm(stress)

        theta_share = theta_value / total if total else 0.0
        alpha_share = alpha_value / total if total else 0.0
        beta_share = beta_value / total if total else 0.0

        classifier = (classifier_state or "").lower()

        if theta_share >= max(alpha_share, beta_share) or classifier in {"sleep", "sleepy", "fatigued"}:
            if fatigue_score >= 0.6 or theta_share >= 0.45:
                return "T1"
            return "T2"

        if beta_share >= max(alpha_share, theta_share) or classifier in {"focused"}:
            if stress_score >= 0.55 or beta_share >= 0.5:
                return "B2"
            return "B1"

        mindful_alertness = max(focus_score, 0.35 + (alpha_share * 0.5))
        if relaxation_score >= mindful_alertness and relaxation_score >= 0.55:
            return "A1"
        return "A2"

    def _current_track(self, plan: SessionPlan, elapsed_seconds: int) -> tuple[Optional[PlaylistEntry], Optional[PlaylistEntry], int]:
        if not plan.playlist:
            return None, None, 0
        for index, track in enumerate(plan.playlist):
            if elapsed_seconds < track.end_time:
                upcoming = plan.playlist[index + 1] if index + 1 < len(plan.playlist) else None
                return track, upcoming, index
        return plan.playlist[-1], None, len(plan.playlist) - 1

    def therapy_snapshot(self, *, headset_ready: bool, now: Optional[datetime] = None) -> Dict[str, Any]:
        current_time = now or datetime.utcnow()
        accepted_state = self.stability.accepted_state
        pending_state = self.stability.pending_state
        pending_seconds = 0
        if self.stability.pending_since and pending_state:
            pending_seconds = int((current_time - self.stability.pending_since).total_seconds())

        base = {
            "therapy_active": bool(self.session and self.session.status == "active"),
            "headset_ready": headset_ready,
            "headset_message": "" if headset_ready else "Adjust Headband Position",
            "current_eeg_state": accepted_state,
            "current_eeg_state_label": STATE_DESCRIPTIONS.get(accepted_state or "", ""),
            "pending_eeg_state": pending_state,
            "pending_eeg_state_label": STATE_DESCRIPTIONS.get(pending_state or "", ""),
            "pending_state_stable_for_seconds": pending_seconds,
            "stability_required_seconds": self.stability_seconds,
        }

        if not self.session:
            base.update(
                {
                    "target_eeg_state": None,
                    "target_eeg_state_label": None,
                    "playlist_version": 0,
                    "time_period": self.determine_time_period(current_time),
                    "playlist": [],
                    "current_track": None,
                    "upcoming_track": None,
                    "current_raaga": None,
                    "upcoming_raaga": None,
                    "session_progress_percent": 0,
                    "crossfade_seconds": self.default_crossfade_seconds,
                }
            )
            return base

        elapsed = max(0, int((current_time - self.session.started_at).total_seconds()))
        if elapsed >= self.session.session_duration_seconds:
            self.session.status = "completed"
            elapsed = self.session.session_duration_seconds

        current_track, upcoming_track, current_index = self._current_track(self.session.plan, elapsed)
        progress = 0 if self.session.session_duration_seconds <= 0 else min(
            100,
            round((elapsed / self.session.session_duration_seconds) * 100, 2),
        )

        base.update(
            {
                "therapy_active": self.session.status == "active",
                "target_eeg_state": self.session.target_state,
                "target_eeg_state_label": STATE_DESCRIPTIONS[self.session.target_state],
                "playlist_version": self.session.playlist_version,
                "time_period": self.session.plan.time_period,
                "playlist": [entry.to_dict() for entry in self.session.plan.playlist],
                "current_track": current_track.to_dict() if current_track else None,
                "upcoming_track": upcoming_track.to_dict() if upcoming_track else None,
                "current_track_index": current_index,
                "current_raaga": current_track.raaga if current_track else None,
                "upcoming_raaga": upcoming_track.raaga if upcoming_track else None,
                "session_progress_percent": progress,
                "session_elapsed_seconds": elapsed,
                "session_duration_seconds": self.session.session_duration_seconds,
                "crossfade_seconds": self.session.plan.crossfade_seconds,
                "transition_path": [entry.state for entry in self.session.plan.playlist],
            }
        )
        return base

    def refresh_plan_for_new_state(self, *, now: Optional[datetime] = None) -> Optional[SessionPlan]:
        if not self.session or not self.stability.accepted_state:
            return None

        accepted_state = self.stability.accepted_state
        if accepted_state == self.session.current_source_state:
            return self.session.plan

        current_time = now or datetime.utcnow()
        elapsed = max(0, int((current_time - self.session.started_at).total_seconds()))
        remaining_seconds = max(1, self.session.session_duration_seconds - elapsed)
        self.session.playlist_version += 1
        self.session.current_source_state = accepted_state
        self.session.plan = self.build_playlist(
            accepted_state,
            self.session.target_state,
            remaining_seconds,
            now=current_time,
            playlist_version=self.session.playlist_version,
        )
        self.session.last_transition_at = current_time
        return self.session.plan
