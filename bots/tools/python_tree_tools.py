def view(label, path):
    """  
        Show the expanded view of the node with the given label (two depths are shown).
    
        Args:
        path (str): The path to the project root.
        label (str): The label of the node to expand.
    
        Returns:
        str: The expanded view of the node or an error message.

        Notes for this tool:
            Use path '.' for cwd
            Use label '0' for project root


        Notes for all tools:
            You're working with a toolset that represents a 
            project as a labeled tree. The labels allow you
            to view and modify code precisely, without the 
            need to write an entire file. The tree encompases
            directories, files, and for python, a limited ast.
        """
    try:
        from bots.tools.llast import LLASTProject
        project = LLASTProject(path)
        return project.expand(label)
def add(code, label, path):
    """
        Add code as a child to the node with "label".
    
        Args:
        path (str): The path to the project root.
        label (str): The label of the parent node.
        code (str): The code to add as a child.
    
        Returns:
        str: The result of the insertion operation or an error message.
        """
    try:
        from bots.tools.llast import LLASTProject
        project = LLASTProject(path)
        result = project.insert_child(label, code)
        return f'{result}\nChanges have been saved.'
def change(code, label, path):
    """
        Update the node with the given label with new code.
    
        Args:
        path (str): The path to the project root.
        label (str): The label of the node to update.
        code (str): The new code for the node.
    
        Returns:
        str: The result of the update operation or an error message.
        """
    try:
        from bots.tools.llast import LLASTProject
        project = LLASTProject(path)
        result = project.update_node(label, code)
        return f'{result}\nChanges have been saved.'
def delete(label, path):
    """
        Delete the node with the given label and save changes.
    
        Args:
        path (str): The path to the project root.
        label (str): The label of the node to delete.
    
        Returns:
        str: The result of the deletion operation or an error message.
        """
    try:
        from bots.tools.llast import LLASTProject
        project = LLASTProject(path)
        result = project.delete(label)
        return f'{result}\nChanges have been saved.'
if __name__ == '__main__':
    pass