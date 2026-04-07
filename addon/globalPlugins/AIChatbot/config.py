# -*- coding: UTF-8 -*-

import config

CONFIG_SECTION = "AIChatbot"

CONFIG_SPEC = {
    "provider": "string(default='gemini')",
    "model": "string(default='auto')",
    "apiKey": "string(default='')",
    "timeout": "integer(default=30)"
}


def initializeConfig():
    """Register the add-on configuration spec."""
    if CONFIG_SECTION not in config.conf.spec:
        config.conf.spec[CONFIG_SECTION] = CONFIG_SPEC


def getConfig():
    """Return the add-on config section."""
    return config.conf[CONFIG_SECTION]


def getProvider():
    """Return the selected provider."""
    return getConfig()["provider"]


def setProvider(value):
    """Set the selected provider."""
    getConfig()["provider"] = value


def getModel():
    """Return the selected model."""
    return getConfig()["model"]


def setModel(value):
    """Set the selected model."""
    getConfig()["model"] = value


def getApiKey():
    """Return the stored API key."""
    return getConfig()["apiKey"].strip()


def setApiKey(value):
    """Set the API key."""
    getConfig()["apiKey"] = value.strip()


def getTimeout():
    """Return the configured timeout as an integer."""
    try:
        return int(getConfig()["timeout"])
    except Exception:
        return 30


def setTimeout(value):
    """Set the request timeout."""
    try:
        getConfig()["timeout"] = int(value)
    except Exception:
        getConfig()["timeout"] = 30
 
 