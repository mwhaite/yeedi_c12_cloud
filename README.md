# yeedi_c12_cloud

Home Assistant custom integration for Yeedi C12 (Cloud API).

## Installation
- Manual (recommended for early adopters)
  1) Copy `custom_components/yeedi_c12_cloud/` from this repository into your Home Assistant config at `config/custom_components/`.
  2) Restart Home Assistant.
- Developer symlink (for contributors)
  1) `mkdir -p ~/.homeassistant/custom_components`
  2) From this repo folder: `ln -s "$(pwd)/custom_components/yeedi_c12_cloud" ~/.homeassistant/custom_components/yeedi_c12_cloud`
  3) Start HA: `hass -c ~/.homeassistant --debug`

### HACS (optional)
- Open HACS → Integrations → three-dots menu → Custom repositories.
- Add repository URL: https://github.com/mwhaite/yeedi_c12_cloud (Category: Integration).
- Search for and install “Yeedi C12 (Cloud API)” in HACS.
- Restart Home Assistant.

## Configuration (GUI-only)
- Settings → Devices & Services → Add Integration → "Yeedi C12 (Cloud API)".
- Sign in with your Yeedi/Ecovacs account, choose your country code, and select the device to add.
- No YAML configuration is required or supported.

## Usage
- Control via Developer Tools → Services. Examples:

```yaml
# Set fan speed
service: vacuum.set_fan_speed
data:
  fan_speed: standard
target:
  entity_id: vacuum.yeedi_c12_cloud_your_device
```

```yaml
# Locate the robot (beep)
service: vacuum.send_command
data:
  command: locate
target:
  entity_id: vacuum.yeedi_c12_cloud_your_device
```

```yaml
# Set mopping water level (if supported)
service: vacuum.set_water_level
data:
  level: 2
target:
  entity_id: vacuum.yeedi_c12_cloud_your_device
```

## Upgrading
- Replace the `custom_components/yeedi_c12_cloud` folder with the new version and restart Home Assistant.
- If entities don’t appear after upgrade, use Settings → Devices & Services → Reload on the integration or restart HA.

## Troubleshooting
- Enable debug logs (see CONTRIBUTING.md) and check Developer Tools → Logs.
- Common issues: invalid credentials, wrong country code, or no MQTT-capable devices on the account.

### Login smoke tests
Need to quickly validate that the cloud login still works? Use the helper scripts in
`scripts/` with your Yeedi credentials (they are never stored):

```bash
export YEEDI_ACCOUNT="name@example.com"
export YEEDI_PASSWORD="super-secret"
# Optional if you are not in the US
export YEEDI_COUNTRY="GB"

python scripts/login_smoke_success.py

# To confirm that bad credentials are rejected
python scripts/login_smoke_failure.py
```

The scripts exit with a non-zero status on unexpected results so they can be wired into
CI or run ad-hoc after dependency updates.

For contributor guidelines, coding standards, and test flow, see AGENTS.md and CONTRIBUTING.md.

## Maps Roadmap
Current release does not render maps. Planned work includes:
- Subscribe to map/room events via `deebot_client` and persist latest state.
- Expose a map as an `image`/`camera` entity for UI display.
- Room discovery: list room names/IDs and enable name-based cleaning.
- Investigate no‑go zones/virtual walls support (model dependent).

Open issues: https://github.com/mwhaite/yeedi_c12_cloud/labels/maps
