#!/bin/bash
# Combined build: database + APK
set -e
cd /home/josh/claw-code/DeFide

export JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64
export ANDROID_HOME=/home/josh/.android-sdk
export GRADLE_USER_HOME=/home/josh/claw-code/DeFide/.gradle-home

LOG_COMPILE="/tmp/compile.log"
LOG_APK="/tmp/apk_build.log"

echo "=== Step 1: Compiling database ===" >> "$LOG_COMPILE"
python3 scripts/compile_content.py >> "$LOG_COMPILE" 2>&1
echo "DB done: $(date)" >> "$LOG_COMPILE"

echo "=== Step 2: Building APK ===" >> "$LOG_APK"
./gradlew assembleDebug >> "$LOG_APK" 2>&1
echo "APK done: $(date)" >> "$LOG_APK"
echo "EXIT: $?" >> "$LOG_APK"
