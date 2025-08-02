# encoding: utf-8

###########################################################################################################
#
#
# General Plugin
#
# Read the docs:
# https://github.com/schriftgestalt/GlyphsSDK/tree/master/Python%20Templates/General%20Plugin
#
#
###########################################################################################################

from __future__ import division, print_function, unicode_literals
import objc, os, subprocess, fontTools
from fontTools import ttLib
from GlyphsApp import Glyphs, DOCUMENTEXPORTED, FILE_MENU, INSTANCETYPEVARIABLE
from GlyphsApp.plugins import GeneralPlugin
from AppKit import NSMenuItem


openInFinderPref = "com.mekkablue.BetterVFExport.openInFinder"
axisValuesParameterName = "Axis Values"


@objc.python_method
def designAxisRecordDict(statTable):
	axes = []
	for axis in statTable.DesignAxisRecord.Axis:
		axes.append({
			"nameID": axis.AxisNameID,
			"tag": axis.AxisTag,
			"ordering": axis.AxisOrdering,
		})
	return axes


@objc.python_method
def nameDictAndHighestNameID(nameTable):
	nameDict = {}
	highestID = 255
	for nameTableEntry in nameTable.names:
		nameID = nameTableEntry.nameID
		if nameID > highestID:
			highestID = nameID
		nameValue = nameTableEntry.toStr()
		if nameValue not in nameDict.keys():
			nameDict[nameValue] = nameID
	return nameDict, highestID


@objc.python_method
def parameterToSTAT(variableFontExport, font, fontPath):
	changed = False

	nameTable = font["name"]
	nameDict, highestID = nameDictAndHighestNameID(nameTable)
	statTable = font["STAT"].table
	axes = designAxisRecordDict(statTable)

	newAxisValues = []
	for parameter in variableFontExport.customParameters:
		if parameter.name == axisValuesParameterName and parameter.active:
			changed = True
			
			statCode = parameter.value
			axisTag, axisValueCode = statCode.split(";")
			axisTag = axisTag.strip()
			for i, axisInfo in enumerate(axes):
				if axisTag == axisInfo["tag"]:
					axisIndex = i
					break

			if len(axisTag) > 4:
				axisTag = axisTag[:4]

			for entryCode in axisValueCode.split(","):
				newAxisValue = fontTools.ttLib.tables.otTables.AxisValue()
				entryValues, entryName = entryCode.split("=")
				entryName = entryName.strip()
				entryFlags = 0
				if entryName.endswith("*"):
					entryFlags = 2
					entryName = entryName[:-1]

				if entryName in nameDict.keys():
					entryValueNameID = nameDict[entryName]
				else:
					# add name entry:
					highestID += 1
					entryValueNameID = highestID
					nameTable.addName(entryName, platforms=((3, 1, 1033), ), minNameID=highestID - 1)
					nameDict[entryName] = entryValueNameID

				if ">" in entryValues:  # Format 3, STYLE LINKING
					entryValue, entryLinkedValue = [float(x.strip()) for x in entryValues.split(">")]
					newAxisValue.Format = 3
					newAxisValue.AxisIndex = axisIndex
					newAxisValue.ValueNameID = entryValueNameID
					newAxisValue.Flags = entryFlags
					newAxisValue.Value = entryValue
					newAxisValue.LinkedValue = entryLinkedValue

				elif ":" in entryValues:  # Format 2, RANGE
					entryRangeMinValue, entryNominalValue, entryRangeMaxValue = [float(x.strip()) for x in entryValues.split(":")]
					newAxisValue.Format = 2
					newAxisValue.AxisIndex = axisIndex
					newAxisValue.ValueNameID = entryValueNameID
					newAxisValue.Flags = entryFlags
					newAxisValue.RangeMinValue = entryRangeMinValue
					newAxisValue.NominalValue = entryNominalValue
					newAxisValue.RangeMaxValue = entryRangeMaxValue

				else:  # Format 1, DISCRETE SPOT
					entryValue = float(entryValues.strip())
					newAxisValue.Format = 1
					newAxisValue.AxisIndex = axisIndex
					newAxisValue.ValueNameID = entryValueNameID
					newAxisValue.Flags = entryFlags
					newAxisValue.Value = entryValue

				newAxisValues.append(newAxisValue)

	statTable.AxisValueArray.AxisValue = newAxisValues
	if changed:
		font.save(fontPath, reorderTables=False)


@objc.python_method
def fixItalicFvar(font, fontPath):
	anythingChanged = False

	nameTable = font["name"]
	for nameTableEntry in nameTable.names:
		nameID = nameTableEntry.nameID
		nameValue = nameTableEntry.toStr()
		oldName = nameValue
		if nameID in (4, 6, 17):
			for oldParticle in ("Regular Italic", "RegularItalic"):
				if oldParticle in nameValue:
					nameValue = nameValue.replace(oldParticle, "Italic")
		if nameID in (3, 6) or nameID > 255:
			oldName = nameValue
			if "Italic-" in nameValue and nameValue.count("Italic") > 1:
				particles = nameValue.split("-")
				for i in range(1, len(particles)):
					particles[i] = particles[i].replace("Italic", "").strip()
					if len(particles[i]) == 0:
						particles[i] = "Regular"
				nameValue = "-".join(particles)
		if nameValue != oldName:
			nameTableEntry.string = nameValue
			anythingChanged = True
	
	if anythingChanged:
		font.save(fontPath, reorderTables=False)


class BetterVFExportCallback(GeneralPlugin):

	@objc.python_method
	def settings(self):
		self.name = Glyphs.localize({
			'en': 'Better VF Export',
			'de': 'Besserer VF-Export',
			'fr': 'Meilleure exportation de police variable',
			'es': 'Mejor exportación de fuente variable',
			'pt': 'Melhor exportação de fonte variavel',
		})


	@objc.python_method
	def start(self):
		# pref
		Glyphs.registerDefault(openInFinderPref, True)
		
		# callback
		Glyphs.addCallback(self.fontsExported_, DOCUMENTEXPORTED)
		
		active = Glyphs.localize({
			'en': 'Active',
			'de': 'aktiv',
			'fr': 'activée',
			'es': 'activada',
			'pt': 'ativada',
		})
		
		# menu item
		if Glyphs.versionNumber >= 3.3:
			newMenuItem = NSMenuItem(f"☑️ {self.name} {active}", callback=None, target=None)
		else:
			newMenuItem = NSMenuItem(f"☑️ {self.name} {active}", None)
		Glyphs.menu[FILE_MENU].append(newMenuItem)


	def fontsExported_(self, info):
		exportInfo = info.object()
		instance = exportInfo["instance"]
		if instance.type != INSTANCETYPEVARIABLE:
			return False, None
			
		fontPaths = exportInfo["fontFilePaths"]
		for fontPath in fontPaths:
			font = ttLib.TTFont(fontPath)
			# FIX STAT
			parameterToSTAT(instance, font, fontPath)
			# FIX FVAR
			fixItalicFvar(font, fontPath)

		firstExportedFontPath = exportInfo["fontFilePath"]
		if Glyphs.defaults[openInFinderPref] and os.path.exists(firstExportedFontPath):
			subprocess.call(["open", "-R", firstExportedFontPath])
		
		return True, "VF exported successfully."


	@objc.python_method
	def __del__(self):
		Glyphs.removeCallback(self.fontsExported_, DOCUMENTEXPORTED)


	@objc.python_method
	def __file__(self):
		"""Please leave this method unchanged"""
		return __file__
