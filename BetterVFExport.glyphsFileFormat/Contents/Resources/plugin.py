# encoding: utf-8

###########################################################################################################
#
#
# File Format Plugin
# Implementation for exporting fonts through the Export dialog
#
# Read the docs:
# https://github.com/schriftgestalt/GlyphsSDK/tree/master/Python%20Templates/File%20Format
#
# For help on the use of Xcode:
# https://github.com/schriftgestalt/GlyphsSDK/tree/master/Python%20Templates
#
#
###########################################################################################################

import objc
import os, subprocess, fontTools
from fontTools import ttLib
from GlyphsApp import Glyphs, INSTANCETYPEVARIABLE, VARIABLE, PLAIN, WOFF, WOFF2
from GlyphsApp.plugins import FileFormatPlugin

openInFinderPref = "com.mekkablue.BetterVFExport.openInFinder"
axisValuesParameterName = "Axis Values"


@objc.python_method
def currentOTVarExportPath():
	exportPath = Glyphs.defaults["GXExportPathManual"]
	if Glyphs.defaults["GXExportUseExportPath"]:
		exportPath = Glyphs.defaults["GXExportPath"]
	return exportPath


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


class BetterVFExport(FileFormatPlugin):
	# Definitions of IBOutlets
	dialog = objc.IBOutlet()
	openInFinderCheckBox = objc.IBOutlet()

	@objc.python_method
	def settings(self):
		self.name = Glyphs.localize({
			'en': 'Better VF Export',
		})
		self.icon = 'IconTemplate'
		self.toolbarPosition = 100

		# Load .nib dialog (with .extension)
		self.loadNib('IBdialog', __file__)


	@objc.python_method
	def start(self):
		Glyphs.registerDefault(openInFinderPref, True)
		self.openInFinderCheckBox.setState_(Glyphs.defaults[openInFinderPref])


	# Example function. You may delete it
	@objc.IBAction
	def setOpenInFinder_(self, sender):
		Glyphs.defaults[openInFinderPref] = bool(sender.intValue())


	@objc.python_method
	def export(self, glyphsFont):
		currentExportPath = currentOTVarExportPath()
		variableFontSettings = []
		for instance in glyphsFont.instances:
			if instance.type == INSTANCETYPEVARIABLE and instance.active:
				variableFontSettings.append(instance)
		if not variableFontSettings:
			return False, "No VF Setting found in Font Info → Exports."
		
		for i in variableFontSettings:
			filePath = currentExportPath
			subFolder = i.customParameters["Export Folder"]
			if subFolder:
				filePath = os.path.join(filePath, subFolder)
			filePath = os.path.join(filePath, i.fileName())
			filePath, _ = os.path.splitext(filePath)

			containers = [PLAIN]
			checkPaths = [filePath + ".ttf"]
			if Glyphs.defaults["GXExportWOFF"]:
				containers.append(WOFF)
				checkFiles.append(filePath + ".woff")
			if Glyphs.defaults["GXExportWOFF2"]:
				containers.append(WOFF2)
				checkFiles.append(filePath + ".woff2")

			# GENERATE VF
			i.generate(
				format=VARIABLE,
				fontPath=currentExportPath,
				autoHint=False,
				removeOverlap=False,
				useSubroutines=False,
				useProductionNames=True,
				containers=containers,
				decomposeSmartStuff=True,
			)
			
			for fontPath in checkPaths:
				font = ttLib.TTFont(fontPath)

				# FIX STAT
				parameterToSTAT(i, font, fontPath)

				# FIX FVAR
				fixItalicFvar(font, fontPath)


		if Glyphs.defaults[openInFinderPref] and os.path.exists(currentExportPath):
			subprocess.call(["open", currentExportPath])
		
		return True, "VF exported successfully."

	@objc.python_method
	def __file__(self):
		"""Please leave this method unchanged"""
		return __file__
