"""
Alibaba CPS Authentication Utilities
"""

import hashlib
import hmac
from urllib.parse import urlparse


def build_signature_string(url_path: str, params: dict) -> str:
    """
    Build the signature source string according to Alibaba's specification.

    Signature string =
        urlPath +
        key1value1 +
        key2value2 +
        ...

    Parameters are sorted alphabetically.
    """

    signature = url_path

    for key in sorted(params.keys()):
        signature += f"{key}{params[key]}"

    return signature


def generate_signature(
    url_path: str,
    params: dict,
    secret_key: str,
) -> str:
    """
    Generate Alibaba _aop_signature.

    Returns uppercase hexadecimal HMAC-SHA1.
    """

    message = build_signature_string(url_path, params)

    digest = hmac.new(
        secret_key.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha1,
    ).hexdigest()

    return digest.upper()


def extract_url_path(url: str) -> str:
    """
    Extract Alibaba urlPath.

    Example:

    https://usapi.alibaba.com/openapi/param2/1/com.alibaba.xxx/get/1000

    becomes

    param2/1/com.alibaba.xxx/get/1000
    """

    parsed = urlparse(url)

    path = parsed.path

    if path.startswith("/openapi/"):
        path = path[len("/openapi/"):]

    return path.lstrip("/")
