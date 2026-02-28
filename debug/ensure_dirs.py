import os

def ensure_dirs():
    dirs = [
        r"c:\Users\alsto\Documents\SUTD\Projects\backend-plant-pot\audio_artifacts\backchannels",
    ]
    
    with open("dir_creation_log.txt", "w") as log:
        for d in dirs:
            try:
                os.makedirs(d, exist_ok=True)
                if os.path.exists(d):
                    log.write(f"SUCCESS: Created {d}\n")
                    # Try to create a dummy file
                    dummy_path = os.path.join(d, "test.txt")
                    with open(dummy_path, "w") as f:
                        f.write("test")
                    log.write(f"SUCCESS: Wrote file to {dummy_path}\n")
                else:
                    log.write(f"FAIL: {d} does not exist after makedirs call\n")
            except Exception as e:
                log.write(f"ERROR: {e}\n")

if __name__ == "__main__":
    ensure_dirs()
