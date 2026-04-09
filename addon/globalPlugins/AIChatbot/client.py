# -*- coding: UTF-8 -*-

from .config import getProvider
from .providers.gemini import sendChat as sendGeminiChat, GeminiError


class AIClientError(Exception):
    pass


def sendChat(history):
    """
    Send chat history to the selected provider and return the assistant reply.
    """
    provider = getProvider().strip().lower()

    if provider == "gemini":
        try:
            return sendGeminiChat(history)
        except GeminiError as e:
            raise AIClientError(str(e))

    raise AIClientError("Unsupported provider: {}".format(provider))