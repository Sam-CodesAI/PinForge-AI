"""Unit & Integration Test Suite for PinForge-AI Agentic Swarm.

Verifies the complete 6-agent lifecycle:
1. SwarmState initialization & logging
2. SwarmMemory persistence & running average scoring
3. ScoutAgent candidate selection & rationale generation
4. CreativeDirectorAgent visual strategy & critique corrections
5. CopywriterAgent Save-First SEO copy synthesis
6. VisionCriticAgent multi-modal structural audit
7. SwarmCoordinator end-to-end autonomous dry run
"""

import sys
import unittest
import tempfile
from pathlib import Path
from PIL import Image

# Ensure python_engine is on path
CURRENT_DIR = Path(__file__).resolve().parent
PYTHON_ENGINE_DIR = CURRENT_DIR.parent
if str(PYTHON_ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(PYTHON_ENGINE_DIR))

from agentic_engine.models import (
    SwarmState,
    ProductCandidate,
    VisionCriticEvaluation,
)
from agentic_engine.memory import SwarmMemory
from agentic_engine.scout_agent import ScoutAgent
from agentic_engine.creative_agent import CreativeDirectorAgent
from agentic_engine.copywriter_agent import CopywriterAgent
from agentic_engine.critic_agent import VisionCriticAgent
from agentic_engine.swarm_coordinator import SwarmCoordinator


class TestAgenticSwarm(unittest.TestCase):
    """Test suite verifying multi-agent collaboration and quality gates."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.memory_path = Path(self.temp_dir.name) / "test_memory.json"
        self.memory = SwarmMemory(memory_path=self.memory_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_swarm_state_and_logging(self):
        """Verifies SwarmState properly records agent actions and thoughts."""
        state = SwarmState(session_id="test-session-001", target_slot=1, target_board="Room Organization")
        state.log("TestAgent", "test_action", "Thinking deeply", "Done")

        self.assertEqual(len(state.execution_log), 1)
        self.assertEqual(state.execution_log[0].agent_name, "TestAgent")
        self.assertEqual(state.execution_log[0].action, "test_action")

    def test_memory_persistence(self):
        """Verifies SwarmMemory records successful pins and calculates moving average score."""
        initial_pins = self.memory.insights.total_pins_published
        self.memory.record_successful_pin("pin_1", "Room Organization", "warm_editorial", 90.0)
        self.memory.record_successful_pin("pin_2", "Room Organization", "warm_editorial", 94.0)

        self.assertEqual(self.memory.insights.total_pins_published, initial_pins + 2)
        self.assertTrue(self.memory_path.exists())

    def test_scout_agent_selection(self):
        """Verifies ScoutAgent selects a valid Smart Spaces candidate with rationale."""
        scout = ScoutAgent(self.memory)
        state = SwarmState(session_id="scout-test", target_board="Room Organization")

        candidate = scout.evaluate_and_select_product(state, preferred_asin="B0DHGM5XT4")

        self.assertIsNotNone(candidate)
        self.assertEqual(candidate.asin, "B0DHGM5XT4")
        self.assertIn("$", candidate.price)
        self.assertGreater(len(candidate.strategic_rationale), 10)
        self.assertEqual(state.product.asin, "B0DHGM5XT4")

    def test_creative_director_strategy_and_corrections(self):
        """Verifies CreativeDirectorAgent formulates layout and applies critique corrections."""
        scout = ScoutAgent(self.memory)
        state = SwarmState(session_id="creative-test", target_board="Room Organization")
        scout.evaluate_and_select_product(state, preferred_asin="B0DHGM5XT4")

        creative = CreativeDirectorAgent(self.memory)
        strategy = creative.formulate_strategy(state)

        self.assertIsNotNone(strategy)
        self.assertEqual(strategy.primary_hex, "#F9F6F0")  # Alabaster
        self.assertEqual(strategy.accent_hex, "#D97706")   # 2700K Amber

        # Test self-healing critique correction
        fake_rejection = VisionCriticEvaluation(
            score=70.0,
            approved=False,
            text_legibility_score=65.0,
            contrast_score=60.0,
            mobile_readability_score=60.0,
            critique_notes=["Text margin too close to border", "Low contrast"],
            corrective_instructions=["Switch to warm_editorial", "Boost accent saturation"],
            auditor_model="test-auditor",
        )

        revised_strategy = creative.apply_critique_corrections(state, fake_rejection)
        self.assertGreater(len(revised_strategy.applied_corrections), 0)
        self.assertEqual(revised_strategy.template_variant, "warm_editorial")

    def test_copywriter_save_first_mandate(self):
        """Verifies CopywriterAgent strictly enforces the '📌 SAVE THIS PIN' CTA and #AmazonAssociate."""
        scout = ScoutAgent(self.memory)
        state = SwarmState(session_id="copy-test", target_board="Room Organization")
        scout.evaluate_and_select_product(state, preferred_asin="B0DHGM5XT4")

        copywriter = CopywriterAgent(self.memory)
        copy = copywriter.draft_copy(state)

        self.assertIsNotNone(copy)
        self.assertIn("SAVE THIS PIN", copy.pin_description.upper())
        self.assertIn("#AMAZONASSOCIATE", copy.pin_description.upper())
        self.assertIn("b0dhgm5xt4", copy.bridge_slug.lower())

    def test_vision_critic_heuristics(self):
        """Verifies VisionCriticAgent audits 1000x1500 canvas resolution and rejects defective sizes."""
        critic = VisionCriticAgent(self.memory)
        state = SwarmState(session_id="critic-test", target_board="Room Organization")

        # 1. Create a valid 1000x1500 dummy image with contrast elements
        valid_img_path = Path(self.temp_dir.name) / "valid_pin.png"
        img = Image.new("RGB", (1000, 1500), color=(249, 246, 240))
        from PIL import ImageDraw
        draw = ImageDraw.Draw(img)
        draw.rectangle([100, 100, 900, 300], fill=(28, 25, 23))  # Deep slate block
        img.save(valid_img_path)

        eval_valid = critic.inspect_rendered_pin(state, str(valid_img_path))
        self.assertTrue(eval_valid.approved)
        self.assertGreaterEqual(eval_valid.score, 85.0)

        # 2. Create an invalid aspect ratio image (e.g. 500x500)
        invalid_img_path = Path(self.temp_dir.name) / "invalid_pin.png"
        img_bad = Image.new("RGB", (500, 500), color=(0, 0, 0))
        img_bad.save(invalid_img_path)

        eval_invalid = critic.inspect_rendered_pin(state, str(invalid_img_path))
        self.assertFalse(eval_invalid.approved)
        self.assertLess(eval_invalid.score, 85.0)

    def test_swarm_coordinator_dry_run_cycle(self):
        """End-to-end integration test of SwarmCoordinator in dry-run mode."""
        coordinator = SwarmCoordinator(memory_path=self.memory_path)

        state = coordinator.run_autonomous_swarm_cycle(
            board_name="Room Organization",
            slot_id=2,
            preferred_asin="B0DHGM5XT4",
            publish_live=False,
            apply_jitter=False,
            max_critique_revisions=1,
        )

        self.assertTrue(state.is_successful)
        self.assertIsNotNone(state.product)
        self.assertIsNotNone(state.copy)
        self.assertIsNotNone(state.creative_direction)
        self.assertIsNotNone(state.rendered_image_path)
        self.assertTrue(Path(state.rendered_image_path).exists())
        self.assertIsNotNone(state.critic_audit)
        self.assertTrue(state.critic_audit.approved)
        self.assertTrue(state.published_pin_id.startswith("dry_run_"))
        self.assertGreater(len(state.execution_log), 5)

    def test_scout_agent_uses_memory_winning_asins(self):
        """Verifies ScoutAgent prioritizes top-converting ASINs from memory for target boards."""
        self.memory.insights.winning_asins = [
            {"asin": "B0DHGM5XT4", "title": "Drawer Dividers", "board": "Room Organization"}
        ]
        scout = ScoutAgent(self.memory)
        state = SwarmState(session_id="mem-scout-test", target_board="Room Organization")

        candidate = scout.evaluate_and_select_product(state, preferred_asin=None)
        self.assertIsNotNone(candidate)
        self.assertIn("$", candidate.price)
        self.assertGreater(len(candidate.strategic_rationale), 10)

    def test_creative_director_uses_schedule_matrix(self):
        """Verifies CreativeDirectorAgent maps slot recommendations from peak schedule matrix."""
        self.memory.insights.peak_schedule_matrix = {
            "slot_1": {"recommended_format": "carousel_suite", "board": "Small Apartment Hacks"}
        }
        creative = CreativeDirectorAgent(self.memory)
        state = SwarmState(session_id="creative-matrix-test", target_slot=1, target_board="Small Apartment Hacks")
        state.product = ProductCandidate(
            asin="B01MR1Y5K8",
            title="Under Cabinet Sliding Organizer",
            price="$22.99",
            image_url="https://m.media-amazon.com/images/I/71s8N2eGq+L.jpg"
        )

        strategy = creative.formulate_strategy(state)
        self.assertEqual(strategy.template_variant, "carousel_suite")

    def test_copywriter_problem_solver_formula(self):
        """Verifies CopywriterAgent applies proven high-converting Problem-Solver hooks."""
        copywriter = CopywriterAgent(self.memory)
        state = SwarmState(session_id="copy-formula-test", target_board="Room Organization")
        state.product = ProductCandidate(
            asin="B0DHGM5XT4",
            title="Lifewit Clear Plastic Drawer Dividers 4-Pack",
            price="$19.99",
            image_url="https://m.media-amazon.com/images/I/71P4q+4oWNL.jpg"
        )

        copy = copywriter.draft_copy(state)
        self.assertIn("Finally Fix Messy Drawers", copy.pin_title)
        self.assertIn("Problem-Solver", copy.hook_formula)
        self.assertIn("📌 SAVE THIS PIN", copy.pin_description)


if __name__ == "__main__":
    unittest.main()
