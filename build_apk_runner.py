#!/usr/bin/env python3
"""Build APK with fresh source, survive context swaps."""
import subprocess, os, sys, time

CWD = "/home/josh/claw-code/DeFide"
LOG = "/tmp/apk_build.log"
ENV = dict(os.environ)
ENV["JAVA_HOME"] = "/usr/lib/jvm/java-21-openjdk-amd64"
ENV["ANDROID_HOME"] = "/home/josh/.android-sdk"
ENV["GRADLE_USER_HOME"] = "/home/josh/claw-code/DeFide/.gradle-home"

def log(msg):
    ts = time.strftime("%H:%M:%S")
    line = f"[{ts}] {msg}\n"
    with open(LOG, "a") as f:
        f.write(line)
    print(msg, flush=True)

def main():
    log("=== APK Build starting ===")
    log(f"JAVA_HOME: {ENV['JAVA_HOME']}")
    log(f"ANDROID_HOME: {ENV['ANDROID_HOME']}")

    logfile = open(LOG, "a", buffering=1)
    proc = subprocess.Popen(
        ["./gradlew", "assembleDebug", "--no-daemon"],
        env=ENV,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        cwd=CWD,
    )

    for line in proc.stdout:
        decoded = line.decode("utf-8", errors="replace")
        logfile.write(decoded)
        logfile.flush()
        sys.stdout.write(decoded)
        sys.stdout.flush()

    retcode = proc.wait()
    log(f"=== APK Build finished: exit {retcode} ===")
    logfile.close()

    if retcode == 0:
        apk = f"{CWD}/app/build/outputs/apk/debug/app-debug.apk"
        if os.path.exists(apk):
            size_mb = os.path.getsize(apk) / 1_048_576
            log(f"APK built: {size_mb:.1f} MB")
        else:
            log("WARNING: build succeeded but APK not found at expected path")
    else:
        log(f"Build FAILED with exit code {retcode}")

    return retcode

if __name__ == "__main__":
    sys.exit(main())
