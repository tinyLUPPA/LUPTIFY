import os
import zipfile

src_dir = r"c:\Users\yusuf\Downloads\LUPTIFY"
out1 = r"c:\Users\yusuf\Downloads\LUPTIFY_backup_latest.zip"
out2 = r"c:\Users\yusuf\Downloads\LUPTIFY\LUPTIFY_backup_latest.zip"

exclude_dirs = {".venv", "__pycache__", ".git"}

for dest in [out1, out2]:
    with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(src_dir):
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            for file in files:
                if file.endswith(".zip"):
                    continue
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, src_dir)
                zf.write(full_path, rel_path)

print(f"Backup created successfully: {os.path.getsize(out1)} bytes")
