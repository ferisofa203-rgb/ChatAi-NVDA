# -*- coding: UTF-8 -*-
# Build customizations
# Change this file instead of sconstruct or manifest files, whenever possible.

def _(arg):
	return arg


# Add-on information variables
addon_info = {
	# Add-on internal name/identifier for NVDA
	"addon_name": "ChatAI",

	# Add-on summary shown to users
	"addon_summary": _("Chat AI"),

	# Add-on description
	"addon_description": _(
		"""Chat AI is an NVDA add-on that allows you to chat with AI models in a simple and accessible way.

This add-on is currently in early development and may change in future versions.

Features:
- Chat with AI using a simple interface
- Session-based chat (history is cleared when the dialog is closed)
- Custom API key support
- Gemini provider support

To open the chat dialog, press NVDA+Alt+A.
To open the add-on settings, press NVDA+Shift+Alt+A."""
	),

	# Version
	"addon_version": "0.1.0",

	# Author(s)
	"addon_author": "Mufida Azza",

	# URL for documentation/support
	"addon_url": "https://github.com/ferisofa203-rgb/ChatAi-NVDA",

	# Documentation file name
	"addon_docFileName": "readme.html",

	# Minimum NVDA version supported
	"addon_minimumNVDAVersion": "2024.3",

	# Last NVDA version supported/tested
	"addon_lastTestedNVDAVersion": "2025.1",

	# Update channel
	"addon_updateChannel": None,
}

# Specify whether this add-on provides a single documentation or separate
# technical and user documentations.
useRootDocAsUserDoc = True

# Define the python files that are the sources of your add-on.
import os
import os.path

pythonSources = [
	os.path.join(dirpath, filename)
	for dirpath, dirnames, filenames in os.walk("addon")
	for filename in filenames
	if os.path.splitext(filename)[1] == ".py"
]

# Files that contain strings for translation
i18nSources = pythonSources + ["buildVars.py"]

# Files that will be ignored when building the nvda-addon file
excludedFiles = []

# Base language for the NVDA add-on
baseLanguage = "en"

# Markdown extensions for add-on documentation
markdownExtensions = []