# yeedi_c12_cloud

Home Assistant custom integration for Yeedi C12 (Cloud API).

## Installation
- Manual (recommended for early adopters)
  1) Copy this folder to your Home Assistant config at `config/custom_components/yeedi_c12_cloud/`.
  2) Restart Home Assistant.
- Developer symlink (for contributors)
  1) `mkdir -p ~/.homeassistant/custom_components`
  2) From this repo folder: `ln -s "$(pwd)" ~/.homeassistant/custom_components/yeedi_c12_cloud`
  3) Start HA: `hass -c ~/.homeassistant --debug`

### HACS (optional)
- Open HACS → Integrations → three-dots menu → Custom repositories.
- Add repository URL: <ADD_REPO_URL_HERE> (Category: Integration).
- Search for and install “Yeedi C12 (Cloud API)” in HACS.
- Restart Home Assistant.

## Configuration (GUI-only)
- Settings → Devices & Services → Add Integration → "Yeedi C12 (Cloud API)".
- Sign in with your Yeedi/Ecovacs account, choose your country code, and select the device to add.
- No YAML configuration is required or supported.

## Upgrading
- Replace the `custom_components/yeedi_c12_cloud` folder with the new version and restart Home Assistant.
- If entities don’t appear after upgrade, use Settings → Devices & Services → Reload on the integration or restart HA.

## Troubleshooting
- Enable debug logs (see CONTRIBUTING.md) and check Developer Tools → Logs.
- Common issues: invalid credentials, wrong country code, or no MQTT-capable devices on the account.

For contributor guidelines, coding standards, and test flow, see AGENTS.md and CONTRIBUTING.md.

## Maps Roadmap
Current release does not render maps. Planned work includes:
- Subscribe to map/room events via `deebot_client` and persist latest state.
- Expose a map as an `image`/`camera` entity for UI display.
- Room discovery: list room names/IDs and enable name-based cleaning.
- Investigate no‑go zones/virtual walls support (model dependent).

Open issues: https://github.com/mwhaite/yeedi_c12_cloud/labels/maps
