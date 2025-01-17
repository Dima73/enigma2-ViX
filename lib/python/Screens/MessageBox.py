from enigma import eTimer, ePoint, eSize, getDesktop

from Components.ActionMap import HelpableActionMap
from Components.config import config
from Components.Label import Label
from Components.MenuList import MenuList
from Components.Pixmap import Pixmap, MultiPixmap
from Components.Sources.StaticText import StaticText
from Screens.HelpMenu import HelpableScreen
from Screens.Screen import Screen
from skin import parseScale, applySkinFactor


class MessageBox(Screen, HelpableScreen):
	TYPE_YESNO = 0
	TYPE_INFO = 1
	TYPE_WARNING = 2
	TYPE_ERROR = 3
	TYPE_MESSAGE = 4

	TYPE_PREFIX = {
		TYPE_YESNO: _("Question"),
		TYPE_INFO: _("Information"),
		TYPE_WARNING: _("Warning"),
		TYPE_ERROR: _("Error"),
		TYPE_MESSAGE: _("Message")
	}

	def __init__(self, session, text, type=TYPE_YESNO, timeout=0, close_on_any_key=False, default=True, enable_input=True, msgBoxID=None, picon=True, simple=False, wizard=False, list=None, skin_name=None, timeout_default=None, title=None):
		Screen.__init__(self, session)
		HelpableScreen.__init__(self)
		if text:
			self.text = _(text)
		else:
			self.text = text
		if type in range(self.TYPE_MESSAGE + 1):
			self.type = type
		else:
			self.type = self.TYPE_MESSAGE
		self.timeout = int(timeout)
		self.close_on_any_key = close_on_any_key
		if enable_input:
			self["actions"] = HelpableActionMap(self, ["MsgBoxActions", "DirectionActions"], {
				"cancel": (self.cancel, _("Cancel the selection")),
				"ok": (self.ok, _("Accept the current selection")),
				"alwaysOK": (self.alwaysOK, _("Always select OK")),
				"up": (self.up, _("Move up a line")),
				"down": (self.down, _("Move down a line")),
				"left": (self.left, _("Move up a page")),
				"right": (self.right, _("Move down a page"))
				# These actions are *ONLY* defined on OpenPLi!
				# I don't believe thay add any functionality even for OpenPLi.
				# "upRepeated": (self.up, _("Move up a line repeatedly")),
				# "downRepeated": (self.down, _("Move down a line repeatedly")),
				# "leftRepeated": (self.left, _("Move up a page repeatedly")),
				# "rightRepeated": (self.right, _("Move down a page repeatedly"))
			}, prio=-1, description=_("MessageBox Functions"))
		self.msgBoxID = msgBoxID
		# These six lines can go with new skins that only use self["icon"]...
		self["QuestionPixmap"] = Pixmap()
		self["QuestionPixmap"].hide()
		self["InfoPixmap"] = Pixmap()
		self["InfoPixmap"].hide()
		self["ErrorPixmap"] = Pixmap()
		self["ErrorPixmap"].hide()
		self["WarningPixmap"] = Pixmap()
		self["WarningPixmap"].hide()
		self["icon"] = MultiPixmap()
		self["icon"].hide()
		self.picon = picon
		if picon:
			# These five lines can go with new skins that only use self["icon"]...
			if self.type == self.TYPE_YESNO:
				self["QuestionPixmap"].show()
			elif self.type == self.TYPE_INFO:
				self["InfoPixmap"].show()
			elif self.type == self.TYPE_ERROR:
				self["ErrorPixmap"].show()
			elif self.type == self.TYPE_WARNING:
				self["WarningPixmap"].show()
			self["icon"].show()
		self.skinName = ["MessageBox"]
		if simple:
			self.skinName = ["MessageBoxSimple"] + self.skinName
		if wizard:
			self["rc"] = MultiPixmap()
			self["rc"].setPixmapNum(config.misc.rcused.value)
			self.skinName = ["MessageBoxWizard"]
		if isinstance(skin_name, str):
			self.skinName = [skin_name] + self.skinName
		if not list:
			list = []
		if type == self.TYPE_YESNO:
			if list:
				self.list = list
			elif default:
				self.list = [(_("Yes"), True), (_("No"), False)]
			else:
				self.list = [(_("No"), False), (_("Yes"), True)]
		else:
			self.list = []
		self.timeout_default = timeout_default
		self.baseTitle = title
		self.activeTitle = None
		self.timerRunning = False
		if timeout > 0:
			self.timerRunning = True
		self["text"] = Label(self.text)
		self["Text"] = StaticText(self.text)  # What is self["Text"] for?
		self["selectedChoice"] = StaticText()
		self["list"] = MenuList(self.list)
		if self.list:
			self["selectedChoice"].setText(self.list[0][0])
		else:
			self["list"].hide()
		self["key_help"] = StaticText(_("HELP"))
		self.timer = eTimer()
		self.timer.callback.append(self.processTimer)
		if self.layoutFinished not in self.onLayoutFinish:
			self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self["icon"].setPixmapNum(self.type)
		prefix = self.TYPE_PREFIX.get(self.type, _("Unknown"))
		if self.baseTitle is None:
			title = self.getTitle()
			if title:
				if "%s" in title:
					self.baseTitle = title % prefix
				else:
					self.baseTitle = title
			else:
				self.baseTitle = prefix
		elif "%s" in self.baseTitle:
			self.baseTitle = self.baseTitle % prefix
		self.setTitle(self.baseTitle)
		if self.timeout > 0:
			print("[MessageBox] Timeout set to %d seconds." % self.timeout)
			self.timer.start(25)

	def processTimer(self):
		# Check if the title has been externally changed and if so make it the dominant title.
		if self.activeTitle is None:
			self.activeTitle = self.getTitle()
			if "%s" in self.activeTitle:
				self.activeTitle = self.activeTitle % self.TYPE_PREFIX.get(self.type, _("Unknown"))
		if self.baseTitle != self.activeTitle:
			self.baseTitle = self.activeTitle
		if self.timeout > 0:
			if self.baseTitle:
				self.setTitle("%s (%d)" % (self.baseTitle, self.timeout))
			self.timer.start(1000)
			self.timeout -= 1
		else:
			self.stopTimer("Timeout!")
			if self.timeout_default is not None:
				self.close(self.timeout_default)
			else:
				self.ok()

	def stopTimer(self, reason):
		print("[MessageBox] %s" % reason)
		self.timer.stop()
		self.timeout = 0
		if self.baseTitle is not None:
			self.setTitle(self.baseTitle)

	def getListItemHeight(self):
		defaultItemHeight = 25  # if no itemHeight is present in the skin
		if self.list and hasattr(self["list"], "skinAttributes") and isinstance(self["list"].skinAttributes, list):
			for (attrib, value) in self["list"].skinAttributes:
				if attrib == "itemHeight":
					itemHeight = parseScale(value)  # if value does not parse (due to bad syntax in skin), itemHeight will be 0
					return itemHeight if itemHeight else defaultItemHeight
		return defaultItemHeight  # if itemHeight not in skinAttributes

	def getPixmapSize(self):
		defaultPixmapWidth = (53, 53)
		try:  # protect from skin errors
			return self["ErrorPixmap"].visible and hasattr(self["ErrorPixmap"], 'getSize') and isinstance(self["ErrorPixmap"].getSize(), tuple) and len(self["ErrorPixmap"].getSize()) and self["ErrorPixmap"].getSize() or \
				self["QuestionPixmap"].visible and hasattr(self["QuestionPixmap"], 'getSize') and isinstance(self["QuestionPixmap"].getSize(), tuple) and len(self["QuestionPixmap"].getSize()) and self["QuestionPixmap"].getSize() or \
				self["InfoPixmap"].visible and hasattr(self["InfoPixmap"], 'getSize') and isinstance(self["InfoPixmap"].getSize(), tuple) and len(self["InfoPixmap"].getSize()) and self["InfoPixmap"].getSize() or \
				self["WarningPixmap"].visible and hasattr(self["WarningPixmap"], 'getSize') and isinstance(self["WarningPixmap"].getSize(), tuple) and len(self["WarningPixmap"].getSize()) and self["WarningPixmap"].getSize() or \
				defaultPixmapWidth
		except Exception as err:
			print("[MessageBox] defaultPixmapWidth, %s: '%s'" % (type(err).__name__, err))
		return defaultPixmapWidth

	def autoResize(self):
		margin = applySkinFactor(4)
		separator = applySkinFactor(10)
		desktop_w = getDesktop(0).size().width()
		desktop_h = getDesktop(0).size().height()
		pixmapWidth = 0
		pixmapHeight = 0
		pixmapMargin = 0
		if self.picon:
			pixmapWidth, pixmapHeight = self.getPixmapSize()
			pixmapMargin = applySkinFactor(4)
		textsize = (0, 0)
		if self["text"].text:
			textsize = self["text"].getSize()
			if textsize[0] < textsize[1]:
				textsize = (textsize[1], textsize[0] + 10)
		listLen = len(self.list)
		itemheight = self.getListItemHeight()
		listMaxItems = int((desktop_h * 0.8 - textsize[1]) // itemheight)
		scrollbar = self["list"].instance.getScrollbarWidth() + 5 if listLen > listMaxItems else 0
		listWidth = int(min(self["list"].instance.getMaxItemTextWidth() + scrollbar, desktop_w * 0.9))
		count = min(listLen, listMaxItems)
		if textsize[1]:
			textsize = (textsize[0] + applySkinFactor(10), textsize[1] + applySkinFactor(2))
			if textsize[0] < listWidth:
				textsize = (listWidth, textsize[1])
		width = max(listWidth, textsize[0])
		listsize = (width, listMaxItems * itemheight)
		listPos = separator + (textsize[1] if textsize[1] > 0 else 0)
		# resize label
		self["text"].instance.resize(eSize(*textsize))
		self["text"].instance.move(ePoint(margin + pixmapWidth + pixmapMargin, 0))
		# move list
		self["list"].instance.resize(eSize(*listsize))
		self["list"].instance.move(ePoint(margin + pixmapWidth + pixmapMargin, listPos))

		wsizex = margin * 2 + width + pixmapWidth + pixmapMargin
		wsizey = max(listPos + (count * itemheight) + margin, pixmapMargin*2 + pixmapHeight)
		wsize = (wsizex, wsizey)
		self.instance.resize(eSize(*wsize))

		# center window
		self.instance.move(ePoint((desktop_w - wsizex) // 2, (desktop_h - wsizey) // 2))

	def cancel(self):
		for x in self["list"].list:
			# print "[MessageBox] DEBUG: (cancel) '%s' -> '%s'" % (str(x[0]), str(x[1]))
			# Should we be looking at the second element to get the boolean value rather than the word?
			if x[0].lower() == _('no') or x[0].lower() == _('false'):
				if len(x) > 2:
					x[2](None)
				break
		# Don't close again if the MessageBox was closed in the loop
		if hasattr(self, "execing"):
			self.close(False)

	def ok(self):
		if self["list"].getCurrent():
			self.goEntry(self["list"].getCurrent())
		else:
			self.close(True)

	def goEntry(self, entry=None):
		if not entry:
			entry = []
		if entry and len(entry) > 3 and isinstance(entry[1], str) and entry[1] == "CALLFUNC":
			arg = entry[3]
			entry[2](arg)
		elif entry and len(entry) > 2 and isinstance(entry[1], str) and entry[1] == "CALLFUNC":
			entry[2](None)
		elif entry:
			self.close(entry[1])
		else:
			self.close(False)

	def alwaysOK(self):
		if self["list"].list:
			for x in self["list"].list:
				# print "[MessageBox] DEBUG: (cancel) '%s' -> '%s'" % (str(x[0]), str(x[1]))
				# Should we be looking at the second element to get the boolean value rather than the word?
				if x[0].lower() == _('yes') or x[0].lower() == _('true'):
					if len(x) > 2:
						self.goEntry(x)
					else:
						self.close(True)
					break
		else:
			self.close(True)

	def up(self):
		self.move(self["list"].instance.moveUp)

	def down(self):
		self.move(self["list"].instance.moveDown)

	def left(self):
		self.move(self["list"].instance.pageUp)

	def right(self):
		self.move(self["list"].instance.pageDown)

	def move(self, direction):
		if self.timeout > 0:
			self.stopTimer("Timeout stopped by user input!")
		if self.close_on_any_key:
			self.close(True)
		self["list"].instance.moveSelection(direction)
		if self.list:
			self["selectedChoice"].setText(self["list"].getCurrent()[0])

	def __repr__(self):
		return "%s(%s)" % (str(type(self)), self.text if hasattr(self, "text") else "<title>")

	def getListWidth(self):
		return self["list"].instance.getMaxItemTextWidth()
