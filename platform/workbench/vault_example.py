#!/usr/bin/env python3
"""
vault_example.py
Demonstrates how to retrieve SOC credentials programmatically from HashiCorp Vault
using the 'hvac' library in the Underground Nexus workbench.
"""

import os
import sys

try:
    import hvac
except ImportError:
    print("Error: 'hvac' library not found. Please install it with 'pip install hvac'.")
    sys.exit(1)

def main():
    # 1. Configure client connection settings
    # Default to the local dev Vault location and token
    vault_addr = os.getenv("VAULT_ADDR", "http://localhost:8200")
    vault_token = os.getenv("VAULT_TOKEN", "myroot")

    print(f"Connecting to HashiCorp Vault at: {vault_addr}")

    # Initialize the HVAC client
    client = hvac.Client(url=vault_addr, token=vault_token)

    # 2. Check connection status
    try:
        is_authenticated = client.is_authenticated()
    except Exception as e:
        print(f"Error connecting to Vault: {e}")
        sys.exit(1)

    if not is_authenticated:
        print("Error: Authentication failed. Please check your VAULT_TOKEN.")
        sys.exit(1)

    print("Successfully authenticated with Vault.")

    # 3. Read secrets from kv-v2 engine
    # In Vault kv-v2, the API path maps secret/soc/wazuh to Mount: "secret" / Path: "soc/wazuh"
    secret_path = "soc/wazuh"
    mount_point = "secret"

    print(f"Reading secrets from path: {mount_point}/{secret_path}")

    try:
        response = client.secrets.kv.v2.read_secret_version(
            path=secret_path,
            mount_point=mount_point
        )
    except hvac.exceptions.InvalidPath:
        print(f"Error: Path '{mount_point}/{secret_path}' was not found. Has it been initialized?")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading secret: {e}")
        sys.exit(1)

    # Extract the data payload
    data = response['data']['data']

    print("\n--- Retrieved Credentials ---")
    for key, value in data.items():
        # Mask the actual secret values for safety in logs
        masked = value[:2] + "*" * (len(value) - 2) if len(value) > 2 else "*" * len(value)
        print(f"{key}: {masked}")
    print("-----------------------------\n")

    print("Integration test completed successfully!")

if __name__ == "__main__":
    main()
