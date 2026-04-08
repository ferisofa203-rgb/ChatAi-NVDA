# -*- coding: UTF-8 -*-

import os
import json
import tempfile
import threading
import webbrowser

import wx
import gui
import ui
import addonHandler

try:
	import urllib2
except ImportError:
	import urllib.request as urllib2

addonHandler.initTranslation()

UPDATE_URL = "https://raw.githubusercontent.com/ferisofa203-rgb/ChatAi-NVDA/main/update.json"


def getCurrentAddonVersion():
	try:
		addon = addonHandler.getCodeAddon()
		manifest = addon.manifest
		return str(manifest["version"]).strip()
	except Exception:
		return "0.0.0"


def normalizeVersion(version):
	parts = str(version).strip().split(".")
	result = []
	for part in parts:
		try:
			result.append(int(part))
		except Exception:
			result.append(0)
	return tuple(result)


def isRemoteVersionNewer(remoteVersion, localVersion):
	return normalizeVersion(remoteVersion) > normalizeVersion(localVersion)


def downloadText(url, timeout=10):
	response = urllib2.urlopen(url, timeout=timeout)
	data = response.read()
	if isinstance(data, bytes):
		data = data.decode("utf-8")
	return data


def downloadFile(url, targetPath, timeout=60):
	response = urllib2.urlopen(url, timeout=timeout)
	with open(targetPath, "wb") as f:
		f.write(response.read())


def showMessageBox(message, caption, style):
	gui.mainFrame.prePopup()
	try:
		return wx.MessageBox(message, caption, style, gui.mainFrame)
	finally:
		gui.mainFrame.postPopup()


def checkForUpdates(parent=None, manual=False):
	thread = threading.Thread(
		target=_checkForUpdatesWorker,
		args=(parent, manual)
	)
	thread.daemon = True
	thread.start()


def _checkForUpdatesWorker(parent=None, manual=False):
	try:
		rawData = downloadText(UPDATE_URL)
		info = json.loads(rawData)

		remoteVersion = str(info.get("version", "")).strip()
		downloadUrl = str(info.get("downloadUrl", "")).strip()
		changelog = str(info.get("changelog", "")).strip()
		homepage = str(info.get("homepage", "")).strip()

		localVersion = getCurrentAddonVersion()

		if not remoteVersion or not downloadUrl:
			if manual:
				wx.CallAfter(
					showMessageBox,
					_("Update information is incomplete."),
					_("Chat AI Update"),
					wx.OK | wx.ICON_ERROR
				)
			return

		if not isRemoteVersionNewer(remoteVersion, localVersion):
			if manual:
				wx.CallAfter(
					showMessageBox,
					_("You are already using the latest version."),
					_("Chat AI Update"),
					wx.OK | wx.ICON_INFORMATION
				)
			return

		message = _(
			"A new version of Chat AI is available.\n\n"
			"Current version: {current}\n"
			"New version: {new}\n\n"
			"Changelog:\n{changelog}\n\n"
			"Do you want to download and install it now?"
		).format(
			current=localVersion,
			new=remoteVersion,
			changelog=changelog if changelog else _("No changelog provided.")
		)

		wx.CallAfter(
			_askUserAndDownload,
			downloadUrl,
			remoteVersion,
			message,
			homepage
		)

	except Exception as e:
		if manual:
			wx.CallAfter(
				showMessageBox,
				_("Failed to check for updates:\n%s") % e,
				_("Chat AI Update"),
				wx.OK | wx.ICON_ERROR
			)


def _askUserAndDownload(downloadUrl, remoteVersion, message, homepage=""):
	gui.mainFrame.prePopup()
	try:
		result = wx.MessageBox(
			message,
			_("Chat AI Update"),
			wx.YES_NO | wx.ICON_INFORMATION,
			gui.mainFrame
		)
	finally:
		gui.mainFrame.postPopup()

	if result != wx.YES:
		return

	thread = threading.Thread(
		target=_downloadAndInstallWorker,
		args=(downloadUrl, remoteVersion, homepage)
	)
	thread.daemon = True
	thread.start()


def _downloadAndInstallWorker(downloadUrl, remoteVersion, homepage=""):
	try:
		ui.message(_("Downloading update, please wait."))

		tempDir = tempfile.gettempdir()
		fileName = "ChatAI-%s.nvda-addon" % remoteVersion
		filePath = os.path.join(tempDir, fileName)

		downloadFile(downloadUrl, filePath)

		if not os.path.isfile(filePath):
			raise RuntimeError(_("The update file was not found after download."))

		ui.message(_("Download complete. Opening the installer."))

		try:
			os.startfile(filePath)
		except Exception:
			webbrowser.open(filePath)

	except Exception as e:
		wx.CallAfter(
			showMessageBox,
			_("Failed to download or open the update:\n%s") % e,
			_("Chat AI Update"),
			wx.OK | wx.ICON_ERROR
		)