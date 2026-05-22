#!/bin/bash
cd /home/josh/claw-code/DeFide
export JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64
export ANDROID_HOME=/home/josh/android-sdk
export GRADLE_USER_HOME=/home/josh/claw-code/DeFide/.gradle-home
exec ./gradlew assembleDebug >> /tmp/apk_build.log 2>&1
