"""
Phase I: Episodic Trace Formation (BetterMemory Pipeline)

This module transforms continuous interaction history into discrete, stable memory units (MemCells).
Optimized for Signal-to-Noise Ratio with:
- Priority Filter (SwiftMem): Discard chitchat before LLM processing
- Unified Prompt Packing: Single LLM call for narrative + facts + foresights + entities
- S-A-O Triples: Subject-Action-Object structured fact extraction
- Entity Extraction: Tag MemCells with entities for grounded retrieval
"""

from datetime import datetime, timedelta
from typing import Optional
import json
import re

from .models import MemCell, Foresight, Metadata, DialogueTurn
from .llm_client import get_llm_client
from .config import Config


class PriorityFilter:
    """
    BetterMemory: SwiftMem Priority Filter
    
    Discards low-information "chitchat" turns (e.g., "Ok", "Thanks", "Haha") 
    before LLM processing to increase signal-to-noise ratio and save ~30% API costs.
    """
    
    def __init__(self):
        self.enabled = Config.PRIORITY_FILTER_ENABLED
        self.max_words = Config.CHITCHAT_MAX_WORDS
        self.patterns = [p.lower() for p in Config.CHITCHAT_PATTERNS]
    
    def filter_turns(self, turns: list) -> list:
        """
        Filter out chitchat turns, preserving informative content.
        
        Args:
            turns: List of DialogueTurn objects
            
        Returns:
            Filtered list with chitchat removed. Always preserves at least 2 turns.
        """
        if not self.enabled or len(turns) <= 2:
            return turns
        
        filtered = []
        for turn in turns:
            if not self._is_chitchat(turn):
                filtered.append(turn)
        
        # Safety: always keep at least 2 turns (never return empty)
        if len(filtered) < 2:
            return turns
        
        return filtered
    
    def _is_chitchat(self, turn: DialogueTurn) -> bool:
        """Check if a turn is low-information chitchat."""
        content = turn.content.strip().lower()
        
        # Remove punctuation for matching
        clean = re.sub(r'[^\w\s]', '', content).strip()
        
        # Check word count
        words = clean.split()
        if len(words) > self.max_words:
            return False  # Too many words to be chitchat
        
        # Exact match against known chitchat patterns
        if clean in self.patterns:
            return True
        
        # Single word responses that aren't informative
        if len(words) == 1 and len(clean) <= 4:
            return True
        
        return False
    
    def get_stats(self, original_count: int, filtered_count: int) -> dict:
        """Get filtering statistics."""
        removed = original_count - filtered_count
        return {
            "original_turns": original_count,
            "filtered_turns": filtered_count,
            "removed": removed,
            "savings_pct": round(removed / max(original_count, 1) * 100, 1)
        }


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
    Step 3: Structural Derivation (BetterMemory Enhanced)
    
    Extracts the constrained schema from the rewritten Episode to create a MemCell.
    Produces: c = (E, F, P, M) with BetterMemory enhancements:
    - E: Episode (the narrative)
    - F: Atomic Facts as S-A-O triples (Subject-Action-Object)
    - P: Foresight (forward-looking inferences with temporal validity)
    - M: Metadata with Entity Tags for grounded retrieval
    """
    
    SYSTEM_PROMPT = """You are a structured information extractor for a memory system.
Your job is to extract atomic facts, foresights (future implications), entities, and metadata from narrative episodes.

ATOMIC FACTS (Subject-Action-Object format):
- Each fact should be a clear statement in Subject-Action-Object format
- Example: "User bought a Tesla Model 3", "User works at Google as engineer"
- Each fact should be independently verifiable
- Include user preferences, attributes, decisions, and stated information

FORESIGHTS (Forward-looking inferences):
- Plans, intentions, goals
- Temporary states (diets, projects, activities)
- Predictions or expectations
- Each must include temporal validity if determinable

ENTITIES:
- Extract named entities: People, Places, Organizations, Objects
- These are used for precise retrieval filtering

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
            tags=extraction.get("tags", []),
            entities=extraction.get("entities", [])
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
        "Subject-Action-Object statement 1 (e.g., 'User started a vegan diet')",
        "Subject-Action-Object statement 2 (e.g., 'User works at Google as senior engineer')"
    ],
    "foresights": [
        {{
            "content": "The plan/intention/temporary state",
            "duration_type": "fixed|ongoing|indefinite",
            "duration_value": "number of days/weeks if fixed (e.g., 14 for 2 weeks), null otherwise",
            "start_offset_days": 0,
            "expiry_date": "YYYY-MM-DD format if determinable from context, null otherwise"
        }}
    ],
    "entities": ["Person Name", "Place Name", "Organization", "Important Object"],
    "tags": ["tag1", "tag2"]
}}

IMPORTANT RULES:
1. Atomic facts MUST be in Subject-Action-Object format for precise conflict detection
2. ENTITIES: Extract ALL named entities (people, places, organizations, objects mentioned)
3. FORESIGHT: ALWAYS try to extract temporal bounds from the conversation
4. Look for phrases like: "next month", "2 weeks", "in March", "until Friday", "for a year"
5. Convert relative times to actual dates using CURRENT TIME as reference
6. For medical treatments: typical duration is 7-14 days
7. For trips/vacations: extract specific dates or duration mentioned
8. Tags should be high-level categories (health, work, travel, etc.)"""
        
        result = self.llm.generate_json(prompt, self.SYSTEM_PROMPT)
        
        if "error" in result:
            # Fallback: return minimal structure
            return {
                "atomic_facts": [episode],
                "foresights": [],
                "entities": [],
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
    Main class for Phase I: Episodic Trace Formation (BetterMemory).
    Orchestrates the complete pipeline from dialogue to MemCells.
    
    BetterMemory enhancements:
    - Priority Filter: Removes chitchat before processing
    - Unified Prompt: Single LLM call for narrative + facts + foresights + entities
    - S-A-O Facts: Structured fact extraction for better conflict detection
    - Entity Tags: Named entity extraction for grounded retrieval
    """
    
    def __init__(self):
        self.priority_filter = PriorityFilter()
        self.boundary_detector = SemanticBoundaryDetector()
        self.narrative_synthesizer = NarrativeSynthesizer()
        self.memcell_extractor = MemCellExtractor()
        self.llm = get_llm_client()
    
    def process_transcript(self, transcript: str, conversation_id: str = "",
                          current_time: datetime = None) -> list:
        """
        Process a full conversation transcript into MemCells.
        
        BetterMemory optimizations:
        1. Priority Filter: Remove chitchat turns before processing
        2. Unified Prompt: Combined narrative + extraction in ONE LLM call
        3. Entity Extraction: Tag MemCells with entities for grounded retrieval
        """
        if current_time is None:
            current_time = datetime.now()
        
        # Parse transcript into turns
        turns = self._parse_transcript(transcript)
        
        if not turns:
            return []
        
        # BetterMemory: Priority Filter - remove chitchat
        filtered_turns = self.priority_filter.filter_turns(turns)
        
        # Detect episode boundaries (skipped for short conversations)
        segments = self.boundary_detector.detect_boundaries(filtered_turns)
        
        # Process each segment with UNIFIED prompt
        memcells = []
        for start_idx, end_idx in segments:
            segment_turns = filtered_turns[start_idx:end_idx + 1]
            
            # BetterMemory: Unified prompt for all extraction
            memcell = self._process_segment_unified(
                segment_turns, conversation_id, current_time
            )
            
            if memcell:
                # Generate embedding (local, no API call)
                searchable_text = memcell.get_searchable_text()
                memcell.embedding = self.llm.embed(searchable_text)
                memcells.append(memcell)
        
        return memcells
    
    def _process_segment_unified(self, turns: list, conversation_id: str, 
                                   current_time: datetime) -> MemCell:
        """
        BetterMemory: Unified prompt packing - single LLM call for:
        - Episode narrative (third-person summary)
        - Atomic facts (S-A-O triples)
        - Foresights (temporal plans)
        - Entity tags (people, places, objects)
        
        For very short conversations (<=3 turns), use simple extraction without LLM.
        """
        # OPTIMIZATION: For very short conversations, skip LLM entirely
        if len(turns) <= 3:
            return self._process_segment_simple(turns, conversation_id, current_time)
        
        # Format dialogue
        dialogue_text = "\n".join([f"{t.speaker}: {t.content}" for t in turns])
        
        prompt = f"""Analyze this dialogue and provide a COMPLETE structured memory extraction in ONE response.

DIALOGUE:
{dialogue_text}

CURRENT TIME: {current_time.strftime("%Y-%m-%d %H:%M")}

Respond with JSON containing ALL of the following:
{{
    "episode": "A clear, third-person narrative summary of the dialogue. Resolve all pronouns and references. 2-4 sentences.",
    "atomic_facts": [
        "Subject-Action-Object statement (e.g., 'User started a vegan diet')",
        "Subject-Action-Object statement (e.g., 'User works at Google as senior engineer')"
    ],
    "foresights": [
        {{
            "content": "Any plan/intention/temporary state mentioned",
            "duration_type": "fixed|ongoing|indefinite",
            "duration_value": null,
            "start_offset_days": 0,
            "expiry_date": "YYYY-MM-DD if determinable, null otherwise"
        }}
    ],
    "entities": ["Person Name", "Place Name", "Organization", "Important Object"],
    "tags": ["high-level category 1", "high-level category 2"]
}}

CRITICAL RULES:
- Episode: 2-4 sentences, third-person perspective, resolve all references
- Atomic facts: MUST be in Subject-Action-Object format for conflict detection
- Entities: Extract ALL named entities (people, places, organizations, key objects)
- Foresights: Include temporal duration if mentioned (e.g., "10 days" = fixed, 10)
- Tags: High-level categories (health, work, travel, personal, etc.)
- If no foresights exist, return empty list
- If no entities found, return empty list"""

        system_prompt = """You are BetterMemory - an advanced memory system that converts dialogues into structured memories.
Extract key information accurately and completely in a single pass. Focus on:
1. Clear narrative summaries
2. Precise Subject-Action-Object facts
3. Named entity extraction for retrieval
4. Temporal plan detection"""

        result = self.llm.generate_json(prompt, system_prompt)
        
        if "error" in result:
            # Fallback: use separate calls
            episode = self.narrative_synthesizer.synthesize(turns, conversation_id)
            return self.memcell_extractor.extract(episode, turns, conversation_id, current_time)
        
        # Build MemCell from unified result
        turn_range = (turns[0].turn_id, turns[-1].turn_id) if turns else (0, 0)
        
        metadata = Metadata(
            created_at=current_time,
            updated_at=current_time,
            source_conversation_id=conversation_id,
            turn_range=turn_range,
            participant_ids=list(set(t.speaker for t in turns)),
            tags=result.get("tags", []),
            entities=result.get("entities", [])
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
        BetterMemory: Also extracts basic entities from content.
        """
        # Create simple episode from dialogue
        episode_parts = []
        for turn in turns:
            episode_parts.append(f"{turn.speaker.capitalize()} said: {turn.content}")
        episode = " ".join(episode_parts)
        
        # Extract simple facts (just the content)
        atomic_facts = [turn.content for turn in turns if turn.speaker.lower() == "user"]
        
        # BetterMemory: Basic entity extraction from content (no LLM needed)
        entities = self._extract_entities_simple(turns)
        
        turn_range = (turns[0].turn_id, turns[-1].turn_id) if turns else (0, 0)
        
        metadata = Metadata(
            created_at=current_time,
            updated_at=current_time,
            source_conversation_id=conversation_id,
            turn_range=turn_range,
            participant_ids=list(set(t.speaker for t in turns)),
            tags=["short_conversation"],
            entities=entities
        )
        
        return MemCell(
            episode=episode,
            atomic_facts=atomic_facts,
            foresights=[],
            metadata=metadata
        )
    
    def _extract_entities_simple(self, turns: list) -> list:
        """
        Simple rule-based entity extraction for short conversations.
        Extracts capitalized words that look like proper nouns.
        """
        entities = set()
        for turn in turns:
            # Find capitalized words (likely proper nouns)
            words = turn.content.split()
            for i, word in enumerate(words):
                clean = re.sub(r'[^\w]', '', word)
                if clean and clean[0].isupper() and len(clean) > 1:
                    # Skip first word of sentence and common words
                    if i > 0 or len(clean) > 3:
                        entities.add(clean)
        return list(entities)
    
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
        
        # BetterMemory: Priority Filter
        filtered_turns = self.priority_filter.filter_turns(turns)
        
        # Detect episode boundaries
        segments = self.boundary_detector.detect_boundaries(filtered_turns)
        
        # Process each segment
        memcells = []
        for start_idx, end_idx in segments:
            segment_turns = filtered_turns[start_idx:end_idx + 1]
            
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
