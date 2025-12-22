import sys
import os
import struct
import shutil
import subprocess

def create_crx(extension_dir, key_path, output_path):
    # Zip the extension directory
    shutil.make_archive('extension', 'zip', extension_dir)
    zip_path = 'extension.zip'

    # Read the public key
    # We use openssl to derive public key from private key
    try:
        # standard openssl command to get pubkey in DER format
        subprocess.run(['openssl', 'rsa', '-in', key_path, '-pubout', '-outform', 'DER', '-out', 'pub.der'], check=True, stderr=subprocess.DEVNULL)
        with open('pub.der', 'rb') as f:
            pub_key = f.read()
    except Exception as e:
        print(f"Error getting public key: {e}")
        return False

    # Sign the zip with private key
    try:
        # sha1 signature (CRX2/3 legacy comaptibility, usually sha256 is better but CRX2 uses sha1)
        # Chrome requires SHA256 usually now. CRX3 format is complex (protobuf).
        # Let's use simple CRX2-like structure but with SHA256 if possible or check what Chrome expects.
        # Actually simplest way for modern Chrome is creating a .crx via `google-chrome --pack-extension`.
        # If that fails (headless CI), we might need a CRX3 builder lib.
        # For simplicity in this script, we'll try to use the system `google-chrome` or `chromium` if available,
        # fallback to a basic CRX2/3 implementation ONLY if needed.
        #
        # BUT, CRX3 is protobuf based. Writing a pure python CRX3 packer is non-trivial without proto defs.
        #
        # Alternative: The user wants "Push everything".
        # If we can't pack CRX easily in python, we rely on the CI environment having 'google-chrome'.
        # GitHub Actions Ubuntu images HAVE google-chrome.
        # So we can just call it via subprocess!
        
        cmd = [
            'google-chrome', 
            f'--pack-extension={os.path.abspath(extension_dir)}', 
            f'--pack-extension-key={os.path.abspath(key_path)}'
        ]
        print(f"Running: {' '.join(cmd)}")
        subprocess.run(cmd, check=True)
        
        # Chrome creates .crx in the parent dir of extension_dir? or alongside?
        # Typically alongside extension_dir. i.e if extension_dir is ./browser-extension, output is ./browser-extension.crx
        expected_crx = extension_dir + '.crx'
        if os.path.exists(expected_crx):
            print(f"CRX created at {expected_crx}")
            shutil.move(expected_crx, output_path)
            return True
        else:
            print("CRX file not found after command.")
            return False

    except Exception as e:
        print(f"Error packing extension: {e}")
        # Fallback to Chromium?
        try:
             cmd[0] = 'chromium-browser'
             subprocess.run(cmd, check=True)
             expected_crx = extension_dir + '.crx'
             if os.path.exists(expected_crx):
                shutil.move(expected_crx, output_path)
                return True
        except:
            pass
            
        print("Failed to use google-chrome or chromium-browser.")
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
