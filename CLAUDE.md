# netbox-surveillance — Agent Operating Guide

AGPL-3.0 NetBox 4.6 plugin, the vendor-neutral SoT for cameras, NVRs and door stations (Zephyrex
card 50). Sibling plugins (`../netbox-meshcore`, `../netbox-database`) set the conventions; the
Zephyrex SOP collective holds the cross-repo rules.

- **Standalone:** FKs only core NetBox (`"dcim.Device"` string labels); no `required_plugins`.
- **Secret policy:** no password, passcode or keypad code is ever a field. `*_ref` fields are
  OpenBao paths checked by `validate_openbao_ref`.
- **Typed columns only:** no JSON blobs, no config_context.
- **Generated layers:** forms, tables, views, URLs, serializers and viewsets are built from
  `forms.FORM_FIELDS`; adding a model means adding it to `models.MODELS`, `FORM_FIELDS`,
  `filtersets.py`, `urls.SLUGS`, a migration and tests.
- **Migrations are hand-authored**; check with `makemigrations netbox_surveillance --check --dry-run`
  on a dev NetBox.
- **Tests:** real DB, no mocks: `manage.py test netbox_surveillance --keepdb`.
- **Gate:** `.githooks/pre-commit` (black + py_compile); enable with `git config core.hooksPath .githooks`.
- SPDX header on every source file.
