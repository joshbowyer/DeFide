#!/bin/bash
cd /home/josh/claw-code/DeFide
export JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64
export GRADLE_USER_HOME=/home/josh/claw-code/DeFide/.gradle-home
export ANDROID_HOME=/home/josh/claw-code/DeFide/android-sdk
export ANDROID_SDK_ROOT=/home/josh/claw-code/DeFide/android-sdk
/home/josh/claw-code/DeFide/.gradle-home/wrapper/dists/gradle-8.11.1-bin/bpt9gzteqjrbo1mjrsomdt32c/gradle-8.11.1/bin/gradle assembleDebug --no-daemon -Dorg.gradle.jvmargs="-Xmx4g" -Pandroid.sdk=/home/josh/claw-code/DeFide/android-sdk
