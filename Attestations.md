# Understanding Attestations

## What are Attestations?
Attestations in NOCTURN provide cryptographic proof that:
1. The file conversion was performed in a trusted environment
2. The output JSON matches the input log file
3. The process was not tampered with

## Example Attestation
```json
{
  "purl": "pkg:github/johntrue15/NOCTURN-Raspi-test",
  "version": "<commit-sha>",
  "metadata": {
    "buildInvocationId": "<run-id>",
    "completeness": {
      "parameters": true,
      "environment": true,
      "materials": true
    }
  }
}
```

## Verification
1. Download the `.sigstore` bundle from the release
2. Verify using GitHub CLI:
   ```bash
   gh attestation verify --bundle attestation.sigstore.json
   ```
3. Check attestation details at: `https://github.com/<org>/<repo>/attestations/<id>` 