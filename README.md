# Better VF Export

Plug-in for Glyphs 3. Changes the variable font export in Glyphs 3 so that you have better control over `STAT` and `fvar` table entries.

## Define Axis Values in a VF Setting

The plug-in expects a VF Setting with (optional) Axis Values in your exports.

1. In *Font Info > Exports,* add a *Variable Font Setting* through the plus menu at the bottom. (Or create a setting with the mekkablue script *OTVAR Maker.*)
2. Select the *Variable Font Setting* and add custom parameters called `Axis Values` for each axis you want in the `STAT` table. Usually you want all the axes defined in *Font Info > Font* plus the Italic axis.
3. The value of each *Axis Values* parameter starts with the axis tag, e.g., `opsz`, `wdth`, `wght`, `ital` followed by a semicolon.
4. For each axis, add all discrete axis values in a comma-separated list of `value=name` entries, for example: `opsz; 6=Caption, 12=Text, 48=Display`.
5. After an elidable entry, add an asterisk `*`. For example: `wdth; 75=Condensed, 100=Normal*, 125=Expanded`.
6. Connect style-linked values with `>`. For example: `ital; 0>1=Roman*`. If you have style-linked values, you do not need to repeat the respective discrete values.
7. Optionally, you can add ranges with `min:nominal:max` as value. For example: `‌wght; 200:200:250=Thin, 250:300:350=Light, 350:400:450=Regular*, 400>700=Regular*, 450:500:550=Medium, 550:600:650=Semibold, 650:700:750=Bold, 750:800:800=Extrabold`. Note that range values do not replace the style linkings, see the double entry for `Regular` in the example. (Currently, I know of no UI that properly supports STAT table ranges.)
8. Drag the *Axis Values* parameters in the correct order. That’s because the order of the axes in `STAT` determines the sort order of styles in the font menu. Unless you know what you are doing, you want `opsz` first, then `wdth`, then `wght`, and finally `ital` (or `slnt`).

### Example Axis Values

Four-axis font with axes for optical size, width, weight and italics. For each axis, add an *Axis Values* parameter in the *Variable Font Setting* in *File > Font Info > Exports.* Their values could be like this:

```text
opsz; 6=Caption, 12=Text, 48=Display
wdth; 75=Condensed, 100=Normal*, 125=Expanded
wght; 200=Thin, 300=Light, 400>700=Regular*, 500=Medium, 600=Semibold, 700=Bold, 800=Extrabold
ital; 0>1=Roman*, 1=Italic
```

![BetterVFExportFontInfoScreenshot.png](Font Info window with Exports tab open, Variable Font Setting with Axis Values parameters)

## No Italic duplication in fvar PS Names

The export plug-in fixes italic PostScript names in the `fvar` table. It turns name table entries like `FamilyNameItalic-MediumItalic` into `FamilyNameItalic-Medium`.

Note that the respective changes happen entirely in the `name` table.

## Installation

1. Open *Window > Plugin Manager* and install the *Better VF Export* plug-in from the *Plugins* tab. It requires the installation of the *Python* and *FontTools* modules.
2. Restart Glyphs.

After the restart you should see a note at the bottom of your *File* menu that confirms that Better VF Export is active.

## Usage Instructions

1. Open a multiple-master file with at least one VF Setting, if possible including Axis Values parameters.
2. Choose *File > Export > Variable Fonts,* pick your settings as usual in the upcoming dialog, and press *Next.* 

The font(s) will be exported and Better VF Export will correct `fvar`, `STAT` and `name` tables where necessary. By default, it will reveal the first of the exported fonts in Finder.

If you do not want that, paste the following line *Window > Macro Panel* and press *Run:*

```python
Glyphs.defaults["com.mekkablue.BetterVFExport.openInFinder"] = False
```

To reset this setting to its default, do the same with this line:

```python
del Glyphs.defaults["com.mekkablue.BetterVFExport.openInFinder"]
```


## Requirements

The plugin works in Glyphs 3.3 or later, and has been tested on macOS Sequoia 15.5. Perhaps it works on earlier versions too, but I cannot guarantee that.

## License

Copyright 2025 Rainer Erich Scheichelbauer (@mekkablue).
Based on sample code by Georg Seifert (@schriftgestalt) and Florian Pircher (@florianpircher).

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

See the License file included in this repository for further details.

