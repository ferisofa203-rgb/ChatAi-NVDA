# -*- coding: UTF-8 -*-

import wx
import threading

import ui

from .client import sendChat, AIClientError


class ChatDialog(wx.Dialog):

    def __init__(self, parent):
        super(ChatDialog, self).__init__(
            parent,
            title="AI Chat",
            size=(600, 500)
        )

        self.chatHistory = []
        self.lastResponse = ""
        self.isBusy = False

        self.buildUI()
        self.Bind(wx.EVT_SHOW, self.onShow)
        self.Centre()

    def buildUI(self):
        mainSizer = wx.BoxSizer(wx.VERTICAL)

        # Conversation label
        historyLabel = wx.StaticText(self, label="Chat history:")
        mainSizer.Add(historyLabel, 0, wx.LEFT | wx.RIGHT | wx.TOP, 5)

        # Conversation area
        self.historyBox = wx.TextCtrl(
            self,
            style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH2
        )
        self.historyBox.SetName("Chat history")
        mainSizer.Add(self.historyBox, 1, wx.EXPAND | wx.ALL, 5)

        # Input label
        inputLabel = wx.StaticText(self, label="Your message:")
        mainSizer.Add(inputLabel, 0, wx.LEFT | wx.RIGHT | wx.TOP, 5)

        # Input box
        self.inputBox = wx.TextCtrl(
            self,
            style=wx.TE_MULTILINE
        )
        self.inputBox.SetName("Your message")
        mainSizer.Add(self.inputBox, 0, wx.EXPAND | wx.ALL, 5)

        # Buttons
        buttonSizer = wx.BoxSizer(wx.HORIZONTAL)

        self.sendButton = wx.Button(self, label="Send")
        self.copyButton = wx.Button(self, label="Copy last reply")
        self.clearButton = wx.Button(self, label="Clear chat")
        self.closeButton = wx.Button(self, label="Close")

        buttonSizer.Add(self.sendButton, 0, wx.ALL, 5)
        buttonSizer.Add(self.copyButton, 0, wx.ALL, 5)
        buttonSizer.Add(self.clearButton, 0, wx.ALL, 5)
        buttonSizer.Add(self.closeButton, 0, wx.ALL, 5)

        mainSizer.Add(buttonSizer, 0, wx.CENTER)

        self.SetSizer(mainSizer)

        # Bind events
        self.sendButton.Bind(wx.EVT_BUTTON, self.onSend)
        self.copyButton.Bind(wx.EVT_BUTTON, self.onCopy)
        self.clearButton.Bind(wx.EVT_BUTTON, self.onClear)
        self.closeButton.Bind(wx.EVT_BUTTON, self.onClose)
        self.inputBox.Bind(wx.EVT_KEY_DOWN, self.onInputKeyDown)

    def onShow(self, event):
        if event.IsShown():
            wx.CallAfter(self.inputBox.SetFocus)
        event.Skip()

    def onInputKeyDown(self, event):
        keyCode = event.GetKeyCode()

        if keyCode in (wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER):
            if event.ShiftDown():
                self.inputBox.WriteText("\n")
            else:
                self.onSend(None)
            return

        event.Skip()

    # =========================
    # Core Logic
    # =========================

    def onSend(self, event):
        if self.isBusy:
            ui.message("Please wait for the current response.")
            return

        text = self.inputBox.GetValue().strip()
        if not text:
            ui.message("Message is empty.")
            return

        self.chatHistory.append({
            "role": "user",
            "content": text
        })

        self.appendToHistory("You: " + text)
        self.inputBox.SetValue("")

        self.isBusy = True
        self.sendButton.Disable()

        ui.message("Sending request...")

        thread = threading.Thread(target=self.processRequest)
        thread.daemon = True
        thread.start()

    def processRequest(self):
        try:
            reply = sendChat(self.chatHistory)
        except AIClientError as e:
            wx.CallAfter(self.onError, str(e))
            return

        wx.CallAfter(self.onResponse, reply)

    def onResponse(self, reply):
        self.chatHistory.append({
            "role": "assistant",
            "content": reply
        })

        self.lastResponse = reply

        self.appendToHistory("Assistant: " + reply)

        self.isBusy = False
        self.sendButton.Enable()

        self.historyBox.SetFocus()
        self.historyBox.SetInsertionPointEnd()
        self.historyBox.ShowPosition(self.historyBox.GetLastPosition())

    def onError(self, message):
        ui.message("Error: " + message)

        self.isBusy = False
        self.sendButton.Enable()
        self.inputBox.SetFocus()

    # =========================
    # UI Helpers
    # =========================

    def appendToHistory(self, text):
        current = self.historyBox.GetValue()
        if current:
            newText = current + "\n" + text
        else:
            newText = text

        self.historyBox.SetValue(newText)
        self.historyBox.SetInsertionPointEnd()
        self.historyBox.ShowPosition(self.historyBox.GetLastPosition())

    def onCopy(self, event):
        if not self.lastResponse:
            ui.message("No response to copy.")
            return

        if wx.TheClipboard.Open():
            wx.TheClipboard.SetData(wx.TextDataObject(self.lastResponse))
            wx.TheClipboard.Close()
            ui.message("Response copied to clipboard.")
        else:
            ui.message("Failed to access clipboard.")

    def onClear(self, event):
        self.chatHistory = []
        self.lastResponse = ""
        self.historyBox.SetValue("")
        ui.message("Chat cleared.")
        self.inputBox.SetFocus()

    def onClose(self, event):
        self.Destroy()