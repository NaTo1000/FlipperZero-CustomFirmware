# ConductorX — Model Card

## Identity

| Field | Value |
|---|---|
| **Name** | ConductorX |
| **Full Name** | CHAIMERA.ConductorX3SP |
| **Version** | 0.1.0 |
| **Role** | Primary orchestration agent for Dolfi.AI |
| **Domain** | Flipper Zero — exclusively |
| **Speed Modes** | 3SP (Three Speed Protocol) |

---

## Description

ConductorX is the central AI conductor agent of the Dolfi.AI platform. It is **solely** a Flipper Zero control conductor — every capability it possesses exists to operate, configure, develop for, and support the Flipper Zero device and ecosystem.

ConductorX orchestrates a cluster of specialized sub-agents (CHAIMERA cluster), each isolated in its own container and communicating via signed message queues.

---

## Three Speed Protocol (3SP)

### Speed 1 — Guidance
- Passive mode. ConductorX responds only when directly asked.
- Answers are minimal, precise, and sourced from RAG.
- No automation is triggered without explicit user command.
- Use case: experienced users who know what they want.

### Speed 2 — Overlay
- Tutorial mode. ConductorX annotates every action in real time.
- Full code proofing on every string submitted.
- Step-by-step UI overlay explaining what is happening and why.
- Workflow algorithms shown with each automated step.
- Use case: learning, onboarding, pair-programming with AI.

### Speed 3 — Full Automation
- ConductorX plans, executes, validates, and recovers autonomously.
- Triggers: CI checks, licence verification, build pipelines, deployments.
- App Store (Apple + Google Play) upload workflows.
- Documentation generation and pricing uploads.
- Source code archival to isolated Code DB.
- Secrets rotation via Vault.
- GPG signing of all release artifacts.
- Use case: production deployments, release automation, fleet management.

---

## CHAIMERA Agent Cluster

| Agent | Container | Responsibility |
|---|---|---|
| ReceptionistAgent | `chaimera-receptionist` | Intent classification, routing |
| ConductorAgent | `chaimera-conductor` | Direct Flipper device operations |
| TutorialAgent | `chaimera-tutorial` | Speed 2 overlay and step narration |
| CodeAgent | `chaimera-code` | Code generation, proofing, rewriting |
| RecoveryAgent | `chaimera-recovery` | Safe-base recovery, state rollback |
| SQLAgent | `chaimera-sql` | Parameterized queries, schema management |
| CryptoAgent | `chaimera-crypto` | Encryption, GPG, key management |
| DebugAgent | `chaimera-debug` | Error analysis, log triage, auto-fix |

### Inter-Agent Communication
- Redis Streams for async message passing
- Ed25519-signed message envelopes (CryptoAgent signs all cross-agent messages)
- Dead-letter queue for failed agent tasks → RecoveryAgent
- Pack inference: batched LLM calls across agents (reduces API cost ~60%)

---

## Quad-Tag RAG

All knowledge is indexed with 4 mandatory metadata tags:

```
Tag 1 — Level:   top | mid | bot
Tag 2 — Domain:  firmware | nfc | subghz | ir | badusb | ibutton | crypto | sql | general
Tag 3 — Type:    tutorial | reference | error | recovery | code | pricing | legal
Tag 4 — Recency: live | recent | archive
```

### Retrieval Cascade (top → mid → bot)
1. **top**: Retrieve architectural/conceptual context
2. **mid**: Retrieve procedural steps relevant to context
3. **bot**: Retrieve raw code, signals, or data grounding the answer
4. **Imputation**: Missing chunks inferred from adjacent tags before final compile

### Section-Tagged Compilation
Retrieved chunks are assembled with section tags:
```xml
<context level="top" domain="firmware" type="reference">...</context>
<steps level="mid" domain="firmware" type="tutorial">...</steps>
<code level="bot" domain="firmware" type="code">...</code>
```

---

## Audit Ledger

ConductorX maintains an immutable, append-only hash-chained audit log of every action:

```sql
CREATE TABLE conductorx_audit (
    id          BIGSERIAL PRIMARY KEY,
    prev_hash   CHAR(64) NOT NULL,
    timestamp   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    agent       VARCHAR(64) NOT NULL,
    action      VARCHAR(256) NOT NULL,
    payload_hash CHAR(64) NOT NULL,
    signature   TEXT NOT NULL
);
```

- `prev_hash` = SHA-256 of the previous row's canonical representation
- `signature` = Ed25519 signature by CryptoAgent
- Replicated to 3 PostgreSQL instances (immutable triple redundancy)
- Queryable — full SQL access for audit and compliance

---

## Security Model

| Layer | Technology |
|---|---|
| Data at rest | AES-256-GCM |
| Data in transit | TLS 1.3 |
| Agent message signing | Ed25519 |
| Session key derivation | HKDF-SHA256 |
| Secrets management | HashiCorp Vault |
| Release signing | GPG (personal admin keyring) |
| Code DB | Network-isolated Postgres instance |
| Secrets DB | Vault — never in application DB |

---

## Hotkey Surface

All Flipper Zero operations accessible via keyboard shortcuts in the web UI:

| Shortcut | Action |
|---|---|
| `Ctrl+F` | Flash firmware |
| `Ctrl+U` | Upload file to SD card |
| `Ctrl+D` | Download file from SD card |
| `Ctrl+L` | Open serial log |
| `Ctrl+R` | Reboot device |
| `Ctrl+Shift+R` | Recovery mode |
| `Ctrl+N` | New NFC scan |
| `Ctrl+G` | Sub-GHz capture |
| `Ctrl+I` | IR capture |
| `Ctrl+B` | BadUSB editor |
| `Ctrl+K` | ConductorX command palette |
| `Ctrl+1/2/3` | Switch 3SP speed |

---

## Limitations

- ConductorX will not operate on non-Flipper devices
- Speed 3 automation requires user account with verified device ownership
- Flash operations always require a confirmation step regardless of speed mode
- ConductorX cannot bypass Flipper Zero hardware security features
