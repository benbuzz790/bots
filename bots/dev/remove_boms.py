import codecs
import os


def remove_bom_from_files():
    nboms = 0

    def remove_bom(file_path):
        nonlocal nboms  # Modify the outer variable
        with open(file_path, "rb") as file:
            content = file.read()
        if content.startswith(codecs.BOM_UTF8):
            with open(file_path, "wb") as file:
                file.write(content[len(codecs.BOM_UTF8) :])
            print(f"Removed BOM from: {file_path}")
            nboms += 1
        else:
            print(f"No BOM found in: {file_path}")

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
            except Exception as e:
                print(f"Error processing {file_path}: {str(e)}")
    print(f"BOM removal process completed. {nboms} BOMs removed")


if __name__ == "__main__":
    remove_bom_from_files()
