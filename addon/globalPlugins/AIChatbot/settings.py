# -*- coding: UTF-8 -*-

import wx
import webbrowser
import ui
from gui import settingsDialogs

from .config import (
	getProvider,
	setProvider,
	getModel,
	setModel,
	getApiKey,
	setApiKey,
	getTimeout,
	setTimeout
)

from .providers.gemini import getAvailableModels


class AIChatSettingsPanel(settingsDialogs.SettingsPanel):
	title = "Chat AI"

	def makeSettings(self, settingsSizer):
		mainSizer = wx.BoxSizer(wx.VERTICAL)

		# Provider
		providerLabel = wx.StaticText(self, label="Provider:")
		mainSizer.Add(providerLabel, 0, wx.ALL, 5)

		self.providerChoice = wx.Choice(
			self,
			choices=["gemini"]
		)
		self.providerChoice.SetStringSelection(getProvider())
		mainSizer.Add(self.providerChoice, 0, wx.EXPAND | wx.ALL, 5)

		# Model mode
		modelModeLabel = wx.StaticText(self, label="Model mode:")
		mainSizer.Add(modelModeLabel, 0, wx.ALL, 5)

		self.modelModeChoice = wx.Choice(
			self,
			choices=["auto", "custom"]
		)

		currentModel = getModel().strip()
		if not currentModel or currentModel.lower() == "auto":
			self.modelModeChoice.SetStringSelection("auto")
			customModelValue = ""
		else:
			self.modelModeChoice.SetStringSelection("custom")
			customModelValue = currentModel

		mainSizer.Add(self.modelModeChoice, 0, wx.EXPAND | wx.ALL, 5)

		# Server model list
		serverModelsLabel = wx.StaticText(self, label="Available models from server:")
		mainSizer.Add(serverModelsLabel, 0, wx.ALL, 5)

		self.modelCombo = wx.ComboBox(
			self,
			value=customModelValue,
			choices=[],
			style=wx.CB_DROPDOWN
		)
		mainSizer.Add(self.modelCombo, 0, wx.EXPAND | wx.ALL, 5)

		self.refreshModelsButton = wx.Button(self, label="Refresh model list")
		mainSizer.Add(self.refreshModelsButton, 0, wx.ALL, 5)

		# Manual override
		manualModelLabel = wx.StaticText(self, label="Manual model name (optional):")
		mainSizer.Add(manualModelLabel, 0, wx.ALL, 5)

		self.manualModelEdit = wx.TextCtrl(
			self,
			value=customModelValue
		)
		mainSizer.Add(self.manualModelEdit, 0, wx.EXPAND | wx.ALL, 5)

		# API Key
		apiKeyLabel = wx.StaticText(self, label="API Key:")
		mainSizer.Add(apiKeyLabel, 0, wx.ALL, 5)

		self.apiKeyEdit = wx.TextCtrl(
			self,
			value=getApiKey(),
			style=wx.TE_PASSWORD
		)
		mainSizer.Add(self.apiKeyEdit, 0, wx.EXPAND | wx.ALL, 5)

		self.geminiHelpButton = wx.Button(self, label="Get Gemini API key")
		mainSizer.Add(self.geminiHelpButton, 0, wx.ALL, 5)

		# Timeout
		timeoutLabel = wx.StaticText(self, label="Timeout (seconds):")
		mainSizer.Add(timeoutLabel, 0, wx.ALL, 5)

		self.timeoutEdit = wx.TextCtrl(
			self,
			value=str(getTimeout())
		)
		mainSizer.Add(self.timeoutEdit, 0, wx.EXPAND | wx.ALL, 5)

		settingsSizer.Add(mainSizer, 1, wx.EXPAND)

		self.modelModeChoice.Bind(wx.EVT_CHOICE, self.onModelModeChanged)
		self.refreshModelsButton.Bind(wx.EVT_BUTTON, self.onRefreshModels)
		self.modelCombo.Bind(wx.EVT_COMBOBOX, self.onModelComboSelected)
		self.geminiHelpButton.Bind(wx.EVT_BUTTON, self.onGeminiHelp)

		self.loadAvailableModels()
		self.onModelModeChanged(None)

	def loadAvailableModels(self, refresh=False):
		currentValue = self.modelCombo.GetValue()

		try:
			models = getAvailableModels(refresh=refresh)
		except Exception:
			models = []

		self.modelCombo.Clear()
		for model in models:
			self.modelCombo.Append(model)

		targetValue = self.manualModelEdit.GetValue().strip() or currentValue
		if targetValue:
			self.modelCombo.SetValue(targetValue)

	def onRefreshModels(self, evt):
		self.loadAvailableModels(refresh=True)

	def onModelComboSelected(self, evt):
		self.manualModelEdit.SetValue(self.modelCombo.GetValue())

	def onModelModeChanged(self, evt):
		isCustom = self.modelModeChoice.GetStringSelection() == "custom"
		self.modelCombo.Enable(isCustom)
		self.manualModelEdit.Enable(isCustom)
		self.refreshModelsButton.Enable(isCustom)

	def onGeminiHelp(self, evt):
		ui.message("Opening Gemini API key page")
		webbrowser.open("https://aistudio.google.com/app/apikey")

	def onSave(self):
		setProvider(self.providerChoice.GetStringSelection())
		setApiKey(self.apiKeyEdit.GetValue())
		setTimeout(self.timeoutEdit.GetValue())

		modelMode = self.modelModeChoice.GetStringSelection()
		if modelMode == "auto":
			setModel("auto")
			return

		manualValue = self.manualModelEdit.GetValue().strip()
		comboValue = self.modelCombo.GetValue().strip()
		finalModel = manualValue or comboValue or "auto"
		setModel(finalModel)