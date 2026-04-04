#!/bin/bash
# Build script to package the addon and generate Kodi repository files

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

ADDON_ID="plugin.video.freehit"
ADDON_SRC="$ADDON_ID"
REPO_DIR="repo"

# Clean previous build
rm -rf "$REPO_DIR"
mkdir -p "$REPO_DIR/$ADDON_ID" "$REPO_DIR/repository.freehit"

# Copy addon files
cp -r "$ADDON_SRC"/* "$REPO_DIR/$ADDON_ID/"

# Create addon zip
cd "$REPO_DIR"
zip -r "./$ADDON_ID-1.0.0.zip" "$ADDON_ID"
cd ..

# Copy kodi repository files
cp -r repository.freehit/* "$REPO_DIR/repository.freehit/" 2>/dev/null || true

# Create repository addon zip
cd "$REPO_DIR"
zip -r "./repository.freehit-1.0.0.zip" repository.freehit
cd ..

# Generate addons.xml
cat > "$REPO_DIR/addons.xml" << 'XMLEOF'
<?xml version="1.0" encoding="UTF-8"?>
<addons>
    <addon id="plugin.video.freehit" name="Freehit" version="1.0.0" provider-name="freehit.eu">
        <requires>
            <import addon="xbmc.python" version="3.0.0"/>
            <import addon="script.module.requests"/>
            <import addon="inputstream.adaptive" optional="true"/>
            <import addon="script.module.inputstreamhelper" optional="true"/>
        </requires>
        <extension point="xbmc.python.pluginsource" library="main.py">
            <provides>video</provides>
        </extension>
        <extension point="xbmc.service" library="service.py" start="startup"/>
        <extension point="xbmc.addon.metadata">
            <reuselanguageinvoker>false</reuselanguageinvoker>
            <summary lang="en_GB">Watch live cricket streaming from freehit.eu</summary>
            <description lang="en_GB">Stream live cricket matches including IPL, PSL, and international cricket from freehit.eu. Features multiple quality options, EPG/schedule support, and live match notifications.</description>
            <platform>all</platform>
            <license>GPL-2.0-or-later</license>
            <news>v1.0.0
- Initial release
- Live cricket streaming from freehit.eu
- Multiple stream quality options
- EPG/schedule support
- Live match notifications
- Multi-source fallback support</news>
            <assets>
                <icon>icon.png</icon>
                <fanart>fanart.jpg</fanart>
            </assets>
        </extension>
    </addon>
    <addon id="repository.freehit" name="Freehit Repository" version="1.0.0" provider-name="freehit.eu">
        <extension point="xbmc.addon.repository" name="Freehit Repository">
            <dir>
                <info compressed="false">https://github.com/freehit-cricket/freehit.eu/raw/main/repo/addons.xml</info>
                <checksum>https://github.com/freehit-cricket/freehit.eu/raw/main/repo/addons.xml.md5</checksum>
                <datadir zip="true">https://github.com/freehit-cricket/freehit.eu/raw/main/repo/</datadir>
            </dir>
        </extension>
        <extension point="xbmc.addon.metadata">
            <summary lang="en_GB">Repository for Freehit add-on</summary>
            <description lang="en_GB">Watch live cricket streaming from freehit.eu</description>
            <platform>all</platform>
        </extension>
    </addon>
</addons>
XMLEOF

# Generate MD5 checksum
md5sum "$REPO_DIR/addons.xml" | awk '{print $1}' > "$REPO_DIR/addons.xml.md5"

# Copy repo zip to docs
mkdir -p docs
cp "$REPO_DIR/repository.freehit-1.0.0.zip" docs/

echo "Build complete!"
echo "Addon zip: $REPO_DIR/$ADDON_ID-1.0.0.zip"
echo "Repo zip: $REPO_DIR/repository.freehit-1.0.0.zip"
echo "Repo files: $REPO_DIR/"
echo "Docs: docs/"
