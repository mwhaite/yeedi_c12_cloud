# Contributing

Thank you for helping improve this Home Assistant custom integration. For coding standards, repo layout, commands, and testing flow, read AGENTS.md first.

## Getting Started
- Prereqs: Python 3.11+, Home Assistant Core (`pip install homeassistant`). Use a virtualenv.
- Link into your HA config:
  - `mkdir -p ~/.homeassistant/custom_components`
  - `ln -s "$(pwd)" ~/.homeassistant/custom_components/yeedi_c12_cloud`
- Run HA Core with debug: `hass -c ~/.homeassistant --debug`
- In the HA UI, add the integration: “Yeedi C12 (Cloud API)”, then sign in and pick your device.

## Dev Workflow
- Follow style, structure, and test guidance in `AGENTS.md`.
- Prefer small, focused branches: `feat/…`, `fix/…`.
- Validate config when relevant: `python -m homeassistant --script check_config -c ~/.homeassistant`.

## Debug Logging
Add to `configuration.yaml` to capture detailed logs during development:

```yaml
logger:
  default: info
  logs:
    custom_components.yeedi_c12_cloud: debug
    deebot_client: debug
    homeassistant.components.vacuum: debug
```

## Pull Requests
- Use Conventional Commits (e.g., `feat:`, `fix:`, `chore:`).
- Include clear description, reproduction steps, linked issues, and relevant logs/screenshots (redact secrets).
- Test your changes locally in HA and ensure entities and services behave as expected.
