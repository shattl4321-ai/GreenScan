import json
import logging
from pathlib import Path

from knowledge import KnowledgeBase

logger = logging.getLogger(__name__)

RULES_PATH = Path(__file__).resolve().parent / "knowledge" / "expert_rules.json"


def _load_rules(path: Path) -> list:
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        rules = data.get("rules", [])
        return rules if isinstance(rules, list) else []
    except FileNotFoundError:
        logger.warning("Файл правил не найден: %s", path)
        return []
    except json.JSONDecodeError as e:
        logger.warning("Некорректный JSON в %s: %s", path, e)
        return []
    except OSError as e:
        logger.warning("Ошибка чтения %s: %s", path, e)
        return []


class RuleEngine:
    def __init__(self):
        self.kb = KnowledgeBase()
        self.rules = _load_rules(RULES_PATH)

    def evaluate(self, lawn_state: dict):
        actions = set()

        # --- 1. БАЗОВЫЕ ПРАВИЛА ---
        for rule in self.rules:
            if all(cond in lawn_state and lawn_state[cond] for cond in rule["conditions"]):
                for action in rule["actions"]:
                    if action == "apply_herbicide":
                        continue
                    actions.add(action)

        # --- 2. УМНАЯ ЛОГИКА СОРНЯКОВ ---
        if lawn_state.get("weed_presence"):
            density = lawn_state.get("weed_density")

            if density == "low":
                actions.add("spot_weed_control")
            elif density in ["medium", "high"]:
                actions.add("full_weed_control")
            else:
                actions.add("spot_weed_control")

        # --- 3. КОШЕНИЕ — только при needs_mowing ---
        if lawn_state.get("needs_mowing") is True:
            actions.add("mow_lawn")

        return list(actions)

    def enrich(self, actions, lawn_state):
        return self.kb.enrich_actions(actions, lawn_state)
