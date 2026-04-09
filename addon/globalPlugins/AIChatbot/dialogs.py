# -*- coding: UTF-8 -*-

import wx
import threading
import ui

from .client import sendChat, AIClientError


class ChatDialog(wx.Dialog):

	def __init__(self, parent):
		super(ChatDialog, self).__init__(
			parent,
			title="Chat AI",
			size=(600, 500)
		)

		self.chatHistory = []
		self.lastResponse = ""
		self.isBusy = False

		self.buildUI()
		self.Bind(wx.EVT_SHOW, self.onShow)
		self.Bind(wx.EVT_CHAR_HOOK, self.onCharHook)
		self.Centre()

	def buildUI(self):
		mainSizer = wx.BoxSizer(wx.VERTICAL)

		historyLabel = wx.StaticText(self, label="Chat history:")
		mainSizer.Add(historyLabel, 0, wx.LEFT | wx.RIGHT | wx.TOP, 5)

		self.historyBox = wx.TextCtrl(
			self,
			style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH2
		)
		self.historyBox.SetName("Chat history")
		mainSizer.Add(self.historyBox, 1, wx.EXPAND | wx.ALL, 5)

		inputLabel = wx.StaticText(self, label="Your message:")
		mainSizer.Add(inputLabel, 0, wx.LEFT | wx.RIGHT | wx.TOP, 5)

		self.inputBox = wx.TextCtrl(
			self,
			style=wx.TE_MULTILINE
		)
		self.inputBox.SetName("Your message")
		mainSizer.Add(self.inputBox, 0, wx.EXPAND | wx.ALL, 5)

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

		self.sendButton.Bind(wx.EVT_BUTTON, self.onSend)
		self.copyButton.Bind(wx.EVT_BUTTON, self.onCopy)
		self.clearButton.Bind(wx.EVT_BUTTON, self.onClear)
		self.closeButton.Bind(wx.EVT_BUTTON, self.onClose)
		self.inputBox.Bind(wx.EVT_KEY_DOWN, self.onInputKeyDown)

	def onShow(self, event):
		if event.IsShown():
			self.Raise()
			wx.CallLater(150, self.setInitialFocus)
		event.Skip()

	def setInitialFocus(self):
		try:
			if self and self.IsShownOnScreen():
				self.inputBox.SetFocus()
				self.inputBox.SetInsertionPointEnd()
		except Exception:
			pass

	def onCharHook(self, event):
		keyCode = event.GetKeyCode()
		if keyCode == wx.WXK_ESCAPE:
			self.Close()
			return
		event.Skip()

	def onInputKeyDown(self, event):
		keyCode = event.GetKeyCode()
		if keyCode in (wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER):
			if event.ShiftDown():
				event.Skip()
				return
			self.onSend(None)
			return
		event.Skip()

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
		self.appendToHistory("You", text)
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
		self.appendToHistory("Asisten", reply)

		self.isBusy = False
		self.sendButton.Enable(True)
		self.historyBox.SetFocus()

	def onError(self, message):
		ui.message("Error: " + message)
		self.isBusy = False
		self.sendButton.Enable()
		self.setInitialFocus()

	def appendToHistory(self, speaker, text):
		text = text.replace("\r\n", "\n").replace("\r", "\n")
		lines = [line for line in text.split("\n") if line.strip() != ""]
		cleanText = "\n".join(lines).strip()

		entry = "%s: %s" % (speaker, cleanText)
		current = self.historyBox.GetValue().replace("\r\n", "\n").replace("\r", "\n").rstrip("\n")

		if current:
			newText = current + "\n" + entry
		else:
			newText = entry

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
		self.setInitialFocus()

	def onClose(self, event):
		self.Destroy()