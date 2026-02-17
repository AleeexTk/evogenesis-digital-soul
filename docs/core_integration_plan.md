# Core Integration Plan (Project_Pyramid2024 → Nexus Core)

## Цель
Свести `Project_Pyramid2024` к роли архивного источника, а рабочую логику исполнения — в `packages/execution/*` и `apps/execution_worker.py`.

## Границы
- **Source of truth:** `SharedTaskManager`.
- **Entry points:** только `apps/*`.
- **Legacy imports:** запрещены, перенос только через адаптеры в `packages/execution`.

## Этап 1 (сделано)
- Legacy перемещён в `legacy/Project_Pyramid2024`.
- Бинарные и компилируемые артефакты исключены (`*.png`, `*.zip`, `*.pyc`).

## Этап 2 (ближайший)
1. Вынести из legacy исключительно execution-контракты:
   - команды выполнения,
   - сериализацию/десериализацию payload,
   - нормализацию stdout/stderr/result.
2. Зафиксировать единый event envelope:
   - `event_id`,
   - `task_id`,
   - `session_id`,
   - `state_version`,
   - `ts`,
   - `kind`, `payload`.
3. Подключить relay-публикацию результата execution worker в `/api/events`.

## Этап 3
- Добавить compatibility-layer тесты на сценарий:
  `pending -> processing_by_exec -> done` + `event published`.
- Добавить smoke-runner в `apps/execution_worker.py` для dry-run режима.

## Мэппинг (минимальный)
- `legacy/Project_Pyramid2024/...` (источник) -> `packages/execution/termux/*` (боевой код)
- `legacy/Project_Pyramid2024/...` (источник) -> `packages/execution/session/*` (сессии)
- `apps/execution_worker.py` (entrypoint)

## Критерии готовности
- Нет runtime-импортов из `legacy/*`.
- Все execution-статусы проходят через `SharedTaskManager`.
- `pytest` в корне проходит без захвата legacy-тестов.
