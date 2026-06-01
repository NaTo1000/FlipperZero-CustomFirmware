"""
CryptoAgent — encryption, decryption, GPG signing, key management.

Handles:
  - AES-256-GCM for data at rest
  - Ed25519 for message signing
  - GPG for release artifact signing
  - HKDF for session key derivation
"""
from __future__ import annotations

import base64
import os
import subprocess
from dataclasses import dataclass
from typing import Optional

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from cryptography.hazmat.primitives.hashes import SHA256
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    NoEncryption,
    PrivateFormat,
    PublicFormat,
)


@dataclass
class EncryptedBlob:
    nonce: bytes
    ciphertext: bytes
    tag_included: bool = True  # AESGCM appends auth tag to ciphertext

    def to_b64(self) -> str:
        return base64.b64encode(self.nonce + self.ciphertext).decode()

    @classmethod
    def from_b64(cls, data: str) -> "EncryptedBlob":
        raw = base64.b64decode(data)
        return cls(nonce=raw[:12], ciphertext=raw[12:])


class CryptoAgent:
    """
    Cryptographic operations for ConductorX.
    """

    # ------------------------------------------------------------------
    # AES-256-GCM (data at rest)
    # ------------------------------------------------------------------

    @staticmethod
    def generate_aes_key() -> bytes:
        return os.urandom(32)  # 256 bits

    @staticmethod
    def encrypt(plaintext: bytes, key: bytes) -> EncryptedBlob:
        nonce = os.urandom(12)
        aesgcm = AESGCM(key)
        ciphertext = aesgcm.encrypt(nonce, plaintext, associated_data=None)
        return EncryptedBlob(nonce=nonce, ciphertext=ciphertext)

    @staticmethod
    def decrypt(blob: EncryptedBlob, key: bytes) -> bytes:
        aesgcm = AESGCM(key)
        return aesgcm.decrypt(blob.nonce, blob.ciphertext, associated_data=None)

    # ------------------------------------------------------------------
    # Ed25519 message signing
    # ------------------------------------------------------------------

    @staticmethod
    def generate_signing_keypair() -> tuple[Ed25519PrivateKey, Ed25519PublicKey]:
        private_key = Ed25519PrivateKey.generate()
        return private_key, private_key.public_key()

    @staticmethod
    def sign(message: bytes, private_key: Ed25519PrivateKey) -> bytes:
        return private_key.sign(message)

    @staticmethod
    def verify(message: bytes, signature: bytes, public_key: Ed25519PublicKey) -> bool:
        try:
            public_key.verify(signature, message)
            return True
        except Exception:
            return False

    # ------------------------------------------------------------------
    # HKDF session key derivation
    # ------------------------------------------------------------------

    @staticmethod
    def derive_session_key(
        ikm: bytes,
        salt: Optional[bytes] = None,
        info: bytes = b"conductorx-session",
        length: int = 32,
    ) -> bytes:
        hkdf = HKDF(algorithm=SHA256(), length=length, salt=salt, info=info)
        return hkdf.derive(ikm)

    # ------------------------------------------------------------------
    # GPG release signing (Speed 3 automation)
    # ------------------------------------------------------------------

    @staticmethod
    def gpg_sign_file(
        file_path: str,
        key_id: str,
        passphrase_env: str = "GPG_PASSPHRASE",
    ) -> str:
        """
        Sign a release artifact with GPG.
        Returns path to the .sig file.

        Requires GPG to be installed and the key imported.
        Passphrase is read from environment variable (never hardcoded).
        """
        sig_path = f"{file_path}.sig"
        passphrase = os.environ.get(passphrase_env, "")
        cmd = [
            "gpg",
            "--batch",
            "--yes",
            "--passphrase", passphrase,
            "--local-user", key_id,
            "--detach-sign",
            "--armor",
            "--output", sig_path,
            file_path,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"GPG signing failed: {result.stderr}")
        return sig_path

    @staticmethod
    def gpg_verify(file_path: str, sig_path: str) -> bool:
        """Verify a GPG detached signature."""
        result = subprocess.run(
            ["gpg", "--verify", sig_path, file_path],
            capture_output=True,
            text=True,
        )
        return result.returncode == 0

    # ------------------------------------------------------------------
    # Key serialization helpers
    # ------------------------------------------------------------------

    @staticmethod
    def private_key_to_pem(key: Ed25519PrivateKey) -> bytes:
        return key.private_bytes(
            encoding=Encoding.PEM,
            format=PrivateFormat.PKCS8,
            encryption_algorithm=NoEncryption(),
        )

    @staticmethod
    def public_key_to_pem(key: Ed25519PublicKey) -> bytes:
        return key.public_bytes(encoding=Encoding.PEM, format=PublicFormat.SubjectPublicKeyInfo)
