#!/usr/bin/env python3
"""Daemonize: runs gradlew assembleDebug as a background daemon, logs to /tmp/apk_build.log."""
import os, sys

LOG = "/tmp/apk_build.log"
CWD = "/home/josh/claw-code/DeFide"
GRADLEW = "/home/josh/claw-code/DeFide/gradlew"

log_file = open(LOG, "w", buffering=1)
pid = os.fork()
if pid > 0:
    log_file.close()
    sys.exit(0)

# Child: become session leader + background process
os.chdir(CWD)
os.setsid()

pid2 = os.fork()
if pid2 > 0:
    sys.exit(0)

# Grandchild: do the actual gradle exec with redirect
sys.stdout.flush()
sys.stderr.flush()
os.dup2(log_file.fileno(), 1)
os.dup2(log_file.fileno(), 2)
log_file.close()

os.execv("/bin/bash", [
    "/bin/bash", "-c",
    "JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64 "
    "ANDROID_HOME=/home/josh/.android-sdk "
    "GRADLE_USER_HOME=/home/josh/claw-code/DeFide/.gradle-home "
    "exec " + GRADLEW + " assembleDebug"
])
