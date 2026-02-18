## Долгоживущая openspec-ветка

```
upstream/master
    │
    ▼
  master  ←── зеркало upstream/master
    │
    └──► openspec-base  ←── долгоживущая, rebase на master
            │                содержит openspec/, CLAUDE.md, AGENTS.md
            │                накапливает specs/ при каждом archive
            │
            ├──► openspec/feat-x  (ответвляется от openspec-base)
            │       │
            │       └──► feat-x   (чистый код → PR в upstream)
            │
            ├──► openspec/feat-y
            │       │
            │       └──► feat-y
            │
            └──► openspec/feat-z  ← specs от feat-x и feat-y уже здесь!


  master
    │
    └──► my-dev  (личные изменения, rebase на master, отдельно)
```

## Жизненный цикл фичи

```bash
# 1. Начало работы над feat-z
git checkout openspec-base
git checkout -b openspec/feat-z

# openspec/specs/ уже содержит знания от feat-x, feat-y
# AI видит контекст предыдущих решений

# 2. Работа в Claude Code
#    /opsx:new feat-z → /opsx:ff → правки → /opsx:apply
#    Коммиты раздельно: spec: ... и feat: ...

# 3. Архивация спеков — возврат знаний в openspec-base
git checkout openspec-base
git merge openspec/feat-z          # или cherry-pick spec-коммитов
#    /opsx:archive                  # если не сделал раньше

# 4. Извлечение чистого кода для upstream
git checkout -b feat-z master
git diff master..openspec/feat-z -- . ':!openspec/' ':!AGENTS.md' ':!CLAUDE.md' | git apply
git add -A
git commit -m "feat: implement feat-z"
git push origin feat-z             # → PR в upstream
```

## Обновление при изменении upstream/master

```bash
# 1. Обновить master
git fetch upstream
git checkout master
git reset --hard upstream/master

# 2. Rebase openspec-base
git checkout openspec-base
git rebase master
#   Конфликтов в openspec/ не будет — upstream про него не знает
#   Конфликты возможны только в CLAUDE.md / AGENTS.md в корне
git push origin openspec-base --force-with-lease

# 3. Rebase активных openspec/feat-* веток
git checkout openspec/feat-z
git rebase openspec-base
git push origin openspec/feat-z --force-with-lease

# 4. Rebase my-dev
git checkout my-dev
git rebase master
git push origin my-dev --force-with-lease
```

## Что накапливается в openspec-base

```
openspec-base/
├── openspec/
│   ├── project.md          # описание проекта — растёт со временем
│   ├── AGENTS.md
│   ├── specs/
│   │   ├── auth/spec.md        ← из feat-x
│   │   ├── payments/spec.md    ← из feat-y
│   │   └── notifications/      ← из feat-z (после archive)
│   ├── changes/
│   │   └── archive/            ← история всех изменений
│   └── config.yaml
├── CLAUDE.md
└── AGENTS.md
```

Каждая новая `openspec/feat-*` ветка стартует с полным контекстом — AI знает про все предыдущие решения, архитектуру и конвенции.
