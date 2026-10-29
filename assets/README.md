# External assets

`manifest.json` pins source commits, model and dataset revisions, checksums and license decisions. Payloads stay under `STUDY_STORAGE_ROOT`. No dataset, robot mesh, model weights, external source tree or runtime image is committed here.

```bash
python3 tools/assets.py check
python3 tools/assets.py list
python3 tools/assets.py plan ASSET_ID
python3 tools/assets.py fetch ASSET_ID
python3 tools/assets.py verify ASSET_ID
```

`fetch` requires explicit IDs and approved external storage. The tool reuses verified files and rejects mismatched files without overwriting them. Missing or unresolved license grants block automatic fetch. Content under a restricted license requires a separate explicit acceptance flag. A source-code license does not automatically license its model weights or datasets.

Publisher SHA256 values identify large Hub files; Git blob IDs identify ordinary Hub files. `verify` checks the actual bytes. `COLD_ARCHIVE` means an archived local environment or asset needs restoration; it does not count as an available payload. Exact local receipts stay under the external `private/asset-receipts` directory.
