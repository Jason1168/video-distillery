#!/bin/bash
# Install the local 08:15 collector. It writes a digest; it does not judge films.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LABEL="com.jason.film-craft-distill"
PLIST="${HOME}/Library/LaunchAgents/${LABEL}.plist"
PYTHON="/usr/bin/python3"
FFMPEG_DIR=""
if command -v ffmpeg >/dev/null 2>&1; then
  FFMPEG_DIR="$(cd "$(dirname "$(command -v ffmpeg)")" && pwd)"
fi
mkdir -p "${HOME}/Library/LaunchAgents" "${ROOT}/library/logs"

cat > "${PLIST}" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>${LABEL}</string>
  <key>ProgramArguments</key>
  <array>
    <string>${PYTHON}</string>
    <string>${ROOT}/scripts/daily.py</string>
  </array>
  <key>WorkingDirectory</key>
  <string>${ROOT}</string>
  <key>StartCalendarInterval</key>
  <dict>
    <key>Hour</key>
    <integer>8</integer>
    <key>Minute</key>
    <integer>15</integer>
  </dict>
  <key>RunAtLoad</key>
  <false/>
  <key>StandardOutPath</key>
  <string>${ROOT}/library/logs/daily.log</string>
  <key>StandardErrorPath</key>
  <string>${ROOT}/library/logs/daily.err</string>
  <key>EnvironmentVariables</key>
  <dict>
    <key>PATH</key>
    <string>${FFMPEG_DIR:+${FFMPEG_DIR}:}/usr/bin:/bin:/usr/sbin:/sbin</string>
  </dict>
</dict>
</plist>
EOF

UID_NUM="$(id -u)"
launchctl bootout "gui/${UID_NUM}" "${PLIST}" 2>/dev/null || true
launchctl bootstrap "gui/${UID_NUM}" "${PLIST}"
launchctl enable "gui/${UID_NUM}/${LABEL}"
echo "installed ${PLIST}"
echo "next run: local 08:15, digest in ${ROOT}/library/digests/"
