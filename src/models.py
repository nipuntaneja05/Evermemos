"""
Data models for the Evermemos memory system.
Defines the core structures: MemCell, MemScene, UserProfile, etc.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from uuid import uuid4
import json


@dataclass
class Foresight:
    """
    Forward-looking inference with temporal validity.
    Represents temporary states, plans, or predictions.
    """
    id: str = field(default_factory=lambda: str(uuid4()))
    content: str = ""
    t_start: datetime = field(default_factory=datetime.now)
    t_end: Optional[datetime] = None  # None means indefinitely valid
    confidence: float = 0.8
    source_episode_id: str = ""
    
    def is_valid_at(self, timestamp: datetime) -> bool:
        """Check if this foresight is valid at a given timestamp."""
        if timestamp < self.t_start:
            return False
        if self.t_end is not None and timestamp > self.t_end:
            return False
        return True
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "content": self.content,
            "t_start": self.t_start.isoformat(),
            "t_end": self.t_end.isoformat() if self.t_end else None,
            "confidence": self.confidence,
            "source_episode_id": self.source_episode_id
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Foresight":
        return cls(
            id=data.get("id", str(uuid4())),
            content=data["content"],
            t_start=datetime.fromisoformat(data["t_start"]) if data.get("t_start") else datetime.now(),
            t_end=datetime.fromisoformat(data["t_end"]) if data.get("t_end") else None,
            confidence=data.get("confidence", 0.8),
            source_episode_id=data.get("source_episode_id", "")
        )


@dataclass
class Metadata:
    """
    Contextual grounding for MemCells.
    Contains timestamps and source pointers.
    """
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    source_conversation_id: str = ""
    turn_range: tuple = (0, 0)  # (start_turn, end_turn)
    participant_ids: list = field(default_factory=list)
    tags: list = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "source_conversation_id": self.source_conversation_id,
            "turn_range": list(self.turn_range),
            "participant_ids": self.participant_ids,
            "tags": self.tags
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Metadata":
        return cls(
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now(),
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else datetime.now(),
            source_conversation_id=data.get("source_conversation_id", ""),
            turn_range=tuple(data.get("turn_range", [0, 0])),
            participant_ids=data.get("participant_ids", []),
            tags=data.get("tags", [])
        )


@dataclass
class MemCell:
    """
    The fundamental memory unit: c = (E, F, P, M)
    - E: Episode (narrative summary)
    - F: Atomic Facts (discrete verifiable statements)
    - P: Foresight (forward-looking inferences with temporal validity)
    - M: Metadata (contextual grounding)
    """
    id: str = field(default_factory=lambda: str(uuid4()))
    episode: str = ""  # E: Third-person narrative summary
    atomic_facts: list = field(default_factory=list)  # F: List of fact strings
    foresights: list = field(default_factory=list)  # P: List of Foresight objects
    metadata: Metadata = field(default_factory=Metadata)  # M: Contextual info
    embedding: list = field(default_factory=list)  # Vector embedding
    memscene_id: Optional[str] = None  # Reference to parent MemScene
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "episode": self.episode,
            "atomic_facts": self.atomic_facts,
            "foresights": [f.to_dict() if isinstance(f, Foresight) else f for f in self.foresights],
            "metadata": self.metadata.to_dict() if isinstance(self.metadata, Metadata) else self.metadata,
            "embedding": self.embedding,
            "memscene_id": self.memscene_id
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "MemCell":
        return cls(
            id=data.get("id", str(uuid4())),
            episode=data["episode"],
            atomic_facts=data.get("atomic_facts", []),
            foresights=[Foresight.from_dict(f) for f in data.get("foresights", [])],
            metadata=Metadata.from_dict(data["metadata"]) if data.get("metadata") else Metadata(),
            embedding=data.get("embedding", []),
            memscene_id=data.get("memscene_id")
        )
    
    def get_searchable_text(self) -> str:
        """Get combined text for embedding and search."""
        facts_text = " ".join(self.atomic_facts)
        foresight_text = " ".join([f.content for f in self.foresights if isinstance(f, Foresight)])
        return f"{self.episode} {facts_text} {foresight_text}"


@dataclass
class MemScene:
    """
    A thematic cluster of related MemCells.
    Represents a higher-order semantic structure.
    """
    id: str = field(default_factory=lambda: str(uuid4()))
    theme: str = ""  # Descriptive theme of this scene
    summary: str = ""  # Aggregated summary
    memcell_ids: list = field(default_factory=list)  # References to MemCells
    centroid: list = field(default_factory=list)  # Centroid vector
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "theme": self.theme,
            "summary": self.summary,
            "memcell_ids": self.memcell_ids,
            "centroid": self.centroid,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "MemScene":
        return cls(
            id=data.get("id", str(uuid4())),
            theme=data.get("theme", ""),
            summary=data.get("summary", ""),
            memcell_ids=data.get("memcell_ids", []),
            centroid=data.get("centroid", []),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now(),
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else datetime.now()
        )


@dataclass
class ExplicitFact:
    """Verifiable attribute with temporal tracking."""
    attribute: str = ""
    value: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    source_memcell_id: str = ""
    confidence: float = 1.0
    
    def to_dict(self) -> dict:
        return {
            "attribute": self.attribute,
            "value": self.value,
            "timestamp": self.timestamp.isoformat(),
            "source_memcell_id": self.source_memcell_id,
            "confidence": self.confidence
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "ExplicitFact":
        return cls(
            attribute=data["attribute"],
            value=data["value"],
            timestamp=datetime.fromisoformat(data["timestamp"]) if data.get("timestamp") else datetime.now(),
            source_memcell_id=data.get("source_memcell_id", ""),
            confidence=data.get("confidence", 1.0)
        )


@dataclass
class ImplicitTrait:
    """Inferred preferences, habits, personality traits."""
    trait_type: str = ""  # preference, habit, personality
    description: str = ""
    evidence: list = field(default_factory=list)  # List of supporting memcell_ids
    strength: float = 0.5  # 0.0 to 1.0
    last_updated: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> dict:
        return {
            "trait_type": self.trait_type,
            "description": self.description,
            "evidence": self.evidence,
            "strength": self.strength,
            "last_updated": self.last_updated.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "ImplicitTrait":
        return cls(
            trait_type=data.get("trait_type", ""),
            description=data["description"],
            evidence=data.get("evidence", []),
            strength=data.get("strength", 0.5),
            last_updated=datetime.fromisoformat(data["last_updated"]) if data.get("last_updated") else datetime.now()
        )


@dataclass
class ConflictRecord:
    """Record of detected conflicts and their resolution."""
    id: str = field(default_factory=lambda: str(uuid4()))
    attribute: str = ""
    old_value: str = ""
    new_value: str = ""
    old_source: str = ""
    new_source: str = ""
    resolution: str = ""  # "recency", "confidence", "manual"
    resolved_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "attribute": self.attribute,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "old_source": self.old_source,
            "new_source": self.new_source,
            "resolution": self.resolution,
            "resolved_at": self.resolved_at.isoformat()
        }


@dataclass
class UserProfile:
    """
    Compact user profile derived from MemScene evidence.
    Maintains explicit facts, implicit traits, and conflict history.
    """
    id: str = field(default_factory=lambda: str(uuid4()))
    user_id: str = ""
    explicit_facts: dict = field(default_factory=dict)  # attribute -> ExplicitFact
    implicit_traits: list = field(default_factory=list)  # List of ImplicitTrait
    conflict_history: list = field(default_factory=list)  # List of ConflictRecord
    last_updated: datetime = field(default_factory=datetime.now)
    source_memscenes: list = field(default_factory=list)  # List of contributing MemScene IDs
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "explicit_facts": {k: v.to_dict() if isinstance(v, ExplicitFact) else v 
                             for k, v in self.explicit_facts.items()},
            "implicit_traits": [t.to_dict() if isinstance(t, ImplicitTrait) else t 
                               for t in self.implicit_traits],
            "conflict_history": [c.to_dict() if isinstance(c, ConflictRecord) else c 
                                for c in self.conflict_history],
            "last_updated": self.last_updated.isoformat(),
            "source_memscenes": self.source_memscenes
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "UserProfile":
        return cls(
            id=data.get("id", str(uuid4())),
            user_id=data.get("user_id", ""),
            explicit_facts={k: ExplicitFact.from_dict(v) for k, v in data.get("explicit_facts", {}).items()},
            implicit_traits=[ImplicitTrait.from_dict(t) for t in data.get("implicit_traits", [])],
            conflict_history=data.get("conflict_history", []),
            last_updated=datetime.fromisoformat(data["last_updated"]) if data.get("last_updated") else datetime.now(),
            source_memscenes=data.get("source_memscenes", [])
        )
    
    def update_explicit_fact(self, attribute: str, new_fact: ExplicitFact) -> Optional[ConflictRecord]:
        """
        Update an explicit fact with recency-aware conflict resolution.
        Returns a ConflictRecord if there was a conflict.
        """
        conflict = None
        if attribute in self.explicit_facts:
            old_fact = self.explicit_facts[attribute]
            if old_fact.value != new_fact.value:
                # Conflict detected - use recency to resolve
                conflict = ConflictRecord(
                    attribute=attribute,
                    old_value=old_fact.value,
                    new_value=new_fact.value,
                    old_source=old_fact.source_memcell_id,
                    new_source=new_fact.source_memcell_id,
                    resolution="recency"
                )
                self.conflict_history.append(conflict)
        
        self.explicit_facts[attribute] = new_fact
        self.last_updated = datetime.now()
        return conflict


@dataclass 
class DialogueTurn:
    """A single turn in a conversation."""
    turn_id: int = 0
    speaker: str = ""  # "user" or "assistant" or participant ID
    content: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> dict:
        return {
            "turn_id": self.turn_id,
            "speaker": self.speaker,
            "content": self.content,
            "timestamp": self.timestamp.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "DialogueTurn":
        return cls(
            turn_id=data.get("turn_id", 0),
            speaker=data.get("speaker", ""),
            content=data.get("content", ""),
            timestamp=datetime.fromisoformat(data["timestamp"]) if data.get("timestamp") else datetime.now()
        )


@dataclass
class RetrievalResult:
    """Result from the retrieval system."""
    memcell: MemCell = None
    memscene: Optional[MemScene] = None
    dense_score: float = 0.0
    sparse_score: float = 0.0
    rrf_score: float = 0.0
    temporal_valid_foresights: list = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            "memcell": self.memcell.to_dict() if self.memcell else None,
            "memscene": self.memscene.to_dict() if self.memscene else None,
            "dense_score": self.dense_score,
            "sparse_score": self.sparse_score,
            "rrf_score": self.rrf_score,
            "temporal_valid_foresights": [f.to_dict() if isinstance(f, Foresight) else f 
                                          for f in self.temporal_valid_foresights]
        }
