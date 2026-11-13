"""PinForge AI — Autonomous Agentic Swarm System.

Provides a multi-agent swarm architecture for Pinterest automation:
- ScoutAgent: Market & trend intelligence
- CreativeDirectorAgent: Visual strategy & layout selection
- CopywriterAgent: Conversion copywriting & Save-First SEO
- VisionCriticAgent: Multi-modal visual inspection & self-healing reflection
- PublisherAgent: Jittered algorithmic Pinterest dispatcher
- GrowthAnalystAgent: Closed-loop analytics & memory evolution
- SwarmCoordinator: End-to-end swarm lifecycle orchestrator
"""

from .models import (
    SwarmState,
    ProductCandidate,
    CreativeStrategy,
    PinCopyDraft,
    VisionCriticEvaluation,
    AgentLogEntry,
    MemoryInsights,
)
from .memory import SwarmMemory
from .scout_agent import ScoutAgent
from .creative_agent import CreativeDirectorAgent
from .copywriter_agent import CopywriterAgent
from .critic_agent import VisionCriticAgent
from .publisher_agent import PublisherAgent
from .analyst_agent import GrowthAnalystAgent
from .swarm_coordinator import SwarmCoordinator

__all__ = [
    "SwarmCoordinator",
    "SwarmState",
    "SwarmMemory",
    "ScoutAgent",
    "CreativeDirectorAgent",
    "CopywriterAgent",
    "VisionCriticAgent",
    "PublisherAgent",
    "GrowthAnalystAgent",
    "ProductCandidate",
    "CreativeStrategy",
    "PinCopyDraft",
    "VisionCriticEvaluation",
    "AgentLogEntry",
    "MemoryInsights",
]
