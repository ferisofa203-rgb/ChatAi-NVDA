# -*- coding: UTF-8 -*-

import requests

from ..config import getApiKey, getModel, getTimeout


GEMINI_MODELS_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models"
GEMINI_GENERATE_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

# Cache the resolved model for the current NVDA session only.
_resolvedModelCache = None


class GeminiError(Exception):
    pass


def buildContentsFromHistory(history):
    """
    Convert internal chat history into Gemini API format.
    history format:
    [
        {"role": "user", "content": "..."},
        {"role": "assistant", "content": "..."}
    ]
    """
    contents = []

    for message in history:
        role = message.get("role")
        text = message.get("content", "")

        if not text:
            continue

        if role == "user":
            contents.append({
                "role": "user",
                "parts": [{"text": text}]
            })
        elif role == "assistant":
            contents.append({
                "role": "model",
                "parts": [{"text": text}]
            })

    return contents


def _getHeaders(apiKey):
    return {
        "Content-Type": "application/json",
        "x-goog-api-key": apiKey,
    }


def _listModels(apiKey):
    """
    Return a list of model metadata from the Gemini models endpoint.
    """
    models = []
    pageToken = None

    while True:
        params = {}
        if pageToken:
            params["pageToken"] = pageToken

        try:
            response = requests.get(
                GEMINI_MODELS_ENDPOINT,
                headers=_getHeaders(apiKey),
                params=params,
                timeout=getTimeout()
            )
        except requests.exceptions.RequestException as e:
            raise GeminiError("Network error while listing models: {}".format(str(e)))

        if response.status_code != 200:
            raise GeminiError(
                "Failed to list models: {} {}".format(response.status_code, response.text)
            )

        try:
            data = response.json()
        except Exception:
            raise GeminiError("Invalid model list response from server.")

        models.extend(data.get("models", []))
        pageToken = data.get("nextPageToken")

        if not pageToken:
            break

    return models


def _supportsGenerateContent(modelInfo):
    """
    Check whether the model supports generateContent.
    """
    methods = modelInfo.get("supportedGenerationMethods", [])
    return "generateContent" in methods


def _normalizeModelName(modelName):
    """
    The list endpoint returns model names like 'models/gemini-2.5-flash'.
    For generateContent we pass only the base model id like 'gemini-2.5-flash'.
    """
    if modelName.startswith("models/"):
        return modelName.split("/", 1)[1]
    return modelName


def _chooseAutomaticModel(apiKey):
    """
    Choose the best available model automatically.
    Priority order:
    1. gemini-2.5-flash
    2. gemini-2.5-flash-lite
    3. gemini-2.5-pro
    Then fall back to the first model that supports generateContent.
    """
    global _resolvedModelCache

    if _resolvedModelCache:
        return _resolvedModelCache

    models = _listModels(apiKey)

    available = []
    for modelInfo in models:
        if _supportsGenerateContent(modelInfo):
            modelName = _normalizeModelName(modelInfo.get("name", ""))
            if modelName:
                available.append(modelName)

    if not available:
        raise GeminiError("No Gemini models supporting generateContent were found.")

    preferredOrder = [
        "gemini-2.5-flash",
        "gemini-2.5-flash-lite",
        "gemini-2.5-pro",
    ]

    for preferred in preferredOrder:
        if preferred in available:
            _resolvedModelCache = preferred
            return preferred

    _resolvedModelCache = available[0]
    return _resolvedModelCache


def _resolveModel(apiKey):
    """
    Resolve the configured model. If set to 'auto', select one automatically.
    """
    selected = getModel().strip()

    if not selected or selected.lower() == "auto":
        return _chooseAutomaticModel(apiKey)

    return selected


def _extractReply(result):
    try:
        return result["candidates"][0]["content"]["parts"][0]["text"]
    except Exception:
        raise GeminiError("Invalid response from server.")


def sendChat(history):
    """
    Send full chat history to Gemini and return assistant reply.
    """
    apiKey = getApiKey()
    if not apiKey:
        raise GeminiError("API key is missing.")

    model = _resolveModel(apiKey)
    endpoint = GEMINI_GENERATE_ENDPOINT.format(model=model)

    data = {
        "contents": buildContentsFromHistory(history)
    }

    try:
        response = requests.post(
            endpoint,
            headers=_getHeaders(apiKey),
            json=data,
            timeout=getTimeout()
        )
    except requests.exceptions.RequestException as e:
        raise GeminiError("Network error: {}".format(str(e)))

    if response.status_code == 404 and getModel().strip().lower() == "auto":
        # Model cache may be stale. Clear it once and retry.
        global _resolvedModelCache
        _resolvedModelCache = None

        model = _resolveModel(apiKey)
        endpoint = GEMINI_GENERATE_ENDPOINT.format(model=model)

        try:
            response = requests.post(
                endpoint,
                headers=_getHeaders(apiKey),
                json=data,
                timeout=getTimeout()
            )
        except requests.exceptions.RequestException as e:
            raise GeminiError("Network error: {}".format(str(e)))

    if response.status_code != 200:
        raise GeminiError("API error: {} {}".format(response.status_code, response.text))

    try:
        result = response.json()
    except Exception:
        raise GeminiError("Invalid JSON response from server.")

    return _extractReply(result)