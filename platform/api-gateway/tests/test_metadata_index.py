"""Metadata index client — disabled without proxy URL/key."""
from src.clients.metadata_index import MetadataIndexClient


def test_metadata_index_disabled_without_config():
    client = MetadataIndexClient(None, None)
    assert client.enabled is False


def test_metadata_index_enabled_with_config():
    client = MetadataIndexClient("https://example.workers.dev", "secret")
    assert client.enabled is True
