import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_waha_webhook_real_format():
    """Test webhook with real WAHA format"""
    real_payload = {
        'id': 'evt_01kaeq2ytn8nsdfw71h9kcgdhv',
        'timestamp': 1763578051414,
        'event': 'message',
        'session': 'default',
        'metadata': {},
        'me': {
            'id': '6282260987069@c.us',
            'pushName': 'Adi Hermawan'
        },
        'payload': {
            'id': 'false_628970982028@c.us_3A8376E43AF40D6FF778',
            'timestamp': 1763578051,
            'from': '628970982028@c.us',
            'fromMe': False,
            'source': 'app',
            'to': '6282260987069@c.us',
            'body': 'Tes',
            'hasMedia': False,
            'media': None,
            'ack': 1,
            'ackName': 'SERVER',
            'location': None,
            'vCards': [],
            '_data': {
                'id': {
                    'fromMe': False,
                    'remote': '628970982028@c.us',
                    'id': '3A8376E43AF40D6FF778',
                    '_serialized': 'false_628970982028@c.us_3A8376E43AF40D6FF778'
                },
                'viewed': False,
                'body': 'Tes',
                'type': 'chat',
                't': 1763578051,
            }
        },
        'engine': 'WEBJS',
        'environment': {
            'version': '2025.11.2',
            'engine': 'WEBJS',
            'tier': 'CORE',
            'browser': '/usr/bin/chromium'
        }
    }

    response = client.post("/webhook/waha", json=real_payload)
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert "message" in response.json()


def test_waha_webhook_real_format_with_media():
    """Test webhook with media"""
    payload_with_media = {
        'id': 'evt_media_test',
        'timestamp': 1763578051414,
        'event': 'message',
        'session': 'default',
        'metadata': {},
        'me': {
            'id': '6282260987069@c.us',
            'pushName': 'Bot'
        },
        'payload': {
            'id': 'msg_media_test',
            'timestamp': 1763578051,
            'from': '628970982028@c.us',
            'fromMe': False,
            'to': '6282260987069@c.us',
            'body': 'Check this image',
            'hasMedia': True,
            'media': {
                'url': 'http://localhost:3000/api/files/test.jpg',
                'mimetype': 'image/jpeg',
                'filename': 'test.jpg'
            },
            'ack': 1,
            'ackName': 'SERVER',
            'vCards': []
        },
        'engine': 'WEBJS',
        'environment': {
            'version': '2025.11.2',
            'engine': 'WEBJS',
            'tier': 'CORE'
        }
    }

    response = client.post("/webhook/waha", json=payload_with_media)
    assert response.status_code == 200
    assert response.json()["status"] == "success"


def test_waha_webhook_from_me():
    """Test webhook when message is from bot itself"""
    payload = {
        'id': 'evt_from_me',
        'timestamp': 1763578051414,
        'event': 'message',
        'session': 'default',
        'metadata': {},
        'me': {
            'id': '6282260987069@c.us',
            'pushName': 'Bot'
        },
        'payload': {
            'id': 'msg_from_me',
            'timestamp': 1763578051,
            'from': '6282260987069@c.us',
            'fromMe': True,
            'to': '628970982028@c.us',
            'body': 'Hello, how can I help you?',
            'hasMedia': False,
            'ack': 1,
            'vCards': []
        },
        'engine': 'WEBJS',
        'environment': {
            'version': '2025.11.2',
            'engine': 'WEBJS'
        }
    }

    response = client.post("/webhook/waha", json=payload)
    assert response.status_code == 200
