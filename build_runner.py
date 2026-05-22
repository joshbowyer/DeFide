#!/usr/bin/env python3
import subprocess, os

os.chdir("/home/josh/claw-code/DeFide")
env = dict(os.environ)
env["JAVA_HOME"] = "/usr/lib/jvm/java-21-openjdk-amd64"
env["ANDROID_HOME"] = "/home/josh/.android-sdk"
env["GRADLE_USER_HOME"] = "/home/josh/claw-code/DeFide/.gradle-home"
env["GRADLE_HOME"] = "/home/josh/claw-code/DeFide/.gradle-home"

log = open("/tmp/apk_build.log", "w", buffering=1)
proc = subprocess.Popen(
    ["./gradlew", "assembleDebug"],
    env=env,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    cwd="/home/josh/claw-code/DeFide",
)
for line in proc.stdout:
    log.write(line.decode("utf-8", errors="replace"))
    log.flush()
proc.wait()
log.write(f"\nEXIT: {proc.returncode}\n")
log.close()
open("/tmp/build_done", "w").close()
