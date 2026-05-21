import os
import sys
import subprocess
import time

def main():
    if len(sys.argv) < 5:
        print("Usage: python background_tailor.py <master_cv> <jd_path> <output_path> <log_path>")
        sys.exit(1)

    master_cv = sys.argv[1]
    jd_path = sys.argv[2]
    output_path = sys.argv[3]
    log_path = sys.argv[4]

    # Ensure log directory exists
    os.makedirs(os.path.dirname(log_path), exist_ok=True)

    with open(log_path, "w", encoding="utf-8") as log_file:
        log_file.write(f"--- Starting Tailoring Operation ---\n")
        log_file.write(f"Timestamp: {time.ctime()}\n")
        log_file.write(f"Target: {output_path}\n\n")
        log_file.flush()

        try:
            # Step 1: Tailor Resume
            log_file.write("Step 1: Generating tailored suite...\n")
            log_file.flush()
            
            cmd1 = [sys.executable, "scripts/tailor_resume_lossless.py", master_cv, jd_path, output_path]
            process1 = subprocess.Popen(cmd1, stdout=log_file, stderr=subprocess.STDOUT, text=True)
            process1.wait()

            if process1.returncode != 0:
                log_file.write(f"\n❌ Step 1 failed with return code {process1.returncode}\n")
                sys.exit(1)

            # Step 2: Harvest Apps
            log_file.write("\nStep 2: Archiving application...\n")
            log_file.flush()
            
            cmd2 = [sys.executable, "scripts/harvest_apps.py"]
            process2 = subprocess.Popen(cmd2, stdout=log_file, stderr=subprocess.STDOUT, text=True)
            process2.wait()

            if process2.returncode != 0:
                log_file.write(f"\n❌ Step 2 failed with return code {process2.returncode}\n")
                sys.exit(1)

            log_file.write("\n✅ Operation completed successfully.\n")
            log_file.flush()

        except Exception as e:
            log_file.write(f"\n❌ Unexpected error: {str(e)}\n")
            log_file.flush()
            sys.exit(1)

if __name__ == "__main__":
    main()
