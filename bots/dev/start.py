#start.py
from bots.dev import project_tree
import os
import sys

def cleanup_directory(script_path, extensions=('.md', '.txt', '.bot', '.py'), dry_run=True):
    """
    Deletes specific file types in the same directory as the script, except the script itself.
    
    Args:
        script_path: Path to the current script
        extensions: Tuple of file extensions to delete (including the dot)
        dry_run: If True, only prints what would be deleted without actually deleting
    
    Returns:
        list: Names of deleted files
    """
    # Get the directory containing the script
    directory = os.path.dirname(os.path.abspath(script_path))
    
    # Get the script filename
    script_name = os.path.basename(script_path)
    preserve = [script_name, 'process_bots.py']
    
    deleted_files = []
    
    print(f"Cleaning directory: {directory}")
    print(f"Looking for files with extensions: {', '.join(extensions)}")
    print(f"Preserving scripts: {', '.join(preserve)}")
    
    # List all files in the directory
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        
        # Skip if it's a directory or the script itself
        if os.path.isdir(file_path) or filename in preserve:
            continue
            
        # Check if the file has one of the specified extensions
        if not filename.lower().endswith(extensions):
            continue
            
        if dry_run:
            print(f"Would delete: {filename}")
        else:
            try:
                os.remove(file_path)
                deleted_files.append(filename)
                print(f"Deleted: {filename}")
            except Exception as e:
                print(f"Error deleting {filename}: {e}")
    
    return deleted_files

if __name__ == "__main__":
    # First run in dry_run mode to show what would be deleted
    print("DRY RUN - No files will be deleted:")
    cleanup_directory(__file__, extensions=('.txt', '.bot', '.py'), dry_run=True)
    
    # Ask for confirmation before actual deletion
    response = input("\nDo you want to proceed with deletion? (yes/no): ")
    if response.lower() == 'yes':
        print("\nDeleting files:")
        deleted = cleanup_directory(__file__, extensions=('.txt', '.bot', '.py'), dry_run=False)
        print(f"\nSuccessfully deleted {len(deleted)} files")
    else:
        print("Operation cancelled")
    
    project_tree.main(r"nasa5020_analysis_spec.md")