#!/usr/bin/env python3
"""Persistent background runner for compile_content.py.
Survives tool context swaps by self-restarting on completion."""
import subprocess, sys, os, time, signal

SCRIPT = "/home/josh/claw-code/DeFide/scripts/compile_content.py"
LOG    = "/tmp/compile_daemon_final.log"
CWD    = "/home/josh/claw-code/DeFide"
DONE_MARKER = "/tmp/compile_done.flag"

def write_log(msg):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}\n"
    with open(LOG, "a") as f:
        f.write(line)
    print(msg, flush=True)

def main():
    os.chdir(CWD)
    write_log("=== Compiler daemon starting ===")
    write_log(f"Working dir: {os.getcwd()}")
    write_log(f"Python: {sys.executable}")

    while True:
        write_log(f"Starting: python3 {SCRIPT}")
        with open(LOG, "a") as lf:
            proc = subprocess.Popen(
                [sys.executable, SCRIPT],
                stdout=lf, stderr=subprocess.STDOUT,
                cwd=CWD
            )
        write_log(f"Compiler PID={proc.pid}")

        try:
            retcode = proc.wait()
        except KeyboardInterrupt:
            write_log("Interrupted by user -- stopping.")
            proc.terminate()
            proc.wait()
            break

        if os.path.exists(DONE_MARKER):
            write_log(f"Done marker found -- stopping. (exit={retcode})")
            break

        write_log(f"Compiler exited with code {retcode} -- restarting in 5s...")
        time.sleep(5)

if __name__ == "__main__":
    main()
