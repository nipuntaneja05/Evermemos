"""
Phase II: Semantic Consolidation

This module organizes MemCells into higher-order structures (MemScenes)
and maintains User Profiles through scene-driven evolution.
Implements:
- Step 1: Incremental Semantic Clustering
- Step 2: Scene-Driven Profile Evolution with Conflict Detection
"""

from datetime import datetime
from typing import Optional, Tuple
import numpy as np

from .models import MemCell, MemScene, UserProfile, ExplicitFact, ImplicitTrait, ConflictRecord
from .llm_client import get_llm_client
from .vector_store import get_vector_store
from .config import Config



def cosine_similarity(vec1: list, vec2: list) -> float:
    """Compute cosine similarity between two vectors."""
    a = np.array(vec1)
    b = np.array(vec2)
    
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    
    if norm_a == 0 or norm_b == 0:
        return 0.0
    
    return float(np.dot(a, b) / (norm_a * norm_b))


class IncrementalClusterer:
    """
    Step 1: Incremental Semantic Clustering
    
    An online mechanism that maintains thematic structure in real-time
    without batch reprocessing.
    
    When a new MemCell arrives:
    1. Compute its vector embedding
    2. Retrieve nearest MemScene centroid
    3. Calculate similarity
    4. If similarity > τ, assimilate into existing scene
    5. Otherwise, instantiate a new MemScene
    """
    
    SCENE_THEME_PROMPT = """You are a thematic analyzer. Given a collection of episode summaries,
identify the overarching theme that connects them.

Provide a concise theme title (2-5 words) and a brief summary."""

    def __init__(self):
        self.llm = get_llm_client()
        self.vector_store = get_vector_store()
        self.threshold = Config.MEMSCENE_SIMILARITY_THRESHOLD
    
    def cluster_memcell(self, memcell: MemCell) -> Tuple[MemScene, bool]:
        """
        Cluster a MemCell into an existing or new MemScene.
        
        Args:
            memcell: The MemCell to cluster
            
        Returns:
            Tuple of (MemScene, is_new_scene)
        """
        if not memcell.embedding:
            raise ValueError("MemCell must have an embedding before clustering")
        
        # Get all existing MemScenes
        existing_scenes = self.vector_store.get_all_memscenes()
        
        if not existing_scenes:
            # First MemCell - create new scene
            return self._create_new_scene(memcell), True
        
        # Find the most similar scene
        best_scene = None
        best_similarity = -1.0
        
        for scene in existing_scenes:
            if scene.centroid:
                similarity = cosine_similarity(memcell.embedding, scene.centroid)
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_scene = scene
        
        # Check against threshold
        if best_similarity >= self.threshold:
            # Assimilate into existing scene
            updated_scene = self._assimilate_memcell(memcell, best_scene)
            return updated_scene, False
        else:
            # Create new scene
            return self._create_new_scene(memcell), True
    
    def _create_new_scene(self, memcell: MemCell) -> MemScene:
        """Create a new MemScene from a single MemCell."""
        
        # Generate theme from the episode
        theme = self._generate_theme([memcell.episode])
        
        scene = MemScene(
            theme=theme,
            summary=memcell.episode,
            memcell_ids=[memcell.id],
            centroid=memcell.embedding.copy(),
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Update memcell's scene reference
        memcell.memscene_id = scene.id
        
        # Store both
        self.vector_store.upsert_memscene(scene)
        self.vector_store.upsert_memcell(memcell)
        
        return scene
    
    def _assimilate_memcell(self, memcell: MemCell, scene: MemScene) -> MemScene:
        """Assimilate a MemCell into an existing MemScene."""
        
        # Add MemCell to scene
        scene.memcell_ids.append(memcell.id)
        
        # Update centroid (running average)
        n = len(scene.memcell_ids)
        new_centroid = []
        for i in range(len(scene.centroid)):
            updated = ((scene.centroid[i] * (n - 1)) + memcell.embedding[i]) / n
            new_centroid.append(updated)
        scene.centroid = new_centroid
        
        # Update summary with new information
        scene.summary = self._update_scene_summary(scene, memcell)
        scene.updated_at = datetime.now()
        
        # Update memcell's scene reference
        memcell.memscene_id = scene.id
        
        # BetterMemory: Virtual graph linking - connect related MemCells via entity overlap
        self._link_related_memcells(memcell, scene)
        
        # Store both
        self.vector_store.upsert_memscene(scene)
        self.vector_store.upsert_memcell(memcell)
        
        return scene
    
    def _link_related_memcells(self, new_memcell: MemCell, scene: MemScene):
        """
        BetterMemory: Virtual graph linking.
        Connect MemCells that share entity tags within a scene.
        This creates bidirectional links in metadata.related_memcell_ids.
        """
        new_entities = set(getattr(new_memcell.metadata, 'entities', []))
        if not new_entities:
            return
        
        # Check existing memcells in the scene for entity overlap
        existing_ids = [mid for mid in scene.memcell_ids if mid != new_memcell.id]
        if not existing_ids:
            return
        
        existing_memcells = self.vector_store.get_memcells_by_ids(existing_ids)
        
        for existing_mc in existing_memcells:
            existing_entities = set(getattr(existing_mc.metadata, 'entities', []))
            # Check for entity overlap (case-insensitive)
            overlap = {e.lower() for e in new_entities} & {e.lower() for e in existing_entities}
            
            if overlap:
                # Add bidirectional links
                if existing_mc.id not in new_memcell.metadata.related_memcell_ids:
                    new_memcell.metadata.related_memcell_ids.append(existing_mc.id)
                if new_memcell.id not in existing_mc.metadata.related_memcell_ids:
                    existing_mc.metadata.related_memcell_ids.append(new_memcell.id)
                    # Persist the updated existing memcell
                    self.vector_store.upsert_memcell(existing_mc)
    
    def _generate_theme(self, episodes: list) -> str:
        """Generate a thematic title from episodes."""
        
        combined = "\n---\n".join(episodes[:5])  # Limit to first 5
        
        prompt = f"""Given these episode summaries, provide a concise theme title (2-5 words):

{combined}

Theme title:"""
        
        theme = self.llm.generate(prompt, temperature=0.3, max_tokens=50)
        return theme.strip().replace('"', '').replace("'", "")
    
    def _update_scene_summary(self, scene: MemScene, new_memcell: MemCell) -> str:
        """Update scene summary to incorporate new MemCell."""
        
        prompt = f"""Update this scene summary to incorporate new information.

CURRENT SUMMARY:
{scene.summary}

NEW EPISODE:
{new_memcell.episode}

Provide an updated, cohesive summary that captures all key information:"""
        
        summary = self.llm.generate(prompt, temperature=0.5, max_tokens=500)
        return summary.strip()


class ProfileEvolver:
    """
    Step 2: Scene-Driven Profile Evolution
    
    Updates a compact User Profile from aggregated scene evidence.
    Tracks:
    - Explicit Facts: Verifiable attributes and time-varying measurements
    - Implicit Traits: Preferences, habits, and personality traits
    - Conflict Tracking: Managed through recency-aware updates
    """
    
    EXTRACTION_PROMPT = """You are a profile analyzer. Extract user information from scene summaries.

EXPLICIT FACTS: Verifiable attributes like:
- Demographics (age, location, occupation)
- Time-varying measurements (weight, health metrics)
- Stated preferences that are factual

IMPLICIT TRAITS: Inferences about:
- Preferences and tastes
- Habits and routines
- Personality characteristics
- Communication style

Be precise and include only information with clear evidence."""

    def __init__(self):
        self.llm = get_llm_client()
        self.vector_store = get_vector_store()
        self._profile: Optional[UserProfile] = None
    
    def get_profile(self, user_id: str = "default") -> UserProfile:
        """Get or create the user profile."""
        if self._profile is None:
            self._profile = UserProfile(user_id=user_id)
        return self._profile
    
    def evolve_from_scene(self, scene: MemScene, user_id: str = "default") -> list:
        """
        Update user profile based on a MemScene.
        
        Args:
            scene: The MemScene to process
            user_id: The user ID
            
        Returns:
            List of ConflictRecord if any conflicts were detected
        """
        profile = self.get_profile(user_id)
        
        # Extract facts and traits from scene
        extraction = self._extract_profile_data(scene)
        
        conflicts = []
        
        # Process explicit facts
        for fact_data in extraction.get("explicit_facts", []):
            fact = ExplicitFact(
                attribute=fact_data.get("attribute", ""),
                value=fact_data.get("value", ""),
                timestamp=datetime.now(),
                source_memcell_id=scene.memcell_ids[-1] if scene.memcell_ids else "",
                confidence=fact_data.get("confidence", 0.8)
            )
            
            if fact.attribute:
                conflict = profile.update_explicit_fact(fact.attribute, fact)
                if conflict:
                    conflicts.append(conflict)
        
        # Process implicit traits
        for trait_data in extraction.get("implicit_traits", []):
            trait = ImplicitTrait(
                trait_type=trait_data.get("type", "preference"),
                description=trait_data.get("description", ""),
                evidence=[scene.id],
                strength=trait_data.get("strength", 0.5),
                last_updated=datetime.now()
            )
            
            if trait.description:
                self._update_or_add_trait(profile, trait)
        
        # Track the source scene
        if scene.id not in profile.source_memscenes:
            profile.source_memscenes.append(scene.id)
        
        profile.last_updated = datetime.now()
        
        return conflicts
    
    def _extract_profile_data(self, scene: MemScene) -> dict:
        """Extract profile data from a scene using LLM."""
        
        prompt = f"""Analyze this scene and extract user profile information.

SCENE THEME: {scene.theme}

SCENE SUMMARY:
{scene.summary}

IMPORTANT: For "attribute", you MUST use one of these standard categories:
- "name" (user's name)
- "age" (user's age)
- "location" (where user lives)
- "hometown" (where user is from)
- "occupation" (user's job/role)
- "company" (where user works)
- "diet" (eating habits, food restrictions)
- "health" (health conditions, medications)
- "exercise" (fitness routine, sports)
- "relationship" (marital status, partner)
- "family" (family members, family situation)
- "pet" (pets owned)
- "hobby" (hobbies, interests, activities)
- "music" (music preferences)
- "travel_plan" (upcoming trips, travel goals)
- "travel_history" (places visited)
- "education" (degrees, schools)
- "language" (languages spoken)
- "goal" (personal or career goals)
- "finance" (salary, budget, savings)
- "housing" (rent, own, living situation)
- "vehicle" (car, transport)
- "sleep" (sleep habits)
- "religion" (religious beliefs)
- "political_view" (political leanings)
If a fact doesn't fit any category, use a short snake_case name.
Use the SAME attribute for related facts (e.g., both "vegan" and "eats fish" → "diet").

Extract and respond with JSON:
{{
"explicit_facts": [
    {{
        "attribute": "category from list above",
        "value": "attribute value",
        "confidence": 0.0-1.0
    }}
],
"implicit_traits": [
    {{
        "type": "preference|habit|personality",
        "description": "description of the trait",
        "strength": 0.0-1.0
    }}
]
}}"""
        
        result = self.llm.generate_json(prompt, self.EXTRACTION_PROMPT)
        
        if "error" in result:
            return {"explicit_facts": [], "implicit_traits": []}
        
        return result
    
    def _update_or_add_trait(self, profile: UserProfile, new_trait: ImplicitTrait):
        """Update an existing trait or add a new one."""
        
        # Check for similar existing traits
        for existing in profile.implicit_traits:
            if self._traits_similar(existing, new_trait):
                # Update existing trait
                existing.strength = (existing.strength + new_trait.strength) / 2
                existing.evidence.extend(new_trait.evidence)
                existing.last_updated = datetime.now()
                return
        
        # Add as new trait
        profile.implicit_traits.append(new_trait)
    
    def _traits_similar(self, trait1: ImplicitTrait, trait2: ImplicitTrait) -> bool:
        """Check if two traits are semantically similar."""
        if trait1.trait_type != trait2.trait_type:
            return False
        
        # Simple word overlap check
        words1 = set(trait1.description.lower().split())
        words2 = set(trait2.description.lower().split())
        
        if not words1 or not words2:
            return False
        
        overlap = len(words1 & words2) / min(len(words1), len(words2))
        return overlap > 0.5
    
    def _check_semantic_conflict(self, profile: UserProfile, new_fact: ExplicitFact):
        """Check if a new fact semantically contradicts any existing active fact.
        
        BetterMemory: O(n) check — compares ONE new fact against existing facts.
        Uses embedding similarity to catch conflicts like 'vegan diet' vs 'eats fish'
        even when they have different attribute names.
        
        Returns:
            ConflictRecord if contradiction found, None otherwise
        """
        llm = get_llm_client()
        new_desc = f"{new_fact.attribute}: {new_fact.value}"
        
        try:
            new_emb = llm.embed(new_desc)
        except Exception:
            return None
        
        for attr, existing_fact in profile.explicit_facts.items():
            if not isinstance(existing_fact, ExplicitFact):
                continue
            if existing_fact.status == "deprecated":
                continue
            if attr == new_fact.attribute:
                continue  # Already handled by update_explicit_fact
            
            try:
                existing_desc = f"{existing_fact.attribute}: {existing_fact.value}"
                existing_emb = llm.embed(existing_desc)
                
                similarity = cosine_similarity(new_emb, existing_emb)
                
                if similarity > 0.75 and new_fact.value != existing_fact.value:
                    # Soft-delete the older fact
                    existing_fact.status = "deprecated"
                    
                    return ConflictRecord(
                        attribute=f"{attr} vs {new_fact.attribute}",
                        old_value=existing_fact.value,
                        new_value=new_fact.value,
                        old_source=existing_fact.source_memcell_id,
                        new_source=new_fact.source_memcell_id,
                        resolution="semantic_soft_delete"
                    )
            except Exception:
                continue
        
        return None
    
    def detect_conflicts(self, profile: UserProfile) -> list:
        """Analyze profile for potential conflicts using semantic similarity.
        
        BetterMemory: Uses embedding similarity to catch conflicts
        even when attribute names differ (e.g., 'diet' vs 'eating_habits').
        When a conflict is found, the older fact is soft-deleted.
        """
        conflicts = []
        
        # Check explicit facts for contradictions
        facts_list = list(profile.explicit_facts.items())
        active_facts = [(attr, fact) for attr, fact in facts_list 
                        if not isinstance(fact, ExplicitFact) or fact.status == "active"]
        
        for i, (attr1, fact1) in enumerate(active_facts):
            for attr2, fact2 in active_facts[i+1:]:
                if self._facts_contradict(fact1, fact2):
                    # Determine which is older (soft-delete the older one)
                    if fact1.timestamp <= fact2.timestamp:
                        old_fact, new_fact = fact1, fact2
                        old_attr, new_attr = attr1, attr2
                    else:
                        old_fact, new_fact = fact2, fact1
                        old_attr, new_attr = attr2, attr1
                    
                    # BetterMemory: Soft-delete the older fact
                    old_fact.status = "deprecated"
                    
                    conflict = ConflictRecord(
                        attribute=f"{old_attr} vs {new_attr}",
                        old_value=old_fact.value,
                        new_value=new_fact.value,
                        old_source=old_fact.source_memcell_id,
                        new_source=new_fact.source_memcell_id,
                        resolution="recency_soft_delete"
                    )
                    conflicts.append(conflict)
        
        return conflicts
    
    def _facts_contradict(self, fact1: ExplicitFact, fact2: ExplicitFact) -> bool:
        """Check if two facts contradict each other using semantic similarity.
        
        BetterMemory: Uses embedding-based similarity to detect semantic
        conflicts even when attribute names differ.
        E.g., 'follows vegan diet' vs 'started eating fish' → conflict detected.
        """
        # Quick check: exact attribute match with different values
        if fact1.attribute == fact2.attribute:
            return fact1.value != fact2.value
        
        # Semantic check: compare full fact descriptions via embeddings
        try:
            llm = get_llm_client()
            desc1 = f"{fact1.attribute}: {fact1.value}"
            desc2 = f"{fact2.attribute}: {fact2.value}"
            
            emb1 = llm.embed(desc1)
            emb2 = llm.embed(desc2)
            
            similarity = cosine_similarity(emb1, emb2)
            
            # High similarity (>0.75) means they're about the same topic
            # but different values → contradiction
            if similarity > 0.75 and fact1.value != fact2.value:
                return True
        except Exception:
            pass  # Fallback: no contradiction if embedding fails
        
        return False
    
    def get_profile_summary(self, profile: UserProfile = None) -> str:
        """Generate a human-readable profile summary with BetterMemory soft-delete."""
        
        if profile is None:
            profile = self.get_profile()
        
        lines = [f"User Profile (ID: {profile.user_id})", "=" * 40, ""]
        
        # Active explicit facts
        lines.append("EXPLICIT FACTS (Active):")
        active_facts = profile.get_active_facts()
        if active_facts:
            for attr, fact in active_facts.items():
                conf_str = f" (confidence: {fact.confidence:.1f})" if hasattr(fact, 'confidence') else ""
                lines.append(f"  - {attr}: {fact.value}{conf_str}")
        else:
            lines.append("  (none)")
        
        # BetterMemory: Show deprecated facts separately
        deprecated = {k: v for k, v in profile.explicit_facts.items() 
                     if isinstance(v, ExplicitFact) and v.status == "deprecated"}
        if deprecated:
            lines.append("")
            lines.append("DEPRECATED FACTS (Soft-deleted):")
            for attr, fact in deprecated.items():
                lines.append(f"  - {attr}: {fact.value} [DEPRECATED]")
        
        lines.append("")
        
        # Implicit traits by type
        lines.append("IMPLICIT TRAITS:")
        if profile.implicit_traits:
            for trait in profile.implicit_traits:
                lines.append(f"  - [{trait.trait_type}] {trait.description} (strength: {trait.strength:.2f})")
        else:
            lines.append("  (none)")
        
        lines.append("")
        
        # Conflict history
        if profile.conflict_history:
            lines.append("CONFLICT HISTORY:")
            for conflict in profile.conflict_history[-5:]:  # Last 5
                lines.append(f"  - {conflict.attribute}: {conflict.old_value} -> {conflict.new_value} ({conflict.resolution})")
        
        return "\n".join(lines)


class SemanticConsolidation:
    """
    Main class for Phase II: Semantic Consolidation.
    Orchestrates clustering and profile evolution.
    """
    
    def __init__(self):
        self.clusterer = IncrementalClusterer()
        self.profile_evolver = ProfileEvolver()
        self.vector_store = get_vector_store()
    
    def process_memcells(self, memcells: list, user_id: str = "default") -> dict:
        """
        Process a list of MemCells through semantic consolidation.
        
        Args:
            memcells: List of MemCell objects
            user_id: User ID for profile
            
        Returns:
            Dict with processing results
        """
        results = {
            "memcells_processed": 0,
            "new_scenes_created": 0,
            "scenes_updated": 0,
            "conflicts_detected": [],
            "scenes": [],
            "profile": None
        }
        
        processed_scenes = set()
        
        for memcell in memcells:
            # Cluster the MemCell
            scene, is_new = self.clusterer.cluster_memcell(memcell)
            
            if is_new:
                results["new_scenes_created"] += 1
            else:
                results["scenes_updated"] += 1
            
            results["memcells_processed"] += 1
            
            # Evolve profile from scene (if not already processed)
            if scene.id not in processed_scenes:
                conflicts = self.profile_evolver.evolve_from_scene(scene, user_id)
                results["conflicts_detected"].extend(conflicts)
                processed_scenes.add(scene.id)
                results["scenes"].append(scene)
        
        results["profile"] = self.profile_evolver.get_profile(user_id)
        
        return results
    
    def process_memcell(self, memcell: MemCell, user_id: str = "default") -> dict:
        """
        Process a single MemCell through semantic consolidation.
        
        Args:
            memcell: The MemCell to process
            user_id: User ID for profile
            
        Returns:
            Dict with processing results
        """
        return self.process_memcells([memcell], user_id)
    
    def get_all_scenes(self) -> list:
        """Get all MemScenes."""
        return self.vector_store.get_all_memscenes()
    
    def get_scene(self, scene_id: str) -> Optional[MemScene]:
        """Get a specific MemScene."""
        return self.vector_store.get_memscene(scene_id)
    
    def get_scene_memcells(self, scene_id: str) -> list:
        """Get all MemCells in a scene."""
        scene = self.vector_store.get_memscene(scene_id)
        if scene:
            return self.vector_store.get_memcells_by_ids(scene.memcell_ids)
        return []
    
    def get_profile(self, user_id: str = "default") -> UserProfile:
        """Get the user profile."""
        return self.profile_evolver.get_profile(user_id)
    
    def get_profile_summary(self, user_id: str = "default") -> str:
        """Get a human-readable profile summary."""
        profile = self.profile_evolver.get_profile(user_id)
        return self.profile_evolver.get_profile_summary(profile)
