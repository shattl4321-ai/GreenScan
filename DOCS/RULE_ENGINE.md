# RuleEngine и KnowledgeBase

## Разделение ответственности

| Слой | Вопрос |
|------|--------|
| **Vision** | Что видно на фотографии? |
| **RuleEngine** | Какие действия предложить пользователю? |
| **KnowledgeBase** | Какие конкретные рекомендации и продукты подобрать? |

## RuleEngine (`BACKEND/engine.py`)

### Вход

Словарь `lawn_state` — агрегированные признаки после Vision и `aggregate_results`.

Поля `is_lawn` и `lawn_confidence` **удаляются** до вызова RuleEngine.

### Выход `evaluate(lawn_state)`

Список строк — ID действий, например:

- `water_increase`
- `apply_fertilizer`
- `spot_weed_control`
- `full_weed_control`
- `overseed`
- `mow_lawn`
- `apply_fungicide`
- и др.

Порядок действий **не гарантирован** (используется `set`).

### Этапы evaluate

#### 1. Правила из `expert_rules.json`

Для каждого правила: если **все** условия из `conditions` истинны в `lawn_state`, добавляются `actions`.

Действие `apply_herbicide` **пропускается** (`continue`) — вместо него используется умная логика сорняков.

#### 2. Умная логика сорняков

Если `weed_presence = true`:

| `weed_density` | Действие |
|----------------|----------|
| `"low"` | `spot_weed_control` |
| `"medium"` или `"high"` | `full_weed_control` |
| иное / `null` | `spot_weed_control` |

#### 3. Кошение

`mow_lawn` добавляется **только** при `needs_mowing is True`.

### Правила в `expert_rules.json`

| Rule ID | Conditions | Actions |
|---------|------------|---------|
| `rule_dry_lawn` | `dryness` | `water_increase` |
| `rule_waterlogging` | `excess_moisture` | `water_reduce`, `improve_drainage` |
| `rule_pale_grass_spring` | `pale_grass`, `spring` | `apply_fertilizer` |
| `rule_slow_growth` | `slow_growth` | `apply_fertilizer`, `soil_improvement` |
| `rule_weeds_present` | `weed_presence` | `apply_herbicide` (пропускается) |
| `rule_fungal_signs` | `fungal_signs` | `apply_fungicide`, `water_reduce` |
| `rule_bare_spots` | `bare_spots` | `overseed` |
| `rule_thin_lawn` | `thin_lawn` | `overseed`, `apply_fertilizer` |
| `rule_compacted_soil` | `soil_compaction` | `aeration` |
| `rule_thatch` | `thatch_layer` | `dethatching` |
| `rule_moss` | `moss` | `improve_drainage`, `reduce_shade` |
| `rule_shade_problem` | `shade` | `reduce_shade`, `overseed` |
| `rule_heat_stress` | `heat_stress` | `water_increase`, `mowing_adjust` |

> Часть conditions (`excess_moisture`, `spring`, `slow_growth`, `soil_compaction`, `thatch_layer`, `moss`, `shade`, `heat_stress`) **отсутствует** в Vision-схеме. Эти правила в текущем MVP фактически не срабатывают.

> Правило `rule_moss` использует condition `moss`, а Vision возвращает `moss_presence` — **несовпадение имён**.

### Выход `enrich(actions, lawn_state)`

Делегирует в `KnowledgeBase.enrich_actions`. Возвращает список объектов рекомендаций.

## KnowledgeBase (`BACKEND/knowledge.py`)

### Загружаемые файлы

| Файл | Ключ JSON | Назначение |
|------|-----------|------------|
| `recommendations.json` | `recommendations` | Метаданные действий (id, name, description, category) |
| `fertilizers.json` | `fertilizers` | Удобрения для `apply_fertilizer` |
| `herbicides.json` | `herbicides` | Гербициды для `spot_weed_control` / `full_weed_control` |
| `grass_seeds.json` | `grass_seeds` | Семена для `overseed` |

Лимиты: `MAX_MATCHED = 3`, `MAX_FALLBACK = 2`.

### Обогащение по action ID

| Action ID | Knowledge source |
|-----------|-----------------|
| `apply_fertilizer` | `get_fertilizers()` |
| `spot_weed_control`, `full_weed_control` | `get_herbicides()` |
| `overseed` | `get_grass_seeds()` |
| остальные | без `knowledge_items` |

### Подбор гербицидов

Приоритет `commercial_product` с `parent_type_id` из `herb_selective_broadleaf` / `herb_selective_combined`. Неселективные препараты отфильтровываются.

## Примеры

### Пример 1: сухость

```text
Vision: dryness = true
    ↓
RuleEngine: rule_dry_lawn → water_increase
    ↓
KnowledgeBase: рекомендация «Увеличить полив»
```

### Пример 2: сорняки низкой плотности

```text
Vision: weed_presence = true, weed_density = "low"
    ↓
RuleEngine: spot_weed_control (умная логика)
    ↓
KnowledgeBase: подбор гербицидов (commercial_product приоритетнее)
```

### Пример 3: кошение

```text
Vision: needs_mowing = true
    ↓
RuleEngine: mow_lawn
```

`mow_lawn` **не добавляется**, если `needs_mowing = false`, даже при других проблемах.

## Доступные action ID (из `recommendations.json`)

`water_increase`, `water_reduce`, `apply_fertilizer`, `spot_weed_control`, `full_weed_control`, `apply_fungicide`, `overseed`, `aeration`, `dethatching`, `mow_lawn`, `mowing_adjust`, `improve_drainage`, `reduce_shade`, `soil_improvement`
