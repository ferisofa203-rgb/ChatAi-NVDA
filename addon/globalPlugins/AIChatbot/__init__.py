# -*- coding: UTF-8 -*-

import addonHandler
import globalPluginHandler
import gui
import scriptHandler
import wx

from .config import initializeConfig
from .dialogs import ChatDialog
from .settings import AIChatSettingsPanel

addonHandler.initTranslation()


class GlobalPlugin(globalPluginHandler.GlobalPlugin):

    def __init__(self):
        super(GlobalPlugin, self).__init__()
        initializeConfig()
        self.chatDialog = None
        self.chatAISettingsMenuItem = None

        # Register settings panel
        try:
            if AIChatSettingsPanel not in gui.settingsDialogs.NVDASettingsDialog.categoryClasses:
                gui.settingsDialogs.NVDASettingsDialog.categoryClasses.append(AIChatSettingsPanel)
        except Exception:
            pass

        # Add direct item to Preferences menu
        try:
            preferencesMenu = gui.mainFrame.sysTrayIcon.preferencesMenu
            self.chatAISettingsMenuItem = preferencesMenu.Append(
                wx.ID_ANY,
                "Chat AI..."
            )
            gui.mainFrame.sysTrayIcon.Bind(
                wx.EVT_MENU,
                self.onOpenSettingsMenu,
                self.chatAISettingsMenuItem
            )
        except Exception:
            self.chatAISettingsMenuItem = None

    def terminate(self):
        try:
            if self.chatDialog is not None:
                self.chatDialog.Destroy()
        except Exception:
            pass

        self.chatDialog = None

        # Remove Preferences menu item
        try:
            if self.chatAISettingsMenuItem is not None:
                preferencesMenu = gui.mainFrame.sysTrayIcon.preferencesMenu
                preferencesMenu.Remove(self.chatAISettingsMenuItem)
                self.chatAISettingsMenuItem = None
        except Exception:
            pass

        # Remove settings panel
        try:
            if AIChatSettingsPanel in gui.settingsDialogs.NVDASettingsDialog.categoryClasses:
                gui.settingsDialogs.NVDASettingsDialog.categoryClasses.remove(AIChatSettingsPanel)
        except Exception:
            pass

        super(GlobalPlugin, self).terminate()

    @scriptHandler.script(
        description="Open the AI chat dialog",
        gesture="kb:NVDA+alt+a"
    )
    def script_openAIChat(self, gesture):
        wx.CallAfter(self.openChatDialog)

    @scriptHandler.script(
        description="Open Chat AI settings",
        gesture="kb:NVDA+alt+shift+a"
    )
    def script_openAIChatSettings(self, gesture):
        wx.CallAfter(self.openSettingsDialog)

    def openChatDialog(self):
        if self.chatDialog is not None:
            try:
                if self.chatDialog:
                    self.chatDialog.Raise()
                    self.chatDialog.SetFocus()
                    return
            except Exception:
                self.chatDialog = None

        self.chatDialog = ChatDialog(gui.mainFrame)
        self.chatDialog.Bind(wx.EVT_CLOSE, self.onDialogClose)
        self.chatDialog.Show()

    def openSettingsDialog(self):
        try:
            gui.mainFrame.popupSettingsDialog(
                gui.settingsDialogs.NVDASettingsDialog,
                AIChatSettingsPanel
            )
        except Exception:
            pass

    def onOpenSettingsMenu(self, event):
        self.openSettingsDialog()

    def onDialogClose(self, event):
        try:
            if self.chatDialog is not None:
                self.chatDialog.Destroy()
        except Exception:
            pass

        self.chatDialog = None