# -*- coding: UTF-8 -*-

import requests

from ..config import getApiKey, getModel, getTimeout

GEMINI_MODELS_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models"
GEMINI_GENERATE_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

_autoModelCandidatesCache = None
_availableModelsCache = None


class GeminiError(Exception):
	pass


def buildContentsFromHistory(history):
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


def _normalizeModelName(modelName):
	if not modelName:
		return ""
	if modelName.startswith("models/"):
		return modelName.split("/", 1)[1]
	return modelName


def _supportsGenerateContent(modelInfo):
	methods = modelInfo.get("supportedGenerationMethods", [])
	return "generateContent" in methods


def _listModels(apiKey):
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


def _isLikelyPreviewModel(modelName):
	name = modelName.lower()
	return (
		"preview" in name or
		"experimental" in name or
		"exp" in name
	)


def _rankAutoModel(modelName):
	name = modelName.lower()

	if _isLikelyPreviewModel(name):
		basePenalty = 1000
	else:
		basePenalty = 0

	if "pro" in name:
		return basePenalty + 10
	if "flash" in name and "flash-lite" not in name:
		return basePenalty + 20
	if "flash-lite" in name:
		return basePenalty + 30

	return basePenalty + 100


def getAvailableModels(refresh=False):
	global _availableModelsCache

	apiKey = getApiKey()
	if not apiKey:
		return []

	if _availableModelsCache is not None and not refresh:
		return list(_availableModelsCache)

	models = _listModels(apiKey)
	available = []

	for modelInfo in models:
		if not _supportsGenerateContent(modelInfo):
			continue

		modelName = _normalizeModelName(modelInfo.get("name", ""))
		if not modelName:
			continue

		available.append(modelName)

	seen = set()
	result = []
	for modelName in available:
		if modelName not in seen:
			seen.add(modelName)
			result.append(modelName)

	result.sort(key=lambda name: (_rankAutoModel(name), name))
	_availableModelsCache = list(result)
	return list(result)


def _getAutomaticModelCandidates(refresh=False):
	global _autoModelCandidatesCache

	if _autoModelCandidatesCache is not None and not refresh:
		return list(_autoModelCandidatesCache)

	available = getAvailableModels(refresh=refresh)
	if not available:
		raise GeminiError("No Gemini models supporting generateContent were found.")

	_autoModelCandidatesCache = list(available)
	return list(available)


def _isAutoMode():
	selected = getModel().strip().lower()
	return (not selected) or selected == "auto"


def _getManualModel():
	return getModel().strip()


def _extractReply(result):
	try:
		return result["candidates"][0]["content"]["parts"][0]["text"]
	except Exception:
		raise GeminiError("Invalid response from server.")


def _postGenerate(apiKey, model, data):
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

	return response


def _isRetryableStatus(statusCode):
	return statusCode in (404, 408, 429, 500, 502, 503, 504)


def _looksLikeModelProblem(responseText):
	if not responseText:
		return False

	text = responseText.lower()
	return (
		"not found" in text or
		"is not supported for generatecontent" in text or
		("model" in text and "not supported" in text)
	)


def sendChat(history):
	global _autoModelCandidatesCache
	global _availableModelsCache

	apiKey = getApiKey()
	if not apiKey:
		raise GeminiError("API key is missing.")

	data = {
		"contents": buildContentsFromHistory(history)
	}

	if not _isAutoMode():
		model = _getManualModel()
		if not model:
			raise GeminiError("No model is configured.")

		response = _postGenerate(apiKey, model, data)

		if response.status_code != 200:
			raise GeminiError("API error: {} {}".format(response.status_code, response.text))

		try:
			result = response.json()
		except Exception:
			raise GeminiError("Invalid JSON response from server.")

		return _extractReply(result)

	candidates = _getAutomaticModelCandidates()
	lastError = None

	for index, model in enumerate(candidates):
		response = _postGenerate(apiKey, model, data)

		if response.status_code == 200:
			try:
				result = response.json()
			except Exception:
				raise GeminiError("Invalid JSON response from server.")
			return _extractReply(result)

		retryable = _isRetryableStatus(response.status_code)
		modelProblem = _looksLikeModelProblem(response.text)

		if retryable or modelProblem:
			lastError = "Model {} failed: {} {}".format(
				model, response.status_code, response.text
			)

			if index == 0 and modelProblem:
				try:
					_availableModelsCache = None
					_autoModelCandidatesCache = None
					candidates = _getAutomaticModelCandidates(refresh=True)
				except Exception:
					pass
			continue

		raise GeminiError("API error: {} {}".format(response.status_code, response.text))

	if lastError:
		raise GeminiError("All automatic Gemini model fallbacks failed. Last error: {}".format(lastError))

	raise GeminiError("Failed to get a response from Gemini.")