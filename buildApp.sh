#!/bin/bash
# Build script for DeFide Android app
# Sets required environment variables and runs the Gradle build.

set -e

cd /home/josh/claw-code/DeFide

export ANDROID_HOME="/home/josh/claw-code/DeFide/android-sdk"
export JAVA_HOME="/usr/lib/jvm/java-21-openjdk-amd64"
export GRADLE_USER_HOME="/home/josh/claw-code/DeFide/.gradle-home"

./gradlew assembleDebug
