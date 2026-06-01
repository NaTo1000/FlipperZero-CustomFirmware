# Dolfi.AI — Model Card

## Model Details

| Field | Value |
|---|---|
| **Name** | Dolfi.AI |
| **Version** | 0.1.0 |
| **Type** | Orchestrated Multi-Agent AI System |
| **Primary Language** | Python 3.11 |
| **LLM Backend** | Grok (xAI API) |
| **License** | MIT |
| **Author** | Nathan Te-Aotonga (NaTo1000) |
| **Repository** | https://github.com/NaTo1000/FlipperZero-CustomFirmware |
| **Website** | https://theflippit.ai |

---

## Model Description

Dolfi.AI is a cloud-hosted AI platform purpose-built for the Flipper Zero ecosystem. It provides a browser-based replacement for qFlipper with an intelligent AI layer — enabling device management, firmware deployment, signal database browsing, and full development workflows from any device without installing desktop software.

Dolfi.AI's core orchestration agent is **ConductorX** — a multi-speed, multi-agent conductor that automates every aspect of Flipper Zero operation.

---

## Intended Use

### Primary Use Cases
- Remote Flipper Zero device management via browser
- Firmware compilation and OTA deployment
- Signal database (NFC, Sub-GHz, IR, iButton) management and sync
- AI-assisted Flipper application development
- BadUSB script generation and validation
- Team-based device fleet management

### Out-of-Scope Use
- Unauthorized access to third-party systems
- Jamming, spoofing, or attacking systems without owner permission
- Any use prohibited by local law or the Flipper Zero terms of service

---

## System Architecture

```
Browser → Dolfi.AI Frontend (SvelteKit)
             ↓
         FastAPI Gateway
             ↓
         ConductorX (LangGraph multi-agent)
          ├── ReceptionistAgent
          ├── ConductorAgent  ←→  Physical Flipper Zero (WebUSB/WebSerial)
          ├── TutorialAgent
          ├── CodeAgent
          ├── RecoveryAgent
          ├── SQLAgent
          ├── CryptoAgent
          └── DebugAgent
             ↓
         Infrastructure
          ├── PostgreSQL (primary data)
          ├── Qdrant (vector store / RAG)
          ├── Redis (cache + message queue)
          └── Vault (secrets)
```

---

## Training & Fine-Tuning

Dolfi.AI uses Grok (xAI) as its base LLM with no additional pre-training. Fine-tuning is performed via:

1. **Interaction Logging**: All user ↔ agent conversations are logged (with consent) to JSONL
2. **RLHF Pipeline**: User feedback (thumbs up/down) is captured per response
3. **LoRA Fine-Tuning**: Periodic LoRA adapters trained on Flipper-domain interactions
4. **Evaluation**: Held-out test set of 500 Flipper Zero Q&A pairs

---

## Evaluation

| Metric | Score | Method |
|---|---|---|
| Flipper Q&A Accuracy | TBD | Human evaluation |
| Code Generation (pass@1) | TBD | Unit test execution |
| RAG Retrieval Precision | TBD | NDCG@10 |
| Response Latency (p50) | TBD | Production telemetry |

---

## Risks & Limitations

- **Hallucination**: Like all LLMs, Dolfi.AI may generate incorrect firmware commands. Recovery Agent and code proofing mitigate this.
- **Device Risk**: Incorrect firmware flashing can brick a Flipper Zero. All flash operations require explicit user confirmation.
- **Legal**: Sub-GHz and NFC capabilities must be used responsibly. Dolfi.AI includes legal disclaimers at point of use.
- **Latency**: Multi-agent orchestration adds latency vs. direct API calls. Pack inference and response streaming reduce perceived latency.

---

## Privacy & Data

- User conversations are logged only with explicit opt-in consent
- Device serial numbers are hashed before storage
- All data encrypted at rest (AES-256-GCM) and in transit (TLS 1.3)
- Secrets stored in HashiCorp Vault — never in application database
- GDPR-compliant data deletion available on request

---

## Citation

```bibtex
@software{dolfi_ai_2026,
  author = {Te-Aotonga, Nathan},
  title  = {Dolfi.AI: Cloud AI Platform for Flipper Zero},
  year   = {2026},
  url    = {https://github.com/NaTo1000/FlipperZero-CustomFirmware}
}
```
