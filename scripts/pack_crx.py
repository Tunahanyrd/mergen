import os
import shutil
import subprocess
import sys


def create_crx(extension_dir, key_path, output_path):
    # Zip the extension directory
    shutil.make_archive("extension", "zip", extension_dir)

    # Read the public key
    # We use openssl to derive public key from private key
    try:
        # standard openssl command to get pubkey in DER format
        subprocess.run(
            ["openssl", "rsa", "-in", key_path, "-pubout", "-outform", "DER", "-out", "pub.der"],
            check=True,
            stderr=subprocess.DEVNULL,
        )
        with open("pub.der", "rb") as f:
            f.read()
    except Exception as e:
        print(f"Error getting public key: {e}")
        return False

    # Create a clean temp copy of the extension without key.pem
    import tempfile

    try:
        with tempfile.TemporaryDirectory() as tmp_dir:
            clean_ext_dir = os.path.join(tmp_dir, "clean_extension")

            # Copy everything except key.pem
            shutil.copytree(extension_dir, clean_ext_dir, ignore=shutil.ignore_patterns("key.pem", "*.pem", ".git*"))

            cmd = [
                "google-chrome",
                f"--pack-extension={clean_ext_dir}",
                f"--pack-extension-key={os.path.abspath(key_path)}",
                "--no-sandbox",
                "--disable-gpu",
                "--headless",
            ]

            print(f"Running: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True)
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)

            # Chrome packs to parent dir of target? Or alongside?
            expected_crx = clean_ext_dir + ".crx"

            if os.path.exists(expected_crx):
                print(f"CRX created at {expected_crx}")
                shutil.move(expected_crx, output_path)
                return True
            else:
                print(f"CRX file not found at {expected_crx}")
                return False

    except Exception as e:
        print(f"Error packing extension: {e}")
        return False


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python3 pack_crx.py <extension_dir> <key.pem> <output.crx>")
        sys.exit(1)

    ext_dir = sys.argv[1]
    key_pem = sys.argv[2]
    out_crx = sys.argv[3]

    if create_crx(ext_dir, key_pem, out_crx):
        print(f"Successfully created {out_crx}")
        sys.exit(0)
    else:
        sys.exit(1)
