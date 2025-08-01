# Better VF Export

File Format plug-in for Glyphs 3. Exports variable fonts from Glyphs 3 with better control for STAT and fvar tables.

## Define Axis Values in a VF Setting

The export plug-in expects a VF Setting with (optional) Axis Values in your exports.

1. In *Font Info > Exports,* add a *Variable Font Setting* through the plus menu at the bottom. (Or create a setting with the mekkablue script *OTVAR Maker.*)
2. Select the *Variable Font Setting* and add custom parameters called `Axis Values` for each axis you want in the `STAT` table. Usually you want all the axes defined in *Font Info > Font* plus the Italic axis.
3. The value of each *Axis Values* parameter starts with the axis tag, e.g., `opsz`, `wdth`, `wght`, `ital` followed by a semicolon.
4. For each axis, add all discrete axis values in a comma-separated list of `value=name` entries, for example: `opsz; 6=Caption, 12=Text, 48=Display`.
5. After an elidable entry, add an asterisk `*`. For example: `wdth; 75=Condensed, 100=Normal*, 125=Expanded`.
6. Connect style-linked values with `>`. For example: `ital; 0>1=Roman*`. If you have style-linked values, you do not need to repeat the respective discrete values.
7. Optionally, you can add ranges with `min:nominal:max` as value. For example: `‌wght; 200:200:250=Thin, 250:300:350=Light, 350:400:450=Regular*, 400>700=Regular*, 450:500:550=Medium, 550:600:650=Semibold, 650:700:750=Bold, 750:800:800=Extrabold`. Note that range values do not replace the style linkings, see the double entry for `Regular` in the example.
8. Drag the *Axis Values* parameters in the correct value. The order of the axes in `STAT` determines the sort order of styles in the font menu.

## No Italic duplication in fvar PS Names

The export plug-in also fixes italic PostScript names in the fvar table. It turns name table entries like `FamilyNameItalic-MediumItalic` into `FamilyNameItalic-Medium`.

## Installation

1. Open *Window > Plugin Manager* and install the *Better VF Export* plug-in from the Plugins tab. It requires the installation of the *Python* and *FontTools* modules.
2. Restart Glyphs.

## Usage Instructions

1. Open a multiple-master file with at least one VF Setting.
2. *File > Export > Better VF Export,* decide if you want to open the enclosing folder after export by clicking the checkbox. The plug-in will take all other settings (export destination, webfonts) from the default (built-in) VF export settings.
3. Press *Next.* The font will be exported.

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

