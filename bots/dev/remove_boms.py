import codecs
import os


def remove_bom_from_files():
    nboms = 0
    files_processed = 0

    def remove_bom(file_path):
        nonlocal nboms  # Modify the outer variable
        with open(file_path, "rb") as file:
            content = file.read()
        if content.startswith(codecs.BOM_UTF8):
            with open(file_path, "wb") as file:
                file.write(content[len(codecs.BOM_UTF8) :])
            nboms += 1

    def is_hidden(path):
        # Check if directory or file is hidden
        return os.path.basename(path).startswith(".")

    for root, dirs, files in os.walk(os.getcwd()):
        # Remove hidden directories from dirs list (modifies dirs in place)
        dirs[:] = [d for d in dirs if not is_hidden(d)]
        for file in files:
            # Skip hidden files
            if is_hidden(file):
                continue
            file_path = os.path.join(root, file)
            try:
                remove_bom(file_path)
                files_processed += 1
            except Exception:
                pass  # Silently skip files that can't be processed

    print("\nBOM Removal Summary:")
    print(f"  Files processed: {files_processed}")
    print(f"  BOMs removed: {nboms}")


if __name__ == "__main__":
    remove_bom_from_files()
