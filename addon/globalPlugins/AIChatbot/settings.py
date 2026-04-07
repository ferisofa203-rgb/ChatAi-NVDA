# -*- coding: UTF-8 -*-

import wx
from gui import settingsDialogs

from .config import (
    getProvider, setProvider,
    getModel, setModel,
    getApiKey, setApiKey,
    getTimeout, setTimeout
)


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

        # Model
        modelLabel = wx.StaticText(self, label="Model:")
        mainSizer.Add(modelLabel, 0, wx.ALL, 5)

        self.modelChoice = wx.Choice(
            self,
            choices=[
                "auto",
                "gemini-2.5-flash",
                "gemini-2.5-flash-lite",
                "gemini-2.5-pro"
            ]
        )

        currentModel = getModel()
        if self.modelChoice.FindString(currentModel) != wx.NOT_FOUND:
            self.modelChoice.SetStringSelection(currentModel)
        else:
            self.modelChoice.SetStringSelection("auto")

        mainSizer.Add(self.modelChoice, 0, wx.EXPAND | wx.ALL, 5)

        # API Key
        apiKeyLabel = wx.StaticText(self, label="API Key:")
        mainSizer.Add(apiKeyLabel, 0, wx.ALL, 5)

        self.apiKeyEdit = wx.TextCtrl(
            self,
            value=getApiKey(),
            style=wx.TE_PASSWORD
        )
        mainSizer.Add(self.apiKeyEdit, 0, wx.EXPAND | wx.ALL, 5)

        # Timeout
        timeoutLabel = wx.StaticText(self, label="Timeout (seconds):")
        mainSizer.Add(timeoutLabel, 0, wx.ALL, 5)

        self.timeoutEdit = wx.TextCtrl(
            self,
            value=str(getTimeout())
        )
        mainSizer.Add(self.timeoutEdit, 0, wx.EXPAND | wx.ALL, 5)

        settingsSizer.Add(mainSizer, 1, wx.EXPAND)

    def onSave(self):
        setProvider(self.providerChoice.GetStringSelection())
        setModel(self.modelChoice.GetStringSelection())
        setApiKey(self.apiKeyEdit.GetValue())
        setTimeout(self.timeoutEdit.GetValue())
 