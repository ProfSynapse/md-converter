"""
File Encryption Utilities
Location: app/utils/encryption.py

This module provides utilities for encrypting files at rest to ensure
that even with disk access, file contents cannot be read without the
decryption key stored in the user's session.

Uses Fernet (symmetric encryption) from the cryptography library.
"""
import os
import logging
from pathlib import Path
from typing import Optional
from cryptography.fernet import Fernet, InvalidToken

logger = logging.getLogger(__name__)


def generate_encryption_key() -> bytes:
    """
    Generate a new Fernet encryption key.

    Returns:
        32-byte URL-safe base64-encoded key

    Example:
        >>> key = generate_encryption_key()
        >>> len(key)
        44
    """
    return Fernet.generate_key()


def encrypt_file(input_path: str, output_path: str, key: bytes) -> bool:
    """
    Encrypt a file using Fernet symmetric encryption.

    Args:
        input_path: Path to plaintext file
        output_path: Path to save encrypted file
        key: Fernet encryption key

    Returns:
        True if encryption successful, False otherwise

    Example:
        >>> key = generate_encryption_key()
        >>> encrypt_file('document.docx', 'document.docx.enc', key)
        True
    """
    try:
        input_file = Path(input_path)
        output_file = Path(output_path)

        if not input_file.exists():
            logger.error(f'Input file not found: {input_path}')
            return False

        # Read plaintext
        with open(input_file, 'rb') as f:
            plaintext = f.read()

        # Encrypt
        fernet = Fernet(key)
        ciphertext = fernet.encrypt(plaintext)

        # Write encrypted file
        with open(output_file, 'wb') as f:
            f.write(ciphertext)

        logger.debug(f'Encrypted file: {input_path} -> {output_path}')
        return True

    except Exception as e:
        logger.error(f'Encryption failed: {e}', exc_info=True)
        return False


def decrypt_file(input_path: str, output_path: str, key: bytes) -> bool:
    """
    Decrypt a file using Fernet symmetric encryption.

    Args:
        input_path: Path to encrypted file
        output_path: Path to save decrypted file
        key: Fernet encryption key

    Returns:
        True if decryption successful, False otherwise

    Raises:
        InvalidToken: If key is incorrect or file is corrupted
    """
    try:
        input_file = Path(input_path)
        output_file = Path(output_path)

        if not input_file.exists():
            logger.error(f'Input file not found: {input_path}')
            return False

        # Read ciphertext
        with open(input_file, 'rb') as f:
            ciphertext = f.read()

        # Decrypt
        fernet = Fernet(key)
        plaintext = fernet.decrypt(ciphertext)

        # Write decrypted file
        with open(output_file, 'wb') as f:
            f.write(plaintext)

        logger.debug(f'Decrypted file: {input_path} -> {output_path}')
        return True

    except InvalidToken:
        logger.error(f'Decryption failed: Invalid key or corrupted file')
        return False
    except Exception as e:
        logger.error(f'Decryption failed: {e}', exc_info=True)
        return False


def encrypt_file_in_place(file_path: str, key: bytes) -> bool:
    """
    Encrypt a file in place (overwrites original).

    Args:
        file_path: Path to file to encrypt
        key: Fernet encryption key

    Returns:
        True if encryption successful, False otherwise
    """
    temp_path = f'{file_path}.tmp'

    try:
        # Encrypt to temporary file
        if not encrypt_file(file_path, temp_path, key):
            return False

        # Replace original with encrypted version
        os.replace(temp_path, file_path)
        logger.debug(f'Encrypted file in place: {file_path}')
        return True

    except Exception as e:
        logger.error(f'In-place encryption failed: {e}', exc_info=True)
        # Clean up temp file if it exists
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return False


def decrypt_to_stream(file_path: str, key: bytes) -> Optional[bytes]:
    """
    Decrypt a file and return contents as bytes (for streaming downloads).

    Args:
        file_path: Path to encrypted file
        key: Fernet encryption key

    Returns:
        Decrypted file contents as bytes, or None if decryption fails
    """
    try:
        file = Path(file_path)

        if not file.exists():
            logger.error(f'File not found: {file_path}')
            return None

        # Read ciphertext
        with open(file, 'rb') as f:
            ciphertext = f.read()

        # Decrypt
        fernet = Fernet(key)
        plaintext = fernet.decrypt(ciphertext)

        logger.debug(f'Decrypted file to stream: {file_path}')
        return plaintext

    except InvalidToken:
        logger.error(f'Decryption failed: Invalid key')
        return None
    except Exception as e:
        logger.error(f'Decryption to stream failed: {e}', exc_info=True)
        return None


def key_to_string(key: bytes) -> str:
    """
    Convert encryption key bytes to string for session storage.

    Args:
        key: Fernet key bytes

    Returns:
        Base64-encoded string
    """
    return key.decode('utf-8')


def string_to_key(key_string: str) -> bytes:
    """
    Convert string back to encryption key bytes.

    Args:
        key_string: Base64-encoded key string

    Returns:
        Fernet key bytes
    """
    return key_string.encode('utf-8')
