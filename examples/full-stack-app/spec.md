# TaskFlow: a small full-stack task manager (synthetic spec)

Build a task manager with a Python API and a TypeScript browser front end.
Users manage tasks inside projects. All names and data here are invented.

## Backend (Python 3.11+, FastAPI, SQLite)

- `backend/app.py`: FastAPI entry point. Runnable with `python app.py`.
- `backend/models.py`: Pydantic models.
- `backend/database.py`: raw `sqlite3` access (no ORM). Creates tables on first run.
  Wrap writes in transactions. Use `sqlite3.Row` for dict-like rows.
- `backend/routes/tasks.py`, `backend/routes/projects.py`: CRUD routes.
- `backend/requirements.txt`: pinned dependencies.

Task: `id`, `title` (1-200 chars, required), `description`, `status`
(`todo` | `in_progress` | `done`), `priority` (`low` | `medium` | `high`),
`project_id`, `created_at`, `updated_at`.

Project: `id`, `name` (1-100 chars, required), `color` (hex, default `#3B82F6`),
`created_at`.

| Method | Path | Purpose |
|--------|------|---------|
| GET | /api/projects | list projects |
| POST | /api/projects | create a project |
| DELETE | /api/projects/{id} | delete a project and its tasks |
| GET | /api/projects/{id}/tasks | list tasks in a project |
| POST | /api/tasks | create a task |
| PUT | /api/tasks/{id} | update a task |
| DELETE | /api/tasks/{id} | delete a task |
| GET | /api/tasks?status=todo | filter by status |

Enable CORS for `http://localhost:3000`.

## Frontend (TypeScript strict, vanilla DOM, vanilla CSS)

- `frontend/index.html`: shell with `#app`, `#sidebar`, `#content`, `#task-list`.
- `frontend/styles.css`: CSS Grid, sidebar 250px plus a `1fr` main column.
  Status badges (gray, blue, green). Priority borders (thin, medium, thick red).
  Sidebar collapses below 768px. Dark mode via `prefers-color-scheme`.
- `frontend/src/main.ts`: entry point.
- `frontend/src/api.ts`: typed fetch wrapper. Base URL defaults to
  `http://localhost:8000`. Throws on non-2xx with the parsed error message.
- `frontend/src/types.ts`: `Task` and `Project` interfaces.
- `frontend/src/components/TaskList.ts`, `TaskForm.ts`, `ProjectSidebar.ts`:
  each exports `render(): HTMLElement`.
- `frontend/tsconfig.json`: strict mode.

## Constraints

- No external CSS framework and no frontend build tool.
- Every file has its imports and is syntactically valid.
- `README.md` explains how to run the backend and the frontend.
