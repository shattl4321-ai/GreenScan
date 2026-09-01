# GreenScan — Отчёт о редизайне UI (2026 SaaS AI)

**Дата:** 2026-07-14
**Задача:** Полный редизайн интерфейса GreenScan (Senior Product Designer уровень), без изменений backend, API и JS-логики.

---

## 1. Что изменилось

### До (было)
- Glassmorphism 2018: полупрозрачные карточки с blur на тёмно-зелёном radial-gradient
- Мелкая типографика: 0.66–0.86 rem, system font (Segoe UI)
- Эмодзи-иконки (🌿 📷 💧 🛡️) выглядят как Windows-стикеры
- Плотный grid с state-chip-ами (2 колонки мелких пилюль)
- Drop-zone 240px с тонкой пунктирной рамкой
- «Админский» look — ощущение курсовой работы
- Все фичи в одном ряду, нет визуального «вау-момента»

### После (стало)
- **Чистый modern SaaS** в духе Perplexity / Vercel / Linear
- **Inter** (UI) + **Instrument Serif** (display-элементы) с Google Fonts
- Inline SVG-иконки (15+ штук) — стиль Lucide, толщина 1.75 px
- Крупная типографика: H1 до 2.625 rem, body 1 rem (на 15–30% крупнее)
- **Hero-блок** с badge, заголовком, подзаголовком и 4 фичами с SVG-иконками
- **Drop-zone 280px** с большой upload-иконкой, при drag-over — glow + scale
- Mesh-gradient фон с плавающими blob-ами (медленная анимация 28–40s)
- Премиальные карточки с мягкими тенями, скруглением 16–24 px
- Вертикальный стек state-chips с иконкой, label, value
- Аккордеон рекомендаций с плавной анимацией раскрытия
- Полный адаптив: desktop / tablet / mobile (3 breakpoint)

---

## 2. Какие файлы изменены

| Файл | Действие | Размер |
|---|---|---|
| `index.html` | **Полностью переписан** | 180 → 270 строк |
| `FRONTEND/styles.css` | **Полностью переписан** | 1091 → 1320 строк |
| `FRONTEND/app.js` | **Не изменён** (994 строки как было) | 994 строки |
| `BACKEND/*` | **Не изменён** | как было |
| `FRONTEND/assets/photo-guide.webp` | Не создан (использован SVG-fallback) | — |
| `FRONTEND/assets/grass-background.webp` | Не создан (использован CSS mesh-gradient) | — |

### Совместимость
- ✅ **Все 38 ID-хуков сохранены** (проверено: `startLayout`, `resultsLayout`, `dropzone`, `fileInput`, `previews`, `previewsCompact`, `counterValue`, `analyzeBtn`, `clearBtn`, `loadingOverlay`, `loadingStep`, `alert`, `toast`, `stateGrid`, `summaryBox`, `recommendations`, `expandAllBtn`, `collapseAllBtn`, `analysisStatusPill`, `analysisStatusText`, `modelName`, `newAnalysisBtn`, `downloadReportBtn`, `openGuideBtn`, `guideModal`, `guideBodyStart`, `guideBodyModal`, `guideTemplate`, `workspace` и др.)
- ✅ **Все обязательные классы** для JS: `app--start/--loading/--results`, `is-open`, `is-dragover`, `is-loading`, `is-done`, `is-visible`, `has-image`
- ✅ **Все `data-*` атрибуты**: `data-remove`, `data-close-modal`, `data-guide-image`, `data-guide-css`
- ✅ **Структура `#guideTemplate`** сохранена (JS монтирует через cloneNode)
- ✅ **API-контракт** `POST /analyze-photo` не тронут
- ✅ **Логика аккордеона** работает через класс `is-open`, переключаемый JS

---

## 3. CSS-эффекты (новые)

### Дизайн-токены (CSS-переменные)
- **Палитра** (light theme "well-kept lawn"): bg `#f6f8f4`, accent-600 `#2d7a4d`, ink-900 `#0f2419`, плюс ok/warn/bad/info тона
- **Spacing scale**: 4/8/12/16/20/24/32/40/56/72/96 px
- **Радиусы**: 6/10/16/24/32 px + pill
- **Тени**: 5 уровней (xs, sm, base, lg, xl) + `shadow-glow` (зелёное свечение)
- **Easing**: `--ease` (cubic-bezier 0.22,1,0.36,1) + `--ease-spring` (0.34,1.56,0.64,1) для spring-эффектов
- **Длительности**: 180/240/360/600 ms

### Mesh-gradient фон
3 больших blob-а (50–60vw) с `filter: blur(80px)` плавают с разными easing-кривыми 28–40s. Заменяет файловое фоновое изображение.

### Glass / Glassmorphism убран
Сознательно — перешёл на чистый flat design с мягкими тенями. Это даёт ощущение «современного SaaS», а не «2018 glass trend».

### Кнопки
- **Primary**: gradient 180° от accent-600 до accent-700 + inset highlight + drop-shadow зелёного
- **Secondary / Ghost**: прозрачные с тонкой границей, hover → accent-50 fill
- **Tiny**: для recs-controls, 6×10 px padding
- **Large**: для основного CTA (56px высота)

### Карточки
- Белая поверхность, border `--border`, border-radius 16–24 px, тень `--shadow-sm`
- Hover: `translateY(-1px)` + усиленная тень

### Аккордеон
- Header: 16×18 px padding, иконка в 40×40 квадрате с tinted-фоном
- Chevron: круг 28×28, при `is-open` rotate 180° + заливка accent-600
- Body: открывается через `display: none → block` (JS контроль)

### Drop-zone
- 280px высота, 24px radius
- Большая upload-иконка 56×56
- При `is-dragover`:
  - Фон → `--accent-50`
  - Border solid 2px accent-600
  - Glow (`--shadow-glow`)
  - Контент scale 1.04
  - Radial-glow появляется через `.dropzone-glow` элемент

### Модалка
- Backdrop: `rgba(15,36,25,0.5)` + blur 6px
- Карточка: max-width 560px, radius 24px
- Close-кнопка: rotate 90° на hover

### Alert + Toast
- Alert: красная плашка с inline SVG-иконкой (!) слева
- Toast: белая карточка снизу-справа с зелёной SVG-иконкой (✓) и shadow-lg

### Loading
- Спиннер: SVG-кольцо 64×64, анимация 1.1s linear infinite
- Прогресс-бар: 4px высота, 280px ширина, ползунок бегает туда-обратно

### State-chips
- Вертикальный стек (не grid)
- Каждый chip: 12×14 px padding, 10px radius
- Иконка слева (32×32, tinted-фон), label слева (uppercase micro), value справа
- 4 тона: ok (зелёный), warn (жёлтый), bad (красный), info (синий)

### Responsive
- **≤ 1099px** (tablet): 1 колонка start, topbar без meta-pills
- **≤ 767px** (mobile): topbar с иконками, hero в 1 столбец фич, dropzone 220px, кнопки full-width, state-chips вертикально, shot-types 2×2
- **≤ 380px** (small phones): компактнее отступы и размеры

### Reduced motion
Полная поддержка `prefers-reduced-motion: reduce` — все анимации отключаются, mesh не движется, прогресс-бар статичен.

---

## 4. Анимации (полный список)

| Анимация | Триггер | Длительность | Easing |
|---|---|---|---|
| `meshDrift1/2/3` | Авто (фон) | 28–40s | ease-in-out |
| `pulse` (status dot) | Авто | 2s | ease-in-out |
| `spin` (спиннер) | loading | 1.1s | linear |
| `progressSlide` (loading bar) | loading | 1.6s | ease |
| `fadeSlideIn` (screens, panels) | Появление | 400ms | var(--ease) |
| `riseIn` (modal, loading card) | Появление | 300–400ms | var(--ease-spring) |
| `popIn` (preview cards) | Появление | 320ms | var(--ease-spring) |
| Hover buttons | `:hover` | 180ms | var(--ease) |
| Hover cards | `:hover` | 180ms | var(--ease) |
| Hover dropzone | `:hover` | 240ms | var(--ease) |
| Drag-over dropzone | `.is-dragover` | 240ms | var(--ease) |
| Drag-over dropzone inner | `.is-dragover` | 360ms | var(--ease-spring) |
| Drag-over glow | `.is-dragover` | 360ms | var(--ease) |
| Accordion chevron rotate | `.is-open` | 240ms | var(--ease-spring) |
| Accordion icon scale | `.is-open` | 240ms | var(--ease-spring) |
| Modal close button rotate | `:hover` | 180ms | var(--ease) |
| Staggered preview cards | nth-child | 0–200ms | var(--ease-spring) |
| Staggered state-chips | nth-child | 0–280ms | var(--ease) |
| Staggered rec-items | nth-child | 0–300ms | var(--ease) |
| Loading step fade | text change | 160ms | var(--ease) |
| Toast appear | `.is-visible` | 240ms | var(--ease-spring) |
| Alert appear | `.is-visible` | 300ms | var(--ease) |

---

## 5. UX-решения (Senior Product Designer взгляд)

### Удалено
- ❌ Glassmorphism (заменён на чистые карточки с мягкими тенями)
- ❌ Эмодзи-иконки в UI shell (оставлены только в `ACTION_COPY` JS, т.к. это data-логика)
- ❌ Дублирование welcome-mobile / welcome-features-desktop (один набор + CSS-адаптив)
- ❌ Тяжёлый radial-gradient фон (заменён на mesh с анимацией)
- ❌ Tagline в topbar (только в hero)
- ❌ Модель-pill на мобильном (съедает место)
- ❌ `app-state-*` legacy classes (JS их добавляет, но CSS их не использует)
- ❌ `MAX_OPEN_RECS = 1` (dead constant в JS, не трогаю)

### Добавлено
- ✅ **Hero-блок** — крупный заголовок с display-шрифтом (Instrument Serif) для акцента, бейдж, 4 фичи в 2×2 grid
- ✅ **Micro-бейдж** «AI для ухоженного газона» — социальное доказательство «это AI»
- ✅ **SVG-схема угла 45°** — заменяет CSS-примитивы, рисует телефон + луч + лужайку + лейбл угла
- ✅ **4 типа снимка** с иконками (camera, leaf, magnifier, foundation) — визуально богаче
- ✅ **Качественный tip-блок** в guide-card — выделен warn-цветом для привлечения внимания
- ✅ **Compact previews** в results — горизонтальная лента с staggered анимацией
- ✅ **Status badge** «Завершено» в diagnosis panel — статус анализа визуально
- ✅ **Chip-иконки** в state-chips — слева цветной квадрат с символом
- ✅ **Аккордеон с tinted-иконкой** в квадрате 40×40 — выглядит как premium-карточки
- ✅ **Tip-блок** в рекомендациях — выделен accent-50 фоном
- ✅ **Warning-блок** в рекомендациях — выделен warn-100 фоном
- ✅ **Loading overlay** с прогресс-баром — пользователь видит, что процесс идёт
- ✅ **Toast** с SVG-иконкой — выглядит как modern SaaS, не alert()
- ✅ **Staggered animations** — превью, chips, рекомендации появляются с задержкой, ощущение «живого» UI

### Сохранено (намеренно)
- 🔒 Все ID-хуки (38 штук) — JS-логика не ломается
- 🔒 Body-классы `app--start/--loading/--results` — единственный механизм переключения экранов
- 🔒 `is-open` класс для аккордеона — JS уже умеет с ним работать
- 🔒 Структура `#guideTemplate` — JS делает cloneNode
- 🔒 Endpoint `POST /analyze-photo` — никаких изменений
- 🔒 Формат `multipart/form-data` с полем `files` — бэкенд не трогаем

### Адаптив
- **Desktop (≥ 1200px)**: 2 колонки везде, полный layout
- **Tablet (768–1099px)**: 1 колонка, topbar без meta-pills, кнопки full-width
- **Mobile (≤ 767px)**: topbar с иконками, hero в 1 столбец фич, dropzone 220px, кнопки 100% width, state-chips вертикально
- **Small phones (≤ 380px)**: ещё компактнее

### Доступность
- `aria-label`, `aria-expanded`, `aria-modal`, `aria-live`, `role` — где нужно
- `focus-visible` outline через `--shadow-ring`
- `prefers-reduced-motion: reduce` — отключает анимации
- Минимум 4.5:1 contrast для всех текстов
- Touch-targets ≥ 40px на мобильном

---

## 6. Что осталось без изменений

- **Backend** — не трогали (по требованию)
- **JS-логика** — не трогали (994 строки, все функции и event handlers как были)
- **`BACKEND/knowledge/*.json`** — данные не менялись
- **API-контракт** — `POST /analyze-photo` с `multipart/form-data`, поле `files` (2–5 файлов)
- **Структура ответа** — `final_state` (12 LawnState полей) + `recommendations` (массив Recommendation)
- **Иконки эмодзи в `ACTION_COPY`** (JS, строки 50–161) — это data-логика, не UI shell; замена потребует изменения JS

---

## 7. Скриншоты (проверено в браузере)

Сделано 11 скриншотов через headless Chromium (Playwright):

1. **Desktop 1440×900 — стартовый экран** — hero, dropzone, фичи, инструкция
2. **Tablet 1024×768 — стартовый экран** — 1 колонка, topbar без meta
3. **Mobile 375×812 — стартовый экран** — компактный topbar с иконками, hero в 1 столбец
4. **Drop-zone hover** — зелёная рамка, бежевый фон, иконка приподнята
5. **Drop-zone drag-over** — solid граница, glow, scale 1.04
6. **Loading overlay** — большая карточка со спиннером, фазой, прогресс-баром
7. **Results desktop** — диагноз слева, рекомендации справа, первая карточка раскрыта
8. **Results с открытой второй карточкой** — accordion работает
9. **Results expand-all** — все 4 карточки раскрыты с продуктами и tip-блоками
10. **Модалка инструкции** — SVG-схема, 4 типа снимка, советы
11. **Results mobile** — 1 колонка, всё адаптировано

**Найденные ошибки:** только 2 ожидаемых 404 на `photo-guide.webp` и `grass-background.webp` (файлы отсутствуют — это учтено в JS, есть fallback). В остальном — никаких console errors, никаких network errors.

---

## 8. Рекомендации (что можно улучшить в следующих итерациях)

1. **Заменить эмодзи-иконки в `ACTION_COPY` (JS)** на inline SVG — потребует косметического изменения JS, но даст визуальную консистентность
2. **Скачать реальное фото** для `photo-guide.webp` — если найдётся подходящее (или замениить на качественную SVG-инфографику)
3. **Тёмная тема** — добавить `@media (prefers-color-scheme: dark)` с переопределением токенов
4. **Skeleton-loader** для state-chips и rec-items — пока backend отвечает, показывать placeholder
5. **Анимация перехода start → results** — сейчас просто `fadeSlideIn`, можно сделать FLIP-анимацию превью → compact
6. **Прогресс-бар** в loading — сейчас не привязан к реальному прогрессу, можно показывать проценты
7. **Светлый/тёмный переключатель** — кнопка в topbar

---

## 9. Главный результат

> Когда пользователь впервые откроет GreenScan, у него должна возникнуть мысль: «Ого. Это уже похоже на настоящий коммерческий AI-продукт.»

✅ Достигнуто:
- Крупная современная типографика (Inter + Instrument Serif)
- Много воздуха (spacing 24–32px, padding в карточках)
- Премиальные карточки (мягкие тени, скругления, hover-эффекты)
- Большая привлекательная drop-zone (280×auto, glow, drag-over анимация)
- Hero-блок в стиле Perplexity/Vercel (badge, заголовок, 4 фичи)
- Mesh-gradient фон (плавающие blob-ы 28–40s)
- Плавные микроанимации (fade, slide, scale, spring)
- Полный адаптив (desktop / tablet / mobile)
- Все функции работают (drag&drop, анализ, рекомендации, отчёт)

**Никаких изменений в backend / API / JS-логике. Полная совместимость.**
