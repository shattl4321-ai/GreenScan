import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

KNOWLEDGE_DIR = Path(__file__).resolve().parent / "knowledge"

# Максимум knowledge_items при точном совпадении и при fallback
MAX_MATCHED = 3
MAX_FALLBACK = 2


class KnowledgeBase:
    """Загружает JSON-базы знаний и обогащает действия рекомендациями."""

    def __init__(self, knowledge_dir: Path | None = None):
        self._dir = Path(knowledge_dir) if knowledge_dir else KNOWLEDGE_DIR
        self.recommendations = self._load_list("recommendations.json", "recommendations")
        self.fertilizers = self._load_list("fertilizers.json", "fertilizers")
        self.herbicides = self._load_list("herbicides.json", "herbicides")
        self.grass_seeds = self._load_list("grass_seeds.json", "grass_seeds")

    def _load_list(self, filename: str, key: str) -> list:
        path = self._dir / filename
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            items = data.get(key, [])
            if not isinstance(items, list):
                logger.warning("%s: ключ '%s' не список, используем []", path, key)
                return []
            return items
        except FileNotFoundError:
            logger.warning("Файл базы знаний не найден: %s", path)
            return []
        except json.JSONDecodeError as e:
            logger.warning("Некорректный JSON в %s: %s", path, e)
            return []
        except OSError as e:
            logger.warning("Ошибка чтения %s: %s", path, e)
            return []

    def get_recommendation(self, action_id: str) -> dict:
        for rec in self.recommendations:
            if rec.get("id") == action_id:
                return dict(rec)
        return {
            "id": action_id,
            "name": action_id,
            "description": "Нет описания",
            "category": "other",
            "related_to": [],
        }

    def get_fertilizers(self, lawn_state: dict) -> list:
        active = _active_conditions(lawn_state)
        matched = []
        universal = []

        for item in self.fertilizers:
            if _has_avoid(item, active):
                continue
            applicable = item.get("applicable_conditions") or []
            if any(c in active for c in applicable):
                matched.append(item)
            elif "general_maintenance" in applicable or "maintenance" in (item.get("purpose") or []):
                universal.append(item)

        if matched:
            return matched[:MAX_MATCHED]
        return (universal or self.fertilizers)[:MAX_FALLBACK]

    def get_herbicides(self, lawn_state: dict) -> list:
        """Подбор гербицидов: сначала commercial_product, затем общая категория."""
        active = _active_conditions(lawn_state)
        weed_type = lawn_state.get("weed_type")
        density = lawn_state.get("weed_density")

        matched_products = []
        matched_types = []

        for item in self.herbicides:
            if _herbicide_unsafe_for_lawn(item):
                continue
            if _has_avoid(item, active):
                continue

            if item.get("product_type") == "commercial_product":
                score = _score_herbicide_product(item, weed_type, density, active)
                if score > 0:
                    matched_products.append((score, item))
            else:
                score = _score_herbicide_type(item, weed_type, density, active, lawn_state)
                if score > 0:
                    matched_types.append((score, item))

        matched_products.sort(key=lambda x: x[0], reverse=True)
        matched_types.sort(key=lambda x: x[0], reverse=True)

        # Нет продуктов → до 2 общих категорий
        if not matched_products:
            return [item for _, item in matched_types[:MAX_FALLBACK]]

        # Сначала до 2 commercial_product, затем до 1 общей категории
        result = [item for _, item in matched_products[:2]]
        if matched_types:
            result.append(matched_types[0][1])
        return result[:MAX_MATCHED]

    def get_grass_seeds(self, lawn_state: dict) -> list:
        matched = []
        universal = []

        for item in self.grass_seeds:
            purpose = item.get("purpose") or []
            shade_tol = item.get("shade_tolerance")

            if lawn_state.get("bare_spots") or lawn_state.get("thin_lawn"):
                if "repair" in purpose or "quick_cover" in purpose:
                    matched.append(item)
                    continue

            if lawn_state.get("shade") or lawn_state.get("moss_presence"):
                if "shade" in purpose or shade_tol == "high":
                    matched.append(item)
                    continue

            if item.get("type") == "mix" and (
                "general_use" in purpose or "repair" in purpose
            ):
                universal.append(item)

        if matched:
            return matched[:MAX_MATCHED]
        return (universal or self.grass_seeds)[:MAX_FALLBACK]

    def enrich_actions(self, actions: list, lawn_state: dict) -> list:
        result = []
        for action_id in actions:
            rec = self.get_recommendation(action_id)
            knowledge_items = self._knowledge_for_action(action_id, lawn_state)
            if knowledge_items:
                rec["knowledge_items"] = knowledge_items
            result.append(rec)
        return result

    def _knowledge_for_action(self, action_id: str, lawn_state: dict) -> list:
        if action_id == "apply_fertilizer":
            return self.get_fertilizers(lawn_state)
        if action_id in ("spot_weed_control", "full_weed_control"):
            return self.get_herbicides(lawn_state)
        if action_id == "overseed":
            return self.get_grass_seeds(lawn_state)
        return []


def _active_conditions(lawn_state: dict) -> set:
    """Условия, которые считаются активными по состоянию газона."""
    active = set()
    for key, value in (lawn_state or {}).items():
        if value is True:
            active.add(key)
        elif isinstance(value, str) and value:
            active.add(key)
            active.add(value)
    return active


def _has_avoid(item: dict, active: set) -> bool:
    avoid = item.get("avoid_conditions") or []
    return any(c in active for c in avoid)


SAFE_LAWN_PARENTS = frozenset({
    "herb_selective_broadleaf",
    "herb_selective_combined",
})


def _herbicide_unsafe_for_lawn(item: dict) -> bool:
    """Неселективные и опасные для газона препараты/категории."""
    if item.get("category") == "non_selective":
        return True
    if item.get("parent_type_id") == "herb_non_selective":
        return True
    if item.get("id") in ("herb_non_selective", "herb_prod_agrokiller"):
        return True
    return False


def _is_safe_lawn_product(item: dict) -> bool:
    if item.get("product_type") != "commercial_product":
        return False
    if _herbicide_unsafe_for_lawn(item):
        return False
    parent = item.get("parent_type_id")
    return parent in SAFE_LAWN_PARENTS and item.get("category") == "selective"


def _score_herbicide_product(item: dict, weed_type, density, active: set) -> int:
    if not _is_safe_lawn_product(item):
        return 0

    parent = item.get("parent_type_id")
    targets = item.get("target_weeds") or []
    applicable = item.get("applicable_conditions") or []
    score = 0

    # Злаковые сорняки: не рекомендовать broadleaf-препараты
    if weed_type == "grass":
        if "grass_weeds" in targets or "grass" in targets:
            score += 3
        return score

    if weed_type == "broadleaf":
        if parent == "herb_selective_broadleaf":
            score += 4
        elif parent == "herb_selective_combined":
            score += 3
        elif "broadleaf" in targets:
            score += 2

    elif weed_type == "mixed":
        if parent == "herb_selective_combined":
            score += 4
        elif parent == "herb_selective_broadleaf":
            score += 3
        elif "broadleaf" in targets or "some_grasses" in targets:
            score += 2

    else:
        # weed_type отсутствует/null — для точечной работы на газоне
        # предлагаем безопасные селективные commercial_product
        if density == "low" and parent in SAFE_LAWN_PARENTS:
            score += 3
        elif parent in SAFE_LAWN_PARENTS:
            score += 2
        elif "broadleaf" in targets:
            score += 1

    if any(c in active for c in applicable):
        score += 1

    if density == "low" and parent in SAFE_LAWN_PARENTS:
        score += 1

    return score


def _score_herbicide_type(item: dict, weed_type, density, active: set, lawn_state: dict) -> int:
    item_id = item.get("id")
    targets = item.get("target_weeds") or []
    applicable = item.get("applicable_conditions") or []
    score = 0

    if lawn_state.get("moss_presence") and "moss" in targets:
        score += 4

    if weed_type == "grass":
        if item_id == "herb_grass_specific" or "grass_weeds" in targets:
            score += 4
        # не поднимаем broadleaf-категории при злаковых сорняках
        return score

    if weed_type == "broadleaf":
        if item_id == "herb_selective_broadleaf":
            score += 4
        elif item_id == "herb_selective_combined":
            score += 2
        elif item_id == "herb_spot_treatment" and density == "low":
            score += 5
        elif item_id == "herb_post_emergent":
            score += 1

    elif weed_type == "mixed":
        if item_id == "herb_selective_combined":
            score += 4
        elif item_id == "herb_selective_broadleaf":
            score += 2
        elif item_id == "herb_spot_treatment" and density == "low":
            score += 3

    else:
        # weed_type неизвестен
        if density == "low":
            if item_id == "herb_spot_treatment":
                score += 5
            elif item_id == "herb_selective_broadleaf":
                score += 2
        else:
            if item_id in ("herb_selective_broadleaf", "herb_post_emergent"):
                score += 2
            elif item_id == "herb_spot_treatment":
                score += 1

    if density in ("medium", "high") and (
        "existing_weeds" in targets or item_id == "herb_post_emergent"
    ):
        score += 1

    if any(c in active for c in applicable):
        score += 1

    return score
