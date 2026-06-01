# Dolfi.AI — App Store & Distribution Guide

## Apple App Store (iOS Companion App)

### Prerequisites
- Apple Developer account (https://developer.apple.com — $99/year)
- App Store Connect access
- Xcode 15+ on macOS

### Required Secrets (store in Vault at `dolfi/apple`)
| Key | Description |
|---|---|
| `issuer_id` | Your Apple Developer Issuer ID (from App Store Connect → Keys) |
| `key_id` | API Key ID |
| `private_key` | `.p8` private key contents |

### Speed 3 Automated Deployment

The CI pipeline handles upload automatically on version tags. Steps:
1. Build SvelteKit frontend as a WKWebView wrapper (Capacitor)
2. Code sign with Distribution certificate
3. Upload to App Store Connect via `altool` or `xcrun`
4. Submit for review via App Store Connect API

### Manual Upload (fallback)
```bash
xcrun altool --upload-app \
  --type ios \
  --file DolfiAI.ipa \
  --apiKey $APPLE_KEY_ID \
  --apiIssuer $APPLE_ISSUER_ID
```

### App Metadata Required
- **Bundle ID**: `ai.theflippit.dolfi`
- **Category**: Utilities
- **Age Rating**: 4+
- **Privacy Policy URL**: https://theflippit.ai/privacy
- **Support URL**: https://theflippit.ai/support

---

## Google Play Store (Android Companion App)

### Prerequisites
- Google Play Developer account (https://play.google.com/console — $25 one-time)
- Service account with `Release Manager` role

### Required Secrets (store in Vault at `dolfi/google`)
| Key | Description |
|---|---|
| `service_account_json` | JSON key for Play API service account |

### Speed 3 Automated Deployment

```bash
# Build APK/AAB via Capacitor
npx cap build android --release

# Upload to Play Store internal track
fastlane supply \
  --aab app/build/outputs/bundle/release/app-release.aab \
  --track internal \
  --json_key $GOOGLE_SERVICE_ACCOUNT_JSON
```

### App Metadata Required
- **Package ID**: `ai.theflippit.dolfi`
- **Category**: Tools
- **Content Rating**: Everyone
- **Privacy Policy URL**: https://theflippit.ai/privacy

---

## Web App (Primary Platform)

Deployed to Hostinger VPS via K3s. No store submission required.

---

## Pricing Tiers

| Tier | Price | Features |
|---|---|---|
| **Free** | $0/month | 1 device, Speed 1 only, 100 AI requests/day |
| **Hobbyist** | $9/month | 3 devices, Speed 1+2, 1,000 AI requests/day, DB sync |
| **Pro** | $29/month | 10 devices, all speeds, unlimited AI, VNC access, priority support |
| **Team** | $99/month | Unlimited devices, all features, team dashboard, SLA 99.9% |
| **Enterprise** | Custom | On-premise deployment, custom model fine-tuning, dedicated support |

---

## GPG Key Setup for Releases

```bash
# Generate a dedicated release signing key
gpg --batch --gen-key <<EOF
Key-Type: EdDSA
Key-Curve: Ed25519
Name-Real: Dolfi.AI Releases
Name-Email: releases@theflippit.ai
Expire-Date: 2y
%no-passphrase
EOF

# Export public key (add to GitHub → Settings → GPG keys)
gpg --armor --export releases@theflippit.ai > dolfi-release-public.asc

# Export private key (store in GitHub Secret GPG_PRIVATE_KEY)
gpg --armor --export-secret-keys releases@theflippit.ai
```

Store the following in GitHub Actions Secrets:
- `GPG_PRIVATE_KEY` — armored private key
- `GPG_PASSPHRASE` — passphrase (use empty string if --no-passphrase)
- `GPG_KEY_ID` — key fingerprint or email
- `APPLE_KEY_ID` — Apple API key ID
- `APPLE_ISSUER_ID` — Apple issuer ID
- `GOOGLE_SERVICE_ACCOUNT_JSON` — Google Play service account JSON
