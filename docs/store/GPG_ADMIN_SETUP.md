# GPG & Admin Account Setup

## Release Signing Key

All Dolfi.AI release artifacts are GPG-signed. The public key is published
at https://theflippit.ai/releases-public.asc for independent verification.

### Generate Release Key
```bash
gpg --batch --gen-key <<EOF
Key-Type: EdDSA
Key-Curve: Ed25519
Name-Real: Dolfi.AI Releases
Name-Email: releases@theflippit.ai
Expire-Date: 2y
%no-passphrase
EOF
```

### Publish Public Key
```bash
gpg --armor --export releases@theflippit.ai > releases-public.asc
# Upload to https://keys.openpgp.org and your website
gpg --keyserver keys.openpgp.org --send-keys <FINGERPRINT>
```

### Store Private Key Securely
- Export to GitHub Actions secret `GPG_PRIVATE_KEY`
- Store backup in HashiCorp Vault at `dolfi/gpg`
- **Never** commit the private key to this repository

---

## Admin Account Structure

### GitHub Organisation (NaTo1000)
- Repository: `NaTo1000/FlipperZero-CustomFirmware`
- Branch protection on `main`: require PR + 1 review + CI passing
- Secrets configured: `GPG_PRIVATE_KEY`, `GPG_PASSPHRASE`, `GPG_KEY_ID`

### Hostinger VPS
- SSH key-based access only (no password login)
- K3s cluster with `dolfi` namespace
- Kubernetes secrets managed via `kubectl create secret` (not committed to repo)

### Vault Admin
- Root token stored in personal password manager only
- Create a dedicated `dolfi-app` policy with minimal permissions
- Rotate root token after initial setup

### Domain (theflippit.ai)
- DNS: Hostinger or Cloudflare (recommended for DDoS protection)
- TLS: Let's Encrypt via cert-manager (K3s)
- Subdomains:
  - `api.theflippit.ai` → ConductorX API
  - `vnc.theflippit.ai` → noVNC remote access
  - `vault.theflippit.ai` → Vault UI (admin only, IP-restricted)

---

## Secrets Checklist (never commit these)

- [ ] `GPG_PRIVATE_KEY` → GitHub Secret
- [ ] `GPG_PASSPHRASE` → GitHub Secret
- [ ] `VAULT_ROOT_TOKEN` → Personal password manager only
- [ ] `POSTGRES_PASSWORD` → Vault at `dolfi/postgres`
- [ ] `XAI_API_KEY` → Vault at `dolfi/xai`
- [ ] `APPLE_KEY_ID` → GitHub Secret + Vault at `dolfi/apple`
- [ ] `GOOGLE_SERVICE_ACCOUNT_JSON` → GitHub Secret + Vault at `dolfi/google`
- [ ] `JWT_SECRET` → Vault at `dolfi/jwt` (min 256-bit random value)
