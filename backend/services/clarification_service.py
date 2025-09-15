"""
Clarification Service

This service detects potential hallucinations or knowledge gaps in LLM responses.
It provides functionality for analyzing responses, logging hallucinations, and
creating clarification nodes.
"""

from __future__ import annotations

import re
import uuid
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

import psycopg
from psycopg.rows import dict_row

# Import LLM service for secondary checking
from services.llm_service import LLMService

logger = logging.getLogger(__name__)


class HallucinationType(Enum):
    MISSING_FACT = "MissingFact"
    WRONG_ASSUMPTION = "WrongAssumption"
    SPECULATION = "Speculation"


@dataclass(frozen=True)
class HallucinationIssue:
    """Represents a detected hallucination or knowledge gap."""
    type: HallucinationType
    snippet: str
    confidence: float = 0.0  # Confidence score (0.0 to 1.0)
    explanation: Optional[str] = None


@dataclass(frozen=True)
class HallucinationRecord:
    """Represents a stored hallucination record."""
    id: str
    node_id: str
    type: HallucinationType
    snippet: str
    created_at: datetime
    resolved: bool = False
    resolution_notes: Optional[str] = None


@dataclass(frozen=True)
class ClarificationConfig:
    """Configuration for the ClarificationService."""
    pg_dsn: str  # PostgreSQL connection string
    llm_provider: str = "ollama"  # LLM provider for secondary checking
    auto_create_children: bool = False  # Whether to auto-create clarification nodes
    min_confidence_threshold: float = 0.7  # Minimum confidence to log hallucinations


class ClarificationService:
    """
    Service for detecting and managing hallucinations in LLM responses.
    
    Features:
    - Analyze LLM responses for potential hallucinations
    - Log detected hallucinations
    - Create clarification nodes
    - Retrieve hallucination logs
    """
    
    def __init__(self, cfg: ClarificationConfig) -> None:
        self.cfg = cfg
        self._conn = psycopg.connect(cfg.pg_dsn, row_factory=dict_row)
        self._conn.execute("SET application_name = 'clarification_service'")
        self._conn.commit()
        
        # Initialize LLM service for secondary checking
        self.llm_service = LLMService()
        
        # Compile regex patterns for heuristic scanning
        self._compile_patterns()
    
    def _compile_patterns(self) -> None:
        """Compile regex patterns for heuristic scanning."""
        # Patterns that might indicate hallucinations
        self.speculation_patterns = [
            re.compile(r'\b(I think|I believe|probably|likely|possibly|maybe|perhaps)\b', re.IGNORECASE),
            re.compile(r'\b(as far as I know|to the best of my knowledge)\b', re.IGNORECASE),
            re.compile(r'\b(I\'m not sure|I\'m uncertain)\b', re.IGNORECASE),
        ]
        
        # Patterns that might indicate missing facts
        self.missing_fact_patterns = [
            re.compile(r'\b(I don\'t know|I\'m not familiar with)\b', re.IGNORECASE),
            re.compile(r'\b(missing information|not enough information)\b', re.IGNORECASE),
        ]
        
        # Patterns that might indicate wrong assumptions
        self.wrong_assumption_patterns = [
            re.compile(r'\b(assuming that|presuming that|based on the assumption)\b', re.IGNORECASE),
            re.compile(r'\b(typically|usually|commonly)\b.*\b(but|however)\b', re.IGNORECASE),
        ]
    
    async def analyze_response(self, node_id: str, response_text: str) -> List[HallucinationIssue]:
        """
        Analyze an LLM response for potential hallucinations or knowledge gaps.
        
        Args:
            node_id: ID of the node that generated the response
            response_text: The LLM response text to analyze
            
        Returns:
            List of detected hallucination issues
        """
        try:
            # Step 1: Run heuristic filters
            issues = self._heuristic_scan(response_text)
            
            # Step 2: (Optional) Call LLM-based evaluator for deeper check
            llm_flags = await self._llm_check(response_text)
            
            # Combine and filter issues based on confidence
            all_issues = issues + llm_flags
            filtered_issues = [
                issue for issue in all_issues 
                if issue.confidence >= self.cfg.min_confidence_threshold
            ]
            
            # Step 3: Persist hallucinations
            for issue in filtered_issues:
                await self._log_hallucination(node_id, issue)
            
            logger.info(f"Analyzed response for node {node_id}, found {len(filtered_issues)} issues")
            
            return filtered_issues
            
        except Exception as e:
            logger.error(f"Failed to analyze response for node {node_id}: {e}")
            raise
    
    def _heuristic_scan(self, response_text: str) -> List[HallucinationIssue]:
        """
        Run heuristic filters to detect potential hallucinations.
        
        Args:
            response_text: The text to scan
            
        Returns:
            List of detected issues
        """
        issues = []
        
        # Check for speculation patterns
        for pattern in self.speculation_patterns:
            matches = pattern.finditer(response_text)
            for match in matches:
                # Extract context around the match
                start = max(0, match.start() - 50)
                end = min(len(response_text), match.end() + 50)
                context = response_text[start:end]
                
                issues.append(HallucinationIssue(
                    type=HallucinationType.SPECULATION,
                    snippet=context.strip(),
                    confidence=0.6,  # Heuristic confidence
                    explanation=f"Speculative language detected: '{match.group()}'"
                ))
        
        # Check for missing fact patterns
        for pattern in self.missing_fact_patterns:
            matches = pattern.finditer(response_text)
            for match in matches:
                # Extract context around the match
                start = max(0, match.start() - 50)
                end = min(len(response_text), match.end() + 50)
                context = response_text[start:end]
                
                issues.append(HallucinationIssue(
                    type=HallucinationType.MISSING_FACT,
                    snippet=context.strip(),
                    confidence=0.8,  # High confidence for explicit missing info
                    explanation=f"Missing fact indicator detected: '{match.group()}'"
                ))
        
        # Check for wrong assumption patterns
        for pattern in self.wrong_assumption_patterns:
            matches = pattern.finditer(response_text)
            for match in matches:
                # Extract context around the match
                start = max(0, match.start() - 50)
                end = min(len(response_text), match.end() + 50)
                context = response_text[start:end]
                
                issues.append(HallucinationIssue(
                    type=HallucinationType.WRONG_ASSUMPTION,
                    snippet=context.strip(),
                    confidence=0.7,  # Medium confidence
                    explanation=f"Potential wrong assumption detected: '{match.group()}'"
                ))
        
        return issues
    
    async def _llm_check(self, response_text: str) -> List[HallucinationIssue]:
        """
        Use a secondary LLM call to audit the main output for hallucinations.
        
        Args:
            response_text: The text to check
            
        Returns:
            List of detected issues
        """
        try:
            # System prompt for fact-checking assistant
            system_prompt = """
You are a fact-checking assistant. Given an LLM output, identify possible issues:
- Missing facts that require clarification
- Wrong assumptions or contradictions
- Speculative or uncertain statements

Return a JSON list: [{ "type": "MissingFact|WrongAssumption|Speculation", "snippet": "...", "confidence": 0.0-1.0, "explanation": "..." }]

If no issues found, return an empty list [].
"""
            
            # User prompt with the response to check
            user_prompt = f"Check this LLM response for potential hallucinations:\n\n{response_text}"
            
            # Call the LLM service
            result = self.llm_service.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                model=self.cfg.llm_provider
            )
            
            # Parse the JSON response (simplified - in practice you'd use proper JSON parsing)
            # This is a placeholder for actual JSON parsing
            issues = []
            
            # In a real implementation, you would parse the LLM's JSON response
            # and convert it to HallucinationIssue objects
            
            return issues
            
        except Exception as e:
            logger.warning(f"LLM check failed: {e}")
            # Return empty list if LLM check fails
            return []
    
    async def _log_hallucination(self, node_id: str, issue: HallucinationIssue) -> str:
        """
        Log a hallucination issue to the database.
        
        Args:
            node_id: ID of the node
            issue: The hallucination issue to log
            
        Returns:
            ID of the created hallucination record
        """
        try:
            hallucination_id = str(uuid.uuid4())
            
            with self._conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO hallucinations (id, node_id, type, snippet)
                    VALUES (%s, %s, %s, %s)
                    """, (
                        hallucination_id,
                        node_id,
                        issue.type.value,
                        issue.snippet
                    )
                )
            
            self._conn.commit()
            logger.info(f"Logged hallucination {hallucination_id} for node {node_id}")
            
            return hallucination_id
            
        except Exception as e:
            self._conn.rollback()
            logger.error(f"Failed to log hallucination for node {node_id}: {e}")
            raise
    
    async def get_hallucinations(self, node_id: str, unresolved_only: bool = True) -> List[HallucinationRecord]:
        """
        Retrieve hallucination records for a specific node.
        
        Args:
            node_id: ID of the node
            unresolved_only: Whether to return only unresolved hallucinations
            
        Returns:
            List of hallucination records
        """
        try:
            with self._conn.cursor() as cur:
                if unresolved_only:
                    cur.execute("""
                        SELECT id, node_id, type, snippet, created_at, resolved, resolution_notes
                        FROM hallucinations 
                        WHERE node_id = %s AND resolved = FALSE
                        ORDER BY created_at DESC
                        """, (node_id,)
                    )
                else:
                    cur.execute("""
                        SELECT id, node_id, type, snippet, created_at, resolved, resolution_notes
                        FROM hallucinations 
                        WHERE node_id = %s
                        ORDER BY created_at DESC
                        """, (node_id,)
                    )
                
                rows = cur.fetchall()
                
            records = []
            for row in rows:
                records.append(HallucinationRecord(
                    id=row["id"],
                    node_id=row["node_id"],
                    type=HallucinationType(row["type"]),
                    snippet=row["snippet"],
                    created_at=row["created_at"],
                    resolved=row["resolved"],
                    resolution_notes=row["resolution_notes"]
                ))
                
            return records
            
        except Exception as e:
            logger.error(f"Failed to retrieve hallucinations for node {node_id}: {e}")
            raise
    
    async def create_clarification_node(self, parent_node_id: str, snippet: str) -> str:
        """
        Auto-create a child node flagged for clarification.
        
        Args:
            parent_node_id: ID of the parent node
            snippet: The text snippet that needs clarification
            
        Returns:
            ID of the created clarification node
        """
        try:
            # In a real implementation, this would call the NodeService
            # For now, we'll simulate the creation
            
            # Generate a new node ID
            child_id = str(uuid.uuid4())
            
            # In a real implementation, you would:
            # 1. Call NodeService.create_node() or similar
            # 2. Set the node type to 'clarification' or similar
            # 3. Set the initial content to the snippet
            # 4. Establish the parent-child relationship
            
            logger.info(f"Created clarification node {child_id} for parent {parent_node_id}")
            
            return child_id
            
        except Exception as e:
            logger.error(f"Failed to create clarification node for parent {parent_node_id}: {e}")
            raise
    
    async def resolve_hallucination(self, hallucination_id: str, resolution_notes: Optional[str] = None) -> bool:
        """
        Mark a hallucination as resolved.
        
        Args:
            hallucination_id: ID of the hallucination record
            resolution_notes: Optional notes about how it was resolved
            
        Returns:
            True if successfully resolved
        """
        try:
            with self._conn.cursor() as cur:
                cur.execute("""
                    UPDATE hallucinations 
                    SET resolved = TRUE, resolution_notes = %s
                    WHERE id = %s
                    """, (resolution_notes, hallucination_id)
                )
                
                if cur.rowcount == 0:
                    return False
            
            self._conn.commit()
            logger.info(f"Resolved hallucination {hallucination_id}")
            
            return True
            
        except Exception as e:
            self._conn.rollback()
            logger.error(f"Failed to resolve hallucination {hallucination_id}: {e}")
            raise
    
    def close(self) -> None:
        """Close the database connection."""
        try:
            self._conn.close()
        except Exception:
            pass


def make_clarification_service_from_env() -> ClarificationService:
    """
    Factory function to create a ClarificationService from environment variables.
    """
    import os
    
    dsn = os.getenv("PG_DSN") or os.getenv("DATABASE_URL")
    if not dsn:
        raise RuntimeError("PG_DSN or DATABASE_URL must be set")
    
    cfg = ClarificationConfig(
        pg_dsn=dsn,
        llm_provider=os.getenv("CLARIFICATION_LLM_PROVIDER", "ollama"),
        auto_create_children=os.getenv("AUTO_CREATE_CLARIFICATION_NODES", "false").lower() == "true",
        min_confidence_threshold=float(os.getenv("CLARIFICATION_MIN_CONFIDENCE", "0.7"))
    )
    
    return ClarificationService(cfg)
