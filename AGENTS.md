# Repository Guidelines

## Project Structure & Module Organization
- Root is the Home Assistant integration package. Place this folder at `config/custom_components/yeedi_c12_cloud/` for local testing.
- `manifest.json`: integration metadata (`domain: yeedi_c12_cloud`, deps).
- `__init__.py`: setup/unload and platform forwarding.
- `config_flow.py`: account/device login + config entries.
- `vacuum.py`: entity implementation, MQTT/cloud wiring, services.
- `services.yaml`: service descriptions for UI docs.
- `translations/`: strings for config flow and errors.

## Build, Test, and Development Commands
- Configuration is GUI-only; no YAML setup is required.
- Link into a local HA config: `mkdir -p ~/.homeassistant/custom_components && ln -s "$(pwd)" ~/.homeassistant/custom_components/yeedi_c12_cloud`
- Run Home Assistant Core: `hass -c ~/.homeassistant --debug`
- Validate config (optional): `python -m homeassistant --script check_config -c ~/.homeassistant`
- Reload during dev: use HA UI (Developer Tools → YAML → Reload) and/or remove/re-add the config entry.
  Optional debug logging is shown in CONTRIBUTING.md.

## Coding Style & Naming Conventions
- Python 3.11+, 4-space indent, type hints; follow PEP 8.
- Keep imports grouped: stdlib → third-party → Home Assistant → local.
- Constants live in `const.py` and use UPPER_SNAKE_CASE.
- Entity IDs: `vacuum.yeedi_c12_cloud_*`; unique_id format: `<domain>:<device_id>`.
- Keep I/O async; avoid blocking calls in the event loop.

## Testing Guidelines
- No unit tests yet; verify via a live HA instance.
- Add the integration via UI: “Yeedi C12 (Cloud API)”, complete login, pick device.
- Use Developer Tools → Services on the Yeedi vacuum entity, e.g.:
  - `vacuum.set_fan_speed` with `fan_speed: standard`.
  - `vacuum.send_command` with `{"command": "locate"}`.
- Confirm state, battery, and attributes update; watch logs at DEBUG.

## Commit & Pull Request Guidelines
- Use Conventional Commits (e.g., `feat:`, `fix:`, `chore:`). History uses `chore: initial commit`.
- One change per PR, with description, linked issues, and reproduction steps.
- Include device model/firmware, logs (redact secrets), and screenshots of entities/services when relevant.

## Security & Configuration Tips
- Never commit credentials. The flow hashes passwords before auth; do not log them.
- Country code should be ISO alpha-2 (e.g., `US`).
- Network/API failures are common—prefer resilient error handling and clear user errors.
