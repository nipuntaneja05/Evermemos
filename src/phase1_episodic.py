"""
Phase I: Episodic Trace Formation

This module transforms continuous interaction history into discrete, stable memory units (MemCells).
Implements:
- Step 1: Contextual Segmentation (Semantic Boundary Detection)
- Step 2: Narrative Synthesis (Episode Rewriting)
- Step 3: Structural Derivation (MemCell Extraction)
"""

from datetime import datetime, timedelta
from typing import Optional
import json

from .models import MemCell, Foresight, Metadata, DialogueTurn
from .llm_client import get_llm_client
from .config import Config


class SemanticBoundaryDetector:
    """
    Step 1: Contextual Segmentation
    
    Uses a sliding window approach to detect topic shifts in conversation.
    When a topic shift is detected, the accumulated turns are cut into a "raw episode history".
    """
    
    SYSTEM_PROMPT = """You are a semantic boundary detector for conversational AI. 
Your job is to analyze dialogue turns and detect when a significant topic shift occurs.

A topic shift happens when:
1. The conversation moves to a completely different subject
2. There's a significant change in context (e.g., from work to personal life)
3. A new task or goal is introduced
4. Time or location context changes significantly

You should NOT flag as topic shifts:
1. Natural follow-up questions on the same topic
2. Clarifications or elaborations
3. Related sub-topics within the same theme"""

    def __init__(self):
        self.llm = get_llm_client()
        self.window_size = Config.SLIDING_WINDOW_SIZE
        self.threshold = Config.TOPIC_SHIFT_THRESHOLD
    
    def detect_boundaries(self, turns: list) -> list:
        """
        Process a list of DialogueTurns and identify episode boundaries.
        
        Returns a list of (start_idx, end_idx) tuples representing episode segments.
        
        OPTIMIZATION: Skip LLM-based detection for short conversations.
        """
        if not turns:
            return []
        
        # OPTIMIZATION: For short conversations, treat as single episode (no LLM calls)
        skip_threshold = getattr(Config, 'SKIP_BOUNDARY_DETECTION_THRESHOLD', 10)
        if len(turns) <= skip_threshold:
            return [(0, len(turns) - 1)]
        
        boundaries = [0]  # Start with first turn
        
        # Slide window through conversation
        for i in range(self.window_size, len(turns)):
            window_start = max(0, i - self.window_size)
            window = turns[window_start:i + 1]
            
            # Check if there's a topic shift at position i
            is_shift = self._detect_shift_at_position(window, len(window) - 1)
            
            if is_shift:
                boundaries.append(i)
        
        # Create segments from boundaries
        segments = []
        for i in range(len(boundaries)):
            start = boundaries[i]
            end = boundaries[i + 1] - 1 if i + 1 < len(boundaries) else len(turns) - 1
            if start <= end:
                segments.append((start, end))
        
        return segments
    
    def _detect_shift_at_position(self, window: list, position: int) -> bool:
        """Use LLM to detect if there's a topic shift at the given position."""
        
        # Format the window for analysis
        window_text = self._format_window(window)
        
        prompt = f"""Analyze this conversation window and determine if the LAST turn represents a significant topic shift from the previous turns.

{window_text}

Analyze the semantic continuity and respond with JSON:
{{
    "is_topic_shift": true/false,
    "confidence": 0.0-1.0,
    "reason": "brief explanation"
}}"""
        
        result = self.llm.generate_json(prompt, self.SYSTEM_PROMPT)
        
        if "error" in result:
            return False
        
        is_shift = result.get("is_topic_shift", False)
        confidence = result.get("confidence", 0.0)
        
        return is_shift and confidence >= self.threshold
    
    def _format_window(self, window: list) -> str:
        """Format dialogue turns for LLM analysis."""
        lines = []
        for i, turn in enumerate(window):
            marker = "[CURRENT TURN]" if i == len(window) - 1 else ""
            lines.append(f"Turn {i + 1} {marker}\n{turn.speaker}: {turn.content}")
        return "\n\n".join(lines)


class NarrativeSynthesizer:
    """
    Step 2: Narrative Synthesis
    
    Transforms raw episode history into a high-fidelity Episode (E).
    Produces a concise, third-person narrative that resolves coreferences
    and dialogue ambiguities.
    """
    
    SYSTEM_PROMPT = """You are a narrative rewriter for a memory system. 
Your job is to transform raw dialogue into clear, third-person narratives.

Guidelines:
1. Write in third person (e.g., "The user stated...", "The assistant explained...")
2. Resolve all coreferences (replace "it", "that", "this" with specific referents)
3. Clarify any ambiguous statements
4. Preserve all important information
5. Keep the narrative concise but complete
6. Include any stated intentions, plans, or preferences
7. Note any temporal or contextual information"""

    def __init__(self):
        self.llm = get_llm_client()
    
    def synthesize(self, turns: list, conversation_id: str = "") -> str:
        """
        Transform a list of DialogueTurns into a third-person narrative episode.
        
        Args:
            turns: List of DialogueTurn objects
            conversation_id: Optional ID for context
            
        Returns:
            A synthesized episode narrative string
        """
        if not turns:
            return ""
        
        # Format the raw dialogue
        dialogue_text = self._format_dialogue(turns)
        
        prompt = f"""Transform this dialogue into a clear, third-person narrative summary.

RAW DIALOGUE:
{dialogue_text}

Requirements:
1. Write in third person perspective
2. Resolve all pronouns and references
3. Capture all key information, decisions, and stated intentions
4. Note any temporal markers or plans
5. Keep it concise but complete

Write the narrative summary:"""
        
        episode = self.llm.generate(prompt, self.SYSTEM_PROMPT, temperature=0.5)
        return episode.strip()
    
    def _format_dialogue(self, turns: list) -> str:
        """Format dialogue turns as readable text."""
        lines = []
        for turn in turns:
            timestamp_str = turn.timestamp.strftime("%Y-%m-%d %H:%M") if turn.timestamp else ""
            lines.append(f"[{timestamp_str}] {turn.speaker}: {turn.content}")
        return "\n".join(lines)


class MemCellExtractor:
    """
    Step 3: Structural Derivation
    
    Extracts the constrained schema from the rewritten Episode to create a MemCell.
    Produces: c = (E, F, P, M)
    - E: Episode (the narrative)
    - F: Atomic Facts (discrete, verifiable statements)
    - P: Foresight (forward-looking inferences with temporal validity)
    - M: Metadata (contextual grounding)
    """
    
    SYSTEM_PROMPT = """You are a structured information extractor for a memory system.
Your job is to extract atomic facts, foresights (future implications), and metadata from narrative episodes.

ATOMIC FACTS:
- Discrete, verifiable statements
- Each fact should be independently true
- Include user preferences, attributes, decisions, and stated information
- Format: clear, concise statements

FORESIGHTS (Forward-looking inferences):
- Plans, intentions, goals
- Temporary states (diets, projects, activities)
- Predictions or expectations
- Each must include temporal validity if determinable

METADATA TAGS:
- Key themes or topics
- Categories (health, work, personal, etc.)"""

    def __init__(self):
        self.llm = get_llm_client()
    
    def extract(self, episode: str, turns: list, 
                conversation_id: str = "", 
                current_time: datetime = None) -> MemCell:
        """
        Extract a MemCell from an episode narrative and original turns.
        
        Args:
            episode: The synthesized narrative
            turns: Original DialogueTurn objects
            conversation_id: Source conversation ID
            current_time: Current timestamp for computing time intervals
            
        Returns:
            A complete MemCell with all components
        """
        if current_time is None:
            current_time = datetime.now()
        
        # Extract structured information via LLM
        extraction = self._extract_structure(episode, current_time)
        
        # Build the MemCell
        turn_range = (turns[0].turn_id, turns[-1].turn_id) if turns else (0, 0)
        
        metadata = Metadata(
            created_at=current_time,
            updated_at=current_time,
            source_conversation_id=conversation_id,
            turn_range=turn_range,
            participant_ids=list(set(t.speaker for t in turns)),
            tags=extraction.get("tags", [])
        )
        
        # Parse foresights
        foresights = []
        for f_data in extraction.get("foresights", []):
            foresight = self._parse_foresight(f_data, current_time)
            if foresight:
                foresights.append(foresight)
        
        memcell = MemCell(
            episode=episode,
            atomic_facts=extraction.get("atomic_facts", []),
            foresights=foresights,
            metadata=metadata
        )
        
        return memcell
    
    def _extract_structure(self, episode: str, current_time: datetime) -> dict:
        """Use LLM to extract structured information from the episode."""
        
        prompt = f"""Analyze this episode and extract structured information.

EPISODE:
{episode}

CURRENT TIME: {current_time.strftime("%Y-%m-%d %H:%M")}

Extract and respond with JSON:
{{
    "atomic_facts": [
        "Discrete, verifiable statement 1",
        "Discrete, verifiable statement 2",
        ...
    ],
    "foresights": [
        {{
            "content": "The plan/intention/temporary state",
            "duration_type": "fixed|ongoing|indefinite",
            "duration_value": "number of days/weeks if fixed (e.g., 14 for 2 weeks), null otherwise",
            "start_offset_days": 0,
            "expiry_date": "YYYY-MM-DD format if determinable from context, null otherwise"
        }},
        ...
    ],
    "tags": ["tag1", "tag2", ...]
}}

IMPORTANT FORESIGHT EXTRACTION RULES:
1. ALWAYS try to extract temporal bounds from the conversation
2. Look for phrases like: "next month", "2 weeks", "in March", "until Friday", "for a year"
3. Convert relative times to actual dates using CURRENT TIME as reference:
   - "next week" = 7 days from current time
   - "next month" = 30 days from current time  
   - "in 2 weeks" = 14 days, expiry_date = current + 14 days
   - "for a year" = 365 days
4. For medical treatments (antibiotics, prescriptions): typical duration is 7-14 days
5. For trips/vacations: extract the specific dates or duration mentioned
6. For learning goals, career plans: use "ongoing" if no end date specified
7. If expiry_date can be calculated, ALWAYS include it in YYYY-MM-DD format

Rules for atomic facts:
- Atomic facts should be independently verifiable
- Tags should be high-level categories"""
        
        result = self.llm.generate_json(prompt, self.SYSTEM_PROMPT)
        
        if "error" in result:
            # Fallback: return minimal structure
            return {
                "atomic_facts": [episode],
                "foresights": [],
                "tags": []
            }
        
        return result
    
    def _parse_foresight(self, f_data: dict, current_time: datetime) -> Optional[Foresight]:
        """Parse a foresight dict into a Foresight object with temporal bounds."""
        
        content = f_data.get("content", "")
        if not content:
            return None
        
        duration_type = f_data.get("duration_type", "indefinite")
        start_offset = f_data.get("start_offset_days", 0)
        if start_offset is None:
            start_offset = 0
        
        try:
            t_start = current_time + timedelta(days=int(start_offset))
        except (TypeError, ValueError):
            t_start = current_time
        
        # First, check if LLM provided an explicit expiry_date
        expiry_date_str = f_data.get("expiry_date")
        if expiry_date_str and expiry_date_str != "null" and expiry_date_str != "None":
            try:
                # Parse YYYY-MM-DD format
                t_end = datetime.strptime(str(expiry_date_str)[:10], "%Y-%m-%d")
                # Preserve time component from current_time
                t_end = t_end.replace(hour=23, minute=59, second=59)
            except (ValueError, TypeError):
                t_end = None
        else:
            t_end = None
        
        # Fallback: calculate from duration if expiry_date wasn't provided
        if t_end is None:
            if duration_type == "fixed":
                duration_value = f_data.get("duration_value")
                if duration_value:
                    try:
                        t_end = t_start + timedelta(days=float(duration_value))
                    except:
                        t_end = None
            elif duration_type == "ongoing":
                # Ongoing but not indefinite - set a review period
                t_end = t_start + timedelta(days=30)  # Default 30-day review
            # else: indefinite, t_end stays None
        
        return Foresight(
            content=content,
            t_start=t_start,
            t_end=t_end,
            confidence=0.8
        )


class EpisodicTraceFormation:
    """
    Main class for Phase I: Episodic Trace Formation.
    Orchestrates the complete pipeline from dialogue to MemCells.
    """
    
    def __init__(self):
        self.boundary_detector = SemanticBoundaryDetector()
        self.narrative_synthesizer = NarrativeSynthesizer()
        self.memcell_extractor = MemCellExtractor()
        self.llm = get_llm_client()
    
    def process_transcript(self, transcript: str, conversation_id: str = "",
                          current_time: datetime = None) -> list:
        """
        Process a full conversation transcript into MemCells.
        
        OPTIMIZATION: Uses combined prompt for narrative + extraction (1 LLM call instead of 2).
        """
        if current_time is None:
            current_time = datetime.now()
        
        # Parse transcript into turns
        turns = self._parse_transcript(transcript)
        
        if not turns:
            return []
        
        # Detect episode boundaries (skipped for short conversations)
        segments = self.boundary_detector.detect_boundaries(turns)
        
        # Process each segment with COMBINED prompt
        memcells = []
        for start_idx, end_idx in segments:
            segment_turns = turns[start_idx:end_idx + 1]
            
            # OPTIMIZATION: Combined narrative + extraction in ONE LLM call
            memcell = self._process_segment_combined(
                segment_turns, conversation_id, current_time
            )
            
            if memcell:
                # Generate embedding (local, no API call)
                searchable_text = memcell.get_searchable_text()
                memcell.embedding = self.llm.embed(searchable_text)
                memcells.append(memcell)
        
        return memcells
    
    def _process_segment_combined(self, turns: list, conversation_id: str, 
                                   current_time: datetime) -> MemCell:
        """
        OPTIMIZATION: Process a segment with a single combined LLM call.
        For very short conversations (<=3 turns), use simple extraction without LLM.
        """
        # OPTIMIZATION: For very short conversations, skip LLM entirely
        if len(turns) <= 3:
            return self._process_segment_simple(turns, conversation_id, current_time)
        # Format dialogue
        dialogue_text = "\n".join([f"{t.speaker}: {t.content}" for t in turns])
        
        prompt = f"""Analyze this dialogue and provide BOTH a narrative summary AND structured extraction.

DIALOGUE:
{dialogue_text}

CURRENT TIME: {current_time.strftime("%Y-%m-%d %H:%M")}

Respond with JSON containing:
{{
    "episode": "A clear, third-person narrative summary of the dialogue. Resolve all pronouns and references.",
    "atomic_facts": [
        "Discrete, verifiable statement 1",
        "Discrete, verifiable statement 2"
    ],
    "foresights": [
        {{
            "content": "Any plan/intention/temporary state mentioned",
            "duration_type": "fixed|ongoing|indefinite",
            "duration_value": null,
            "start_offset_days": 0
        }}
    ],
    "tags": ["tag1", "tag2"]
}}

Rules:
- Episode should be 2-4 sentences, third-person perspective
- Atomic facts: each independently verifiable
- Foresights: include duration if mentioned (e.g., "10 days" = fixed, 10)
- Tags: high-level categories (health, work, travel, etc.)"""

        system_prompt = """You are a memory system that converts dialogues into structured memories.
Extract key information accurately and completely."""

        result = self.llm.generate_json(prompt, system_prompt)
        
        if "error" in result:
            # Fallback: use separate calls
            episode = self.narrative_synthesizer.synthesize(turns, conversation_id)
            return self.memcell_extractor.extract(episode, turns, conversation_id, current_time)
        
        # Build MemCell from combined result
        turn_range = (turns[0].turn_id, turns[-1].turn_id) if turns else (0, 0)
        
        metadata = Metadata(
            created_at=current_time,
            updated_at=current_time,
            source_conversation_id=conversation_id,
            turn_range=turn_range,
            participant_ids=list(set(t.speaker for t in turns)),
            tags=result.get("tags", [])
        )
        
        # Parse foresights
        foresights = []
        for f_data in result.get("foresights", []):
            foresight = self.memcell_extractor._parse_foresight(f_data, current_time)
            if foresight:
                foresights.append(foresight)
        
        return MemCell(
            episode=result.get("episode", ""),
            atomic_facts=result.get("atomic_facts", []),
            foresights=foresights,
            metadata=metadata
        )
    
    def _process_segment_simple(self, turns: list, conversation_id: str,
                                 current_time: datetime) -> MemCell:
        """
        Simple extraction for very short conversations (no LLM call).
        Just concatenates the dialogue as the episode.
        """
        # Create simple episode from dialogue
        episode_parts = []
        for turn in turns:
            episode_parts.append(f"{turn.speaker.capitalize()} said: {turn.content}")
        episode = " ".join(episode_parts)
        
        # Extract simple facts (just the content)
        atomic_facts = [turn.content for turn in turns if turn.speaker.lower() == "user"]
        
        turn_range = (turns[0].turn_id, turns[-1].turn_id) if turns else (0, 0)
        
        metadata = Metadata(
            created_at=current_time,
            updated_at=current_time,
            source_conversation_id=conversation_id,
            turn_range=turn_range,
            participant_ids=list(set(t.speaker for t in turns)),
            tags=["short_conversation"]
        )
        
        return MemCell(
            episode=episode,
            atomic_facts=atomic_facts,
            foresights=[],
            metadata=metadata
        )
    
    def process_turns(self, turns: list, conversation_id: str = "",
                     current_time: datetime = None) -> list:
        """
        Process a list of DialogueTurn objects into MemCells.
        
        Args:
            turns: List of DialogueTurn objects
            conversation_id: Optional ID for the conversation
            current_time: Current timestamp
            
        Returns:
            List of MemCell objects
        """
        if current_time is None:
            current_time = datetime.now()
        
        if not turns:
            return []
        
        # Detect episode boundaries
        segments = self.boundary_detector.detect_boundaries(turns)
        
        # Process each segment
        memcells = []
        for start_idx, end_idx in segments:
            segment_turns = turns[start_idx:end_idx + 1]
            
            # Synthesize narrative
            episode = self.narrative_synthesizer.synthesize(
                segment_turns, conversation_id
            )
            
            # Extract MemCell
            memcell = self.memcell_extractor.extract(
                episode, segment_turns, conversation_id, current_time
            )
            
            # Generate embedding
            searchable_text = memcell.get_searchable_text()
            memcell.embedding = self.llm.embed(searchable_text)
            
            memcells.append(memcell)
        
        return memcells
    
    def _parse_transcript(self, transcript: str) -> list:
        """
        Parse a raw transcript string into DialogueTurn objects.
        Supports various formats.
        """
        turns = []
        lines = transcript.strip().split('\n')
        
        current_turn_id = 0
        current_speaker = None
        current_content = []
        current_timestamp = datetime.now()
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Try to parse as Speaker: Content format
            parsed = self._parse_line(line)
            
            if parsed:
                # Save previous turn if exists
                if current_speaker and current_content:
                    turns.append(DialogueTurn(
                        turn_id=current_turn_id,
                        speaker=current_speaker,
                        content=' '.join(current_content),
                        timestamp=current_timestamp
                    ))
                    current_turn_id += 1
                
                current_speaker = parsed['speaker']
                current_content = [parsed['content']]
                if parsed.get('timestamp'):
                    current_timestamp = parsed['timestamp']
            else:
                # Continuation of previous turn
                if current_content:
                    current_content.append(line)
        
        # Don't forget the last turn
        if current_speaker and current_content:
            turns.append(DialogueTurn(
                turn_id=current_turn_id,
                speaker=current_speaker,
                content=' '.join(current_content),
                timestamp=current_timestamp
            ))
        
        return turns
    
    def _parse_line(self, line: str) -> Optional[dict]:
        """Parse a single line to extract speaker and content."""
        import re
        
        # Pattern 1: [timestamp] Speaker: content
        match = re.match(r'\[([^\]]+)\]\s*(\w+):\s*(.+)', line)
        if match:
            try:
                timestamp = datetime.strptime(match.group(1), "%Y-%m-%d %H:%M")
            except:
                timestamp = None
            return {
                'timestamp': timestamp,
                'speaker': match.group(2).lower(),
                'content': match.group(3)
            }
        
        # Pattern 2: Speaker: content
        match = re.match(r'^(\w+):\s*(.+)', line)
        if match:
            return {
                'speaker': match.group(1).lower(),
                'content': match.group(2)
            }
        
        # Pattern 3: **Speaker**: content (markdown)
        match = re.match(r'^\*\*(\w+)\*\*:\s*(.+)', line)
        if match:
            return {
                'speaker': match.group(1).lower(),
                'content': match.group(2)
            }
        
        return None
