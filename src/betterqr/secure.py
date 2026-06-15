import hashlib
import hmac
import base64
import secrets

class SecureQR:
    def __init__(self, secret_key: str):
        if not secret_key or not isinstance(secret_key, str):
            raise ValueError("Secret key must be a non-empty string.")
        self._secret_key = secret_key.encode('utf-8')

    def sign_payload(self, payload: str) -> str:
        """
        Generates a secure HMAC-SHA256 signature for the given payload.
        Returns a compact string (payload.signature) ready for matrix encoding.
        """
        if not payload or not isinstance(payload, str):
            raise ValueError("Payload must be a non-empty string.")

        h = hmac.new(self._secret_key, payload.encode('utf-8'), hashlib.sha256)
        signature = base64.urlsafe_b64encode(h.digest()).decode('utf-8').rstrip('=')
        return f"{payload}.{signature}"

    def verify_signature(self, signed_payload: str) -> bool:
        """
        Verifies the HMAC-SHA256 signature of a signed payload.
        """
        if not signed_payload or not isinstance(signed_payload, str):
            raise ValueError("Signed payload must be a non-empty string.")

        parts = signed_payload.rsplit(".", 1)
        if len(parts) != 2:
            return False # Invalid format

        payload, signature = parts
        # Re-sign the payload to get the expected signature
        h = hmac.new(self._secret_key, payload.encode('utf-8'), hashlib.sha256)
        expected_signature = base64.urlsafe_b64encode(h.digest()).decode('utf-8').rstrip('=')

        return secrets.compare_digest(signature, expected_signature)

    def obfuscate_payload(self, payload: str) -> str:
        """
        Obfuscates a payload using a symmetric cyclic bitwise XOR loop salted with a SHA-256 derived key stream.
        Returns a base64 encoded string.
        """
        if not payload or not isinstance(payload, str):
            raise ValueError("Payload must be a non-empty string.")

        payload_bytes = payload.encode('utf-8')
        key_hash = hashlib.sha256(self._secret_key).digest()
        obfuscated_bytes = bytearray(len(payload_bytes))

        for i in range(len(payload_bytes)):
            obfuscated_bytes[i] = payload_bytes[i] ^ key_hash[i % len(key_hash)]

        return base64.urlsafe_b64encode(obfuscated_bytes).decode('utf-8').rstrip('=')

    def deobfuscate_payload(self, obfuscated_payload: str) -> str:
        """
        Deobfuscates a payload that was obfuscated using the obfuscate_payload method.
        """
        if not obfuscated_payload or not isinstance(obfuscated_payload, str):
            raise ValueError("Obfuscated payload must be a non-empty string.")

        # Add padding back if it was removed by rstrip(\'=\')
        padding_needed = 4 - (len(obfuscated_payload) % 4)
        if padding_needed != 4:
            obfuscated_payload += '=' * padding_needed

        try:
            obfuscated_bytes = base64.urlsafe_b64decode(obfuscated_payload.encode('utf-8'))
        except Exception:
            return "" # Invalid base64

        key_hash = hashlib.sha256(self._secret_key).digest()
        deobfuscated_bytes = bytearray(len(obfuscated_bytes))

        for i in range(len(obfuscated_bytes)):
            deobfuscated_bytes[i] = obfuscated_bytes[i] ^ key_hash[i % len(key_hash)]

        return deobfuscated_bytes.decode('utf-8');