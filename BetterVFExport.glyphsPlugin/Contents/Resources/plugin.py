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
import objc
import os
import subprocess
import fontTools
from fontTools import ttLib
from fontTools.ttLib.tables import otTables
from GlyphsApp import Glyphs, DOCUMENTEXPORTED, FILE_MENU, INSTANCETYPEVARIABLE
from GlyphsApp.plugins import GeneralPlugin
from AppKit import NSMenuItem, NSImage


openInFinderPref = "com.mekkablue.BetterVFExport.openInFinder"
axisValuesParameterName = "Axis Values"


@objc.python_method
def designAxisRecordDict(statTable):
	axes = []
	if statTable.DesignAxisRecord:
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
def reportProblems(problems, instanceName=None, fontPath=None):
	"""
	Lists the problems in the Macro Window and brings it to the front.
	"""
	print("⚠️ Better VF Export: %i problem%s in the ‘%s’ parameter%s%s:" % (
		len(problems),
		"" if len(problems) == 1 else "s",
		axisValuesParameterName,
		"" if len(problems) == 1 else "s",
		" of ‘%s’" % instanceName if instanceName else "",
	))
	for problem in problems:
		print("   • %s" % problem)
	if fontPath:
		print("   Left the STAT table of %s untouched. Fix the parameter in Font Info → Exports and export again." % os.path.basename(fontPath))
	Glyphs.showMacroWindow()


@objc.python_method
def floatsFromCode(code, separator=None, count=None):
	"""
	Turns code into a list of count numbers, split at separator,
	or a single number if no separator is given.
	Returns None if the code does not hold exactly count numbers.
	"""
	if count is None:
		return None
	particles = code.split(separator) if separator else [code]
	if len(particles) != count:
		return None
	numbers = []
	for particle in particles:
		try:
			numbers.append(float(particle.strip()))
		except ValueError:
			return None
	return numbers


@objc.python_method
def formatAndNumbersFromCode(valueCode):
	"""
	Interprets the value part of an axis value entry:
		700>400 → (3, [700.0, 400.0]), style linking
		100:400:900 → (2, [100.0, 400.0, 900.0]), range
		400 → (1, [400.0]), discrete spot
	Returns the numbers as None if the code does not hold the expected amount of numbers.
	"""
	if ">" in valueCode:
		return 3, floatsFromCode(valueCode, separator=">", count=2)
	elif ":" in valueCode:
		return 2, floatsFromCode(valueCode, separator=":", count=3)
	else:
		return 1, floatsFromCode(valueCode, count=1)


@objc.python_method
def newAxisValue(valueFormat=None, numbers=None, axisIndex=None, valueNameID=None, flags=0):
	"""
	Builds a fontTools AxisValue out of the pieces parsed from an axis value entry.
	Returns None if anything is missing or does not add up.
	"""
	numberCounts = {1: 1, 2: 3, 3: 2}
	if valueFormat not in numberCounts.keys() or axisIndex is None or valueNameID is None:
		return None
	if not numbers or len(numbers) != numberCounts[valueFormat]:
		return None

	axisValue = otTables.AxisValue()
	axisValue.Format = valueFormat
	axisValue.AxisIndex = axisIndex
	axisValue.ValueNameID = valueNameID
	axisValue.Flags = flags

	if valueFormat == 3:  # STYLE LINKING
		axisValue.Value, axisValue.LinkedValue = numbers
	elif valueFormat == 2:  # RANGE
		axisValue.RangeMinValue, axisValue.NominalValue, axisValue.RangeMaxValue = numbers
	else:  # DISCRETE SPOT
		axisValue.Value = numbers[0]

	return axisValue


@objc.python_method
def parseAxisValuesParameter(parameterValue, axisTags=None):
	"""
	Parses the value of an Axis Values parameter, e.g. `wght; 400=Regular, 700>400=Bold*`.
	Returns a list of entries and a list of problem descriptions.
	The entries only carry parsed numbers and names, so the caller can bail out
	before anything in the font is touched.
	"""
	entries = []
	problems = []

	code = str(parameterValue).strip() if parameterValue else ""
	if not code:
		return entries, ["The parameter is empty, expected something like ‘wght; 400=Regular’."]
	if not axisTags:
		return entries, ["‘%s’: the font has no STAT axes to attach the values to." % code]

	codeParticles = code.split(";")
	if len(codeParticles) != 2:
		return entries, ["‘%s’: expected exactly one semicolon, as in ‘wght; 400=Regular’." % code]

	axisTag = codeParticles[0].strip()[:4]
	if axisTag not in axisTags:
		return entries, ["‘%s’: the font has no ‘%s’ axis, only %s." % (code, axisTag, ", ".join(axisTags))]
	axisIndex = axisTags.index(axisTag)

	for entryCode in codeParticles[1].split(","):
		entryCode = entryCode.strip()
		if not entryCode:
			problems.append("‘%s’: empty entry, perhaps a stray comma." % code)
			continue

		entryParticles = entryCode.split("=")
		if len(entryParticles) != 2:
			problems.append("‘%s’: expected exactly one equals sign in ‘%s’, as in ‘400=Regular’." % (code, entryCode))
			continue

		entryValues, entryName = [particle.strip() for particle in entryParticles]
		entryFlags = 0
		if entryName.endswith("*"):
			entryFlags = 2
			entryName = entryName[:-1].strip()
		if not entryName:
			problems.append("‘%s’: missing name in ‘%s’." % (code, entryCode))
			continue

		valueFormat, numbers = formatAndNumbersFromCode(entryValues)
		if numbers is None:
			problems.append("‘%s’: cannot read the numbers in ‘%s’." % (code, entryCode))
			continue

		entries.append({
			"axisIndex": axisIndex,
			"format": valueFormat,
			"numbers": numbers,
			"name": entryName,
			"flags": entryFlags,
		})

	return entries, problems


@objc.python_method
def parameterToSTAT(variableFontExport, font, fontPath):
	if "STAT" not in font:
		return

	statTable = font["STAT"].table
	axisTags = [axisInfo["tag"] for axisInfo in designAxisRecordDict(statTable)]

	# parse everything first, so a typo cannot cripple the STAT table:
	entries = []
	problems = []
	for parameter in variableFontExport.customParameters:
		if parameter.name == axisValuesParameterName and parameter.active:
			parameterEntries, parameterProblems = parseAxisValuesParameter(parameter.value, axisTags=axisTags)
			entries.extend(parameterEntries)
			problems.extend(parameterProblems)

	if problems:
		reportProblems(problems, instanceName=variableFontExport.name, fontPath=fontPath)
		return

	if not entries:
		# no active parameter, so keep the STAT table Glyphs built:
		return

	nameTable = font["name"]
	nameDict, highestID = nameDictAndHighestNameID(nameTable)

	# collect the names and build the axis values before we change anything:
	namesToAdd = []
	newAxisValues = []
	for entry in entries:
		entryName = entry["name"]
		if entryName not in nameDict.keys():
			highestID += 1
			nameDict[entryName] = highestID
			namesToAdd.append((highestID, entryName))

		axisValue = newAxisValue(
			valueFormat=entry["format"],
			numbers=entry["numbers"],
			axisIndex=entry["axisIndex"],
			valueNameID=nameDict[entryName],
			flags=entry["flags"],
		)
		if axisValue is None:
			reportProblems(
				["Cannot build an axis value for ‘%s’." % entryName],
				instanceName=variableFontExport.name,
				fontPath=fontPath,
			)
			return
		newAxisValues.append(axisValue)

	# now change the font:
	for nameID, entryName in namesToAdd:
		nameTable.addName(entryName, platforms=((3, 1, 1033), ), minNameID=nameID - 1)

	if statTable.AxisValueArray is None:
		statTable.AxisValueArray = otTables.AxisValueArray()
	statTable.AxisValueArray.AxisValue = newAxisValues
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

		if "GLYPHS_HEADLESS" in os.environ:
			return

		# menu item
		newMenuItem = NSMenuItem.new()
		newMenuItem.setTitle_(self.name)

		image = None
		try:
			image = NSImage.imageWithSystemSymbolName_accessibilityDescription_("checkmark", "checkmark")
			newMenuItem.setImage_(image)
		except:
			newMenuItem.setState_(True)
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
		if "GLYPHS_HEADLESS" not in os.environ and Glyphs.defaults[openInFinderPref] and os.path.exists(firstExportedFontPath):
			subprocess.call(["open", "-R", firstExportedFontPath])

		return True, "VF exported successfully."


	@objc.python_method
	def __del__(self):
		Glyphs.removeCallback(self.fontsExported_, DOCUMENTEXPORTED)


	@objc.python_method
	def __file__(self):
		"""Please leave this method unchanged"""
		return __file__
