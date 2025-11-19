import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


@pytest.fixture
def sample_waha_webhook_payload():
    """Sample WAHA webhook payload for testing"""
    return {
        "id": "evt_01aaaaaaaaaaaaaaaaaaaaaaaa",
        "timestamp": 1634567890123,
        "session": "default",
        "metadata": {
            "user.id": "123",
            "user.email": "email@example.com"
        },
        "engine": "WEBJS",
        "event": "message",
        "payload": {
            "id": "false_11111111111@c.us_AAAAAAAAAAAAAAAAAAAA",
            "timestamp": 1666943582,
            "from": "11111111111@c.us",
            "fromMe": True,
            "source": "api",
            "to": "11111111111@c.us",
            "participant": "string",
            "body": "string",
            "hasMedia": True,
            "media": {
                "url": "http://localhost:3000/api/files/false_11111111111@c.us_AAAAAAAAAAAAAAAAAAAA.oga",
                "mimetype": "audio/jpeg",
                "filename": "example.pdf",
                "s3": {
                    "Bucket": "my-bucket",
                    "Key": "default/false_11111111111@c.us_AAAAAAAAAAAAAAAAAAAA.oga"
                },
                "error": None
            },
            "ack": -1,
            "ackName": "string",
            "author": "string",
            "location": {
                "latitude": "string",
                "longitude": "string",
                "live": True,
                "name": "string",
                "address": "string",
                "url": "string",
                "description": "string",
                "thumbnail": "string"
            },
            "vCards": [
                "string"
            ],
            "_data": {},
            "replyTo": {
                "id": "AAAAAAAAAAAAAAAAAAAA",
                "participant": "11111111111@c.us",
                "body": "Hello!",
                "_data": {}
            }
        },
        "me": {
            "id": "11111111111@c.us",
            "lid": "123123@lid",
            "jid": "123123:123@s.whatsapp.net",
            "pushName": "string"
        },
        "environment": {
            "version": "YYYY.MM.BUILD",
            "engine": "WEBJS",
            "tier": "PLUS",
            "browser": "/usr/path/to/bin/google-chrome"
        }
    }


def test_waha_webhook_endpoint_success(sample_waha_webhook_payload):
    """Test that the WAHA webhook endpoint accepts valid payloads"""
    response = client.post("/webhook/waha", json=sample_waha_webhook_payload)

    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert "message" in response.json()


def test_waha_webhook_minimal_payload():
    """Test webhook with minimal required fields"""
    minimal_payload = {
        "id": "evt_test",
        "timestamp": 1634567890123,
        "session": "default",
        "engine": "WEBJS",
        "event": "message",
        "payload": {
            "id": "msg_test",
            "timestamp": 1666943582,
            "from": "11111111111@c.us",
            "fromMe": False,
            "to": "22222222222@c.us"
        },
        "me": {
            "id": "11111111111@c.us"
        },
        "environment": {
            "version": "2024.01.001",
            "engine": "WEBJS"
        }
    }

    response = client.post("/webhook/waha", json=minimal_payload)
    assert response.status_code == 200
    assert response.json()["status"] == "success"


def test_waha_webhook_invalid_payload():
    """Test webhook with invalid/incomplete payload returns validation error"""
    # Now we're using WahaWebhookRequest schema which enforces validation
    invalid_payload = {
        "id": "evt_test",
        # Missing required fields like timestamp, session, event, payload, me, environment
    }

    response = client.post("/webhook/waha", json=invalid_payload)
    # Should return 422 for schema validation error
    assert response.status_code == 422


def test_waha_webhook_with_reply():
    """Test webhook with reply message"""
    payload_with_reply = {
        "id": "evt_test",
        "timestamp": 1634567890123,
        "session": "default",
        "engine": "WEBJS",
        "event": "message",
        "payload": {
            "id": "msg_test",
            "timestamp": 1666943582,
            "from": "11111111111@c.us",
            "fromMe": False,
            "to": "22222222222@c.us",
            "body": "This is a reply",
            "replyTo": {
                "id": "original_msg_id",
                "participant": "11111111111@c.us",
                "body": "Original message",
                "_data": {}
            }
        },
        "me": {
            "id": "22222222222@c.us"
        },
        "environment": {
            "version": "2024.01.001",
            "engine": "WEBJS"
        }
    }

    response = client.post("/webhook/waha", json=payload_with_reply)
    assert response.status_code == 200
    assert response.json()["status"] == "success"
