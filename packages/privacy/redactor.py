"""
MigrationMesh - Privacy & Redaction Gateway
Protects enterprise infrastructure topologies, internal IPv4/IPv6 addresses, credentials,
and PII from leaking to LLMs via prompt payloads.
"""

import re
import hashlib
import ipaddress
from typing import Dict, Tuple, Any, List


class PrivacyRedactor:
    """
    Bidirectional Tokenizing Redactor:
    - Redacts IPv4, IPv6, DB connection URIs (with URL-encoded passwords),
      Base64 tokens, AWS/Azure access keys, and bearer tokens.
    - Replaces sensitive strings with deterministic pseudo-tokens (e.g. <IP_NODE_...>, <SECRET_TOKEN_...>).
    - Maintains a local-only token vault for deanonymization in the execution plane.
    """

    def __init__(self, salt: str = "migrationmesh-vault-salt-2026"):
        self.salt = salt
        self.forward_vault: Dict[str, str] = {}  # original -> token
        self.reverse_vault: Dict[str, str] = {}  # token -> original

        self.aws_key_pattern = re.compile(r'\b(AKIA[0-9A-Z]{16})\b')
        self.github_token_pattern = re.compile(r'\b(gh[pousr]_[A-Za-z0-9_]{36,255})\b')
        self.slack_webhook_pattern = re.compile(r'https:\/\/hooks\.slack\.com\/services\/T[a-zA-Z0-9_]+\/B[a-zA-Z0-9_]+\/[a-zA-Z0-9_]+')
        self.stripe_key_pattern = re.compile(r'\b(sk_live_[0-9a-zA-Z]{24,99})\b')
        self.private_key_pattern = re.compile(
            r'-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----[\s\S]+?-----END (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----'
        )
        self.jwt_pattern = re.compile(r'\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b')
        self.connection_string_pattern = re.compile(
            r'(?:postgres|postgresql|mysql|mongodb|redis|sqlserver):\/\/[^:]+:([^@]+)@([^:\/]+):(\d+)\/(\w+)',
            re.IGNORECASE
        )
        self.base64_secret_pattern = re.compile(
            r'(?<![A-Za-z0-9+/_-])[A-Za-z0-9+/_-]{28,}={0,2}(?![A-Za-z0-9+/_-])'
        )
        self.secret_pattern = re.compile(
            r'(?:password|secret|key|token|bearer|pwd)[\s:=]+["\']?([^"\'\s,;]{6,})["\']?',
            re.IGNORECASE
        )
        self.ipv4_pattern = re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b')

    def _get_or_create_token(self, category: str, original: str) -> str:
        if original in self.forward_vault:
            return self.forward_vault[original]

        hash_digest = hashlib.sha256(f"{self.salt}:{original}".encode()).hexdigest()[:6]
        token = f"<{category.upper()}_{hash_digest}>"

        self.forward_vault[original] = token
        self.reverse_vault[token] = original
        return token

    def redact_text(self, text: str) -> Tuple[str, int]:
        """Redacts sensitive entities from plain text or prompt strings."""
        redacted = text
        redaction_count = 0

        # 1. Private Key Blocks (RSA / OpenSSH / DSA / EC)
        for match in self.private_key_pattern.finditer(redacted):
            val = match.group(0)
            tok = self._get_or_create_token("PRIVATE_KEY", val)
            redacted = redacted.replace(val, tok)
            redaction_count += 1

        # 2. Slack Webhooks
        for match in self.slack_webhook_pattern.finditer(redacted):
            val = match.group(0)
            tok = self._get_or_create_token("SLACK_WEBHOOK", val)
            redacted = redacted.replace(val, tok)
            redaction_count += 1

        # 3. GitHub Personal Access Tokens (ghp_..., gho_..., etc.)
        for match in self.github_token_pattern.finditer(redacted):
            val = match.group(1)
            tok = self._get_or_create_token("GITHUB_TOKEN", val)
            redacted = redacted.replace(val, tok)
            redaction_count += 1

        # 4. Stripe API Keys (sk_live_...)
        for match in self.stripe_key_pattern.finditer(redacted):
            val = match.group(1)
            tok = self._get_or_create_token("STRIPE_KEY", val)
            redacted = redacted.replace(val, tok)
            redaction_count += 1

        # 5. AWS Access Keys
        for match in self.aws_key_pattern.finditer(redacted):
            val = match.group(1)
            tok = self._get_or_create_token("AWS_KEY", val)
            redacted = redacted.replace(val, tok)
            redaction_count += 1

        # 6. Connection Strings (Redact passwords and internal hosts)
        for match in self.connection_string_pattern.finditer(redacted):
            pwd = match.group(1)
            host = match.group(2)
            pwd_tok = self._get_or_create_token("DB_PASSWD", pwd)
            host_tok = self._get_or_create_token("DB_HOST", host)
            redacted = redacted.replace(pwd, pwd_tok)
            redacted = redacted.replace(host, host_tok)
            redaction_count += 2

        # 7. JWT Tokens
        for match in self.jwt_pattern.finditer(redacted):
            val = match.group(0)
            if not val.startswith("<") and not val.endswith(">"):
                tok = self._get_or_create_token("JWT_TOKEN", val)
                redacted = redacted.replace(val, tok)
                redaction_count += 1

        # 8. IPv6 Addresses via ipaddress validation
        for candidate in set(re.findall(r'[\w:]+', redacted)):
            if ":" in candidate and len(candidate) >= 4 and not candidate.startswith("<"):
                try:
                    ip = ipaddress.ip_address(candidate)
                    if isinstance(ip, ipaddress.IPv6Address):
                        tok = self._get_or_create_token("IPV6_NODE", candidate)
                        redacted = redacted.replace(candidate, tok)
                        redaction_count += 1
                except ValueError:
                    pass

        # 9. High-Entropy Base64 / Secret tokens (Run before generic keyword matching)
        for match in self.base64_secret_pattern.finditer(redacted):
            val = match.group(0)
            if not val.startswith("<") and not val.endswith(">"):
                tok = self._get_or_create_token("BASE64_KEY", val)
                redacted = redacted.replace(val, tok)
                redaction_count += 1

        # 10. Explicit Secret/Password key-values
        for match in self.secret_pattern.finditer(redacted):
            val = match.group(1)
            if val.startswith("<") and val.endswith(">"):
                continue
            tok = self._get_or_create_token("SECRET_TOKEN", val)
            redacted = redacted.replace(val, tok)
            redaction_count += 1

        # 11. IPv4 Addresses
        for match in self.ipv4_pattern.finditer(redacted):
            val = match.group(0)
            if not val.startswith("<"):
                tok = self._get_or_create_token("IP_NODE", val)
                redacted = redacted.replace(val, tok)
                redaction_count += 1

        return redacted, redaction_count

    def redact_dict(self, data: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
        """Recursively traverses JSON/Dict structure and redacts all string values."""
        redacted_data = {}
        total_redactions = 0

        for key, value in data.items():
            if isinstance(value, str):
                redacted_val, count = self.redact_text(value)
                redacted_data[key] = redacted_val
                total_redactions += count
            elif isinstance(value, dict):
                sub_data, count = self.redact_dict(value)
                redacted_data[key] = sub_data
                total_redactions += count
            elif isinstance(value, list):
                sub_list = []
                for item in value:
                    if isinstance(item, str):
                        r_item, count = self.redact_text(item)
                        sub_list.append(r_item)
                        total_redactions += count
                    elif isinstance(item, dict):
                        r_item, count = self.redact_dict(item)
                        sub_list.append(r_item)
                        total_redactions += count
                    else:
                        sub_list.append(item)
                redacted_data[key] = sub_list
            else:
                redacted_data[key] = value

        return redacted_data, total_redactions

    def deanonymize_text(self, text: str) -> str:
        """Restores original values using the local token vault."""
        restored = text
        for token, original in self.reverse_vault.items():
            restored = restored.replace(token, original)
        return restored
