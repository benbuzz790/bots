import traceback
import bots.tools.code_tools as CT
from bots.foundation.anthropic_bots import AnthropicBot

# Should perhaps be multi-threaded

### Bot tools ###

def instruct_bot(bot_path, instruction):
    """
    Loads a bot, sends it an instruction, and allows it to work.

    Use when a bot is ready to execute a task.

    Parameters:
    - bot_path (str): File path to the saved bot
    - instruction (str): The instruction to send to the bot

    Returns the bot's first response, a list of tool-uses in order, and final response as a string.
    """
    from bots.foundation.base import load
    from bots.dev.project_tree import _process_error
    try:
        bot = load(bot_path)
        first_response = bot.respond(instruction+"\nYou may now use tools.")
        bot.save(bot.name)
        last_response = first_response
        print(bot.name + ": " + first_response)
        tools = ''
        stop = False
        while not stop:
            tool_name = ''
            if bot.tool_handler.requests:
                tool_name, _ = bot.tool_handler.tool_name_and_input(bot.tool_handler.requests[0])
                tools += "- " + tool_name + "\n"
            print(bot.name + ": " + last_response + "\n" + tool_name)
            last_response = bot.respond('ok (reply "DONE" when done)')
            path = bot.save(bot.name)
            stop = 'DONE' in last_response
        return first_response +"\n"+ tools + last_response
    except Exception as error:
        return _process_error(error)

def ask_root_bot(bot_path: str, message:str):
    """
    Loads the project bot from disk and sends it a message.

    Use when you need to communicate with the project bot to discuss requirements,
    get clarification, or review implementation details.

    Parameters:
    - bot_path (str): File path to the saved module bot
    - message (str): The message to send to the bot

    Returns the bot's response as a string or an error message.
    """
    from bots.foundation.base import load
    from bots.dev.project_tree import _process_error

    try:
        rootb0t = load(bot_path)
        response = rootb0t.respond(message)
        rootb0t.save(rootb0t.name)  
        return response
    except Exception as error:
        return _process_error(error)

def set_module_requirements(name: str, requirements: str):
    """
    Creates or updates a requirements file for a module.
    
    Use when you need to document requirements for a new module or update
    existing requirements. Always creates files with _module_requirements.txt suffix.
    
    Parameters:
    - name (str): Base name of the component (without _requirements.txt)
    - requirements (str): The requirements content to write. This must be comprehensive
        and complete. Saying 'everything else stays the same' is NOT allowed.
    
    Returns 'success' or an error message string.
    """
    from bots.dev.project_tree import _process_error

    try:
        file_path = f"{name}_module_requirements.txt"
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(requirements)
        return f'Created requirements file {file_path} successfully'
    except Exception as error:
        return _process_error(error)
    
def set_file_requirements(name: str, requirements: str):
    """
    Creates or updates a requirements file for a module.
    
    Use when you need to document requirements for a new file or update
    existing requirements. Always creates files with _file_requirements.txt suffix.
    
    Parameters:
    - name (str): Base name of the file (without _requirements.txt)
    - requirements (str): The requirements content to write. This must be comprehensive
        and complete. Saying 'everything else stays the same' is NOT allowed.
    
    Returns 'success' or an error message string.
    """
    from bots.dev.project_tree import _process_error

    try:
        file_path = f"{name}_file_requirements.txt"
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(requirements)
        return f'Created requirements file {file_path} successfully'
    except Exception as error:
        return _process_error(error)

def initialize_module_bot(module_name: str) -> str:
    """
    Creates and initializes a new module-level bot, saving it to disk.

    Use when you need to create a new bot to handle a module's requirements and implementation.
    The bot will be initialized with appropriate module-level tools and context as well as the 
    text of the file at requirements_path.

    Parameters:
    - module_name (str): Name of the module this bot will manage
    - requirements_path (str): The location of the requirements file for the module

    Returns success message with bot's file path or an error message string.
    """
    from bots.foundation.anthropic_bots import AnthropicBot
    import bots.tools.code_tools as CT
    from bots.dev.project_tree import _process_error, prompts
    
    try:
        module_bot = AnthropicBot(name=f"{module_name}_Claude")
        module_bot.set_system_message(prompts.file_initialization)
        module_bot.add_tool(initialize_file_bot)
        module_bot.add_tool(prepare_file_bot)
        module_bot.add_tool(set_file_requirements)
        module_bot.add_tool(instruct_bot)
        _ = module_bot.respond(prompts.module_first_message)
        path = module_bot.save(module_bot.name)
        return f"Success: module bot created at {path}"
    except Exception as error:
        return _process_error(error)

def prepare_module_bot(bot_path: str, message: str) -> str:
    """
    Loads a module bot from disk and sends it a message without
    allowing the module bot to use any tools.

    Use when
     - you need to communicate with a module bot to discuss requirements
    
    Parameters:
    - bot_path (str): File path to the saved module bot
    - message (str): The message to send to the bot

    Returns the bot's response as a string or an error message.
    """
    from bots.foundation.base import load
    from bots.dev.project_tree import _process_error, prompts

    try:
        module_bot = load(bot_path)
        response = module_bot.respond(message + "\nDo not use any tools yet.")
        print("\n" + module_bot.name + ": " + response)
        module_bot.save(module_bot.name)
        return response
    except Exception as error:
        return _process_error(error)

def initialize_file_bot(file_name: str) -> str:
    """
    Creates and initializes a new file-editing bot, saving it to disk.

    Use when you need to create a new bot to handle implementation of a specific file.
    The bot will be initialized with appropriate file-level tools and context, as well as
    with the text of the requirements file.

    Parameters:
    - file_name (str): Name of the file this bot will manage
    - requirements_path (str): path to the requirements file

    Returns success message with bot's file path or an error message string.
    """
    import bots.tools.code_tools as CT
    import bots.tools.terminal_tools as TT
    from bots.foundation.anthropic_bots import AnthropicBot
    from bots.dev.project_tree import _process_error, prompts

    try:
        file_bot = AnthropicBot(name=f"{file_name}_Claude")
        file_bot.set_system_message(prompts.file_initialization)
        file_bot.add_tools(CT)
        file_bot.add_tools(TT)       
        path = file_bot.save(file_bot.name)
        return f"Success: file bot created at {path}"
    except Exception as error:
        return _process_error(error)

def prepare_file_bot(bot_path: str, message: str) -> str:
    """
    Loads a file bot from disk and sends it a message without allowing it
    to use any tools.

    Use when 
        - you need to communicate with a file bot to discuss requirements
        
    Parameters:
    - bot_path (str): File path to the saved file bot
    - message (str): The message to send to the bot
    - requirements_path (str): The path to the file requirements. 
      (will be appended to your message if not None)

    Returns the bot's response as a string or an error message.
    """
    from bots.foundation.base import load
    from bots.dev.project_tree import _process_error, prompts

    try:
        file_bot = load(bot_path)
        response = file_bot.respond(message + "\nDo not use any tools yet.")
        print(file_bot.name + ": " + response)
        path = file_bot.save(file_bot.name)  # Save any state changes
        return response
    except Exception as error:
        return _process_error(error)

def _initialize_root_bot():
    root_bot = AnthropicBot(name="project_Claude")
    root_bot.add_tool(initialize_module_bot)
    root_bot.add_tool(prepare_module_bot)
    root_bot.add_tool(set_module_requirements)
    root_bot.add_tool(instruct_bot)
    root_bot.save(root_bot.name)
    root_bot.set_system_message(prompts.root_initialization)
    return root_bot

def _process_error(error):
    #raise error
    error_message = f'Tool Failed: {str(error)}\n'
    error_message += (
        f"Traceback:\n{''.join(traceback.format_tb(error.__traceback__))}")
    return error_message

### Project Creation ###

def generate_project(spec: str):
   """
   Executes the standard process for project generation:
   1. Root bot processes spec and creates module requirements 
   2. Root bot creates and calls module bots for each module
   3. Module bots create and call file bots
   4. File bots implement code
   
   Parameters:
   - spec (str): Project specification text
   
   Returns success or error message string.
   """
   try:
        root_bot = _initialize_root_bot()
        response = root_bot.respond(prompts.root_first_message(spec))
        print("root: " + response)

        # Let root bot work until it signals completion
        while not 'DONE' in response:
            response = root_bot.respond('ok (reply "DONE" when done)')
            print("\n\n" + "root: " + response)
            root_bot.save(root_bot.name)  # Save state after each interaction
        return root_bot
        #return "Project generation completed successfully"

   except Exception as error:
       raise error
   
### Prompt Library ###

class prompts:

    requirements_guidance_module = """
    Module requirements should be written in a structured format:

    1. Overview Section:
        - Module name and one-line purpose
        - Key responsibilities (bullet points)
        - Primary interfaces/APIs it will expose
        - Critical dependencies (external packages, other modules)

    2. Interface Definitions:
        - Each public class/function that other modules will use
        - For each interface:
            * Purpose and use cases
            * Parameters with types and descriptions
            * Return values with types and descriptions
            * Exceptions it may raise
            * Example usage if non-obvious

    3. Data Structures:
        - Key data structures or types defined in this module
        - Data validation requirements
        - State management requirements if applicable

    4. Integration Requirements:
        - How other modules will import/use this module
        - Any initialization/setup required
        - Configuration requirements
        - Resource management (files, connections, etc.)

    5. Non-functional Requirements:
        - Performance expectations
        - Error handling strategies
        - Logging requirements
        - Thread safety requirements if applicable
        - Resource cleanup/management

    6. Implementation Constraints:
        - Required design patterns
        - Code style requirements beyond PEP 8
        - Specific algorithms to use
        - Memory/performance constraints

    Format requirements exactly like this:
    ```
    # ModuleName

    ## Overview
    [Brief description]

    ### Responsibilities
    - [Responsibility 1]
    - [Responsibility 2]
    ...

    ### Primary Interfaces
    - [Interface 1]
    - [Interface 2]
    ...

    ### Dependencies
    - [Dependency 1: reason needed]
    - [Dependency 2: reason needed]
    ...

    ## Interface Definitions

    ### [Interface 1 Name]
    Purpose: [description]
    Parameters:
    - name (type): description
    Returns: (type) description
    Raises: 
    - ExceptionType: when/why
    Example:
    ```python
    [example code]
    ```

    [Continue sections...]
    ```

    BE SPECIFIC. "Handle errors appropriately" is not specific enough. 
    "Catch FileNotFoundError and ValueError, log with error level, re-raise with context" is specific enough.
    """

    requirements_guidance_file = """
    File requirements should be written in a structured format:

    1. File Overview:
        - Filename with extension
        - Single clear purpose
        - Role in the module
        - Direct dependencies

    2. Implementation Requirements:
        For each class/function to implement:
        ```
        def function_name(param1: type, param2: type) -> return_type:
            '''
            [Purpose in active voice]
            
            Args:
                param1: [specific description including valid/invalid values]
                param2: [specific description including valid/invalid values]
            
            Returns:
                [Exact description of return value and format]
                
            Raises:
                ExceptionType: [Exact condition that causes this]
            
            Example:
                >>> [concrete example with actual values]
                [expected output]
            '''
        ```

    3. Error Handling:
        Specify for each error case:
        - Exception type to catch
        - Error message format
        - Whether to log, re-raise, or handle
        - Recovery action if any

    4. Test Requirements:
        For each test:
        ```
        test_[feature]_[scenario]:
            Setup: [specific objects/data to create]
            Action: [specific method call with specific values]
            Assert: [exact condition to verify]
            Cleanup: [specific cleanup needed if any]
        ```

    5. Performance Requirements:
        - Time complexity limits
        - Memory usage limits
        - Specific algorithms to use
        - Data structure choices

    Format requirements exactly like this:
    ```
    # filename.py

    ## Purpose
    [Single sentence purpose]

    ## Dependencies
    - [Import 1: reason needed]
    - [Import 2: reason needed]

    ## Classes and Functions

    ### class ClassName
    Purpose: [description]

    Methods:
    #### method_name(param1: type, param2: type) -> return_type
    [Follow function template above]

    ## Error Handling
    - Case 1: [specific error case]
        * Exception: [type]
        * Action: [log/raise/handle]
        * Recovery: [steps]

    ## Tests
    [Follow test template for each test case]
    ```

    BE SPECIFIC:
    BAD: "Write tests for error cases"
    GOOD: "Test FileNotFoundError when config.json is missing, verify logs contain path"
    """

    project_context = """
    You are part of a hierarchical system of specialized AI assistants 
    working together to create a Python project.
    The system has three levels:
    1. Root: Handles project architecture and module design. Oversees multiple modules.
    2. Module: Handles module implementation and file organization. Oversees multiple files.
    3. File: Handles specific file implementation and testing. 
    """

    root_initialization = project_context + """
    You are the root bot responsible for:
    1. Analyzing project specifications
    2. Breaking down the project into logical modules
    3. Creating clear requirements for each module
    4. Creating and coordinating module bots
    """ + requirements_guidance_module

    def root_first_message(spec: str):
        return f"""
        
        Please analyze this project specification:

        ```specification
        {spec}
        ```

        First, list all major modules for the project.
    
        For each module you identify:
        
        1. Use initialize_module_bot to create a module bot.
        2. Use prepare_module_bot to discuss requirements until clear. Note that you
        will need to send the requirements in your message and should instruct the 
        bot do make at least two files: one will be a test for the other.
        3. Use make_requirements to memorialize final requirements.
        4. Use instruct_bot and allow the module bot to work.
        
        Again,
        1. initialize_module_bot
        2. prepare_module_bot
        3. make_requirements
        4. instruct_bot

        DO NOT:
        - try to edit or write files (other than requirements). Even for
            small changes - use instruct_bot with a message which is an instruction 
            to the appropriate bot.

        """

    module_initialization = project_context + """
    You are a module bot responsible for:
    1. Understanding module requirements
    2. Chunking the module responsibilities into multiple files
    3. Creating clear requirements for each file
    4. Creating and coordinating file bots for your module.
    """ + requirements_guidance_file

    module_first_message = """
    In a moment, you will be contacted by the project manager to discuss module requirements.
    Do not use any tools until this discussion is finished.

    Second, after that discussion, 
    
    0. List all the files which will make up your module, including test files.

    For each file in your list:
    1. Use initialize_file_bot to create a file bot
    2. Use prepare_file_bot to discuss requirements until clear.
    Note that you will have to send the requirements in the first message.
    3. Use make_requirements to document the agreed-upon requirements
    4. Use instruct_bot to allow the file bot to write the ENTIRE file at once

    Again:
    0. Talk to project manager
    1. List all files
    2. initialize_file_bot to get started
    3. prepare_file_bot to clarify
    4. make_requirements to memorialize 
    5. instruct_bot to initiate action
    6. repeat for all files

    DO NOT:
    - try to edit or write files (other than requirements). Even for
    small changes - use instruct_bot with a message which is an instruction 
    to the appropriate bot.

    Please respond with only "YES" to confirm readiness.
    """

    file_initialization = project_context + """
    You are a file bot responsible for:
    1. Understanding file requirements
    2. Implementing the specified functionality
    3. Writing appropriate tests
    4. Ensuring code quality and documentation
        
    Focus on:
    - Clean, maintainable code
    - Proper error handling
    - Clear documentation
    - Making a comprehensive, testable file
    - Following Python best practices

    DO NOT leave any implementation incomplete
    DO NOT leave placeholders in your code

    You may
    - use external dependencies
    - install items with pip
    - make multiple editing passes
    - examine the current working directory and view other files, if needed, for coordination or imports

    You will be contacted by the module manager soon to discuss requirements.
    """

    sample_fuzznet = """
    Project: FuzzNet

    Create a protocol fuzzing framework for network security testing. The system should:

    Core Requirements:
    - Support common protocols (HTTP, FTP, SMTP, custom TCP/UDP)
    - Generate protocol-aware test cases
    - Monitor target for crashes/hangs
    - Record and replay capabilities
    - Mutation-based and generation-based fuzzing
    - Coverage-guided fuzzing for open-source targets
    - Export findings in standard format

    Key Features:
    1. Protocol Handlers
    - Protocol definitions in YAML/JSON
    - Basic protocol automation
    - State tracking
    - Custom protocol support

    2. Fuzzing Engine
    - Smart field mutation
    - Test case generation
    - Coverage feedback integration
    - Crash detection and classification
    - Resource monitoring

    3. Test Case Management
    - Save/load test cases
    - Minimize test cases
    - Export/import capabilities
    - Crash reproduction

    4. Monitoring
    - Target health checking
    - Resource utilization tracking
    - Network traffic monitoring
    - Result correlation

    5. Reporting
    - Detailed crash reports
    - Coverage statistics
    - Test case statistics
    - Export in multiple formats

    Technical Requirements:
    - Handle high-speed packet generation
    - Efficient memory management
    - Modular architecture for extensions
    - Support for custom protocols
    - Comprehensive logging and debugging
    """

    sample_feapy = """
    Project: FeaPy

    Create a command-line finite element analysis package for 2D structural problems. 
    The package should:

    Core Requirements:
    - Support linear elastic analysis of 2D structures
    - Handle triangular and quadrilateral elements
    - Allow definition of structures through JSON/YAML input files
    - Support point loads and distributed loads
    - Calculate displacements, stresses, and strains
    - Generate text-based visualization of results (using ASCII art or similar)
    - Provide error estimates and convergence metrics
    - Export results to CSV/JSON formats

    Key Features:
    1. Mesh Generation
    - Read geometry from input files
    - Basic mesh refinement capabilities
    - Mesh quality checks

    2. Material Models
    - Linear elastic materials
    - Support for different material properties (Young's modulus, Poisson's ratio)
    - Material library management

    3. Analysis
    - Assembly of global stiffness matrix
    - Application of boundary conditions
    - Linear system solver
    - Post-processing of results

    4. Results Processing
    - Calculation of derived quantities (stress, strain)
    - Error estimation
    - Results visualization in terminal
    - Data export

    5. CLI Interface
    - Interactive mode for analysis setup
    - Batch processing mode
    - Progress indicators for long computations
    - Result browsing and querying

    6. Testing
    - Thorough testing of all features

    Performance Requirements:
    - Handle problems up to 1000 elements
    - Memory efficient sparse matrix operations
    - Parallelize matrix assembly and solving where beneficial

    Documentation Requirements:
    - Is a package
    - Follows github community guidelines

    DEFINITION OF DONE:
    FeaPy successfully runs a sample problem which is sufficiently complicated to
    faithfully represent a real-world scenario through the CLI without errors and
    with the correct result.
    """

    sample_logsage = """
    Project: LogSage

    Create a high-performance log analysis framework for processing 
    and analyzing large log files. The system should:

    Core Requirements:
    - Parse multiple log formats (Apache, Nginx, Custom patterns)
    - Process logs in streaming fashion for memory efficiency
    - Support regular expression-based pattern matching
    - Generate statistical summaries and reports
    - Alert on pattern matches or threshold violations
    - Support pipeline-style processing of log data
    - Handle compressed log files directly

    Key Features:
    1. Log Ingestion
    - Multiple input sources (files, streams, S3)
    - Custom log format definition
    - Automatic format detection
    - Handling of malformed entries

    2. Analysis Engine
    - Pattern matching with regex
    - Statistical aggregations
    - Time-window analysis
    - Anomaly detection
    - Custom analyzers plugin system

    3. Alerting
    - Threshold-based alerts
    - Pattern-based alerts
    - Alert aggregation and deduplication
    - Custom alert handlers

    4. Reporting
    - Summary statistics
    - Trend analysis
    - Top-N reports
    - Custom report formats

    5. Performance
    - Stream processing
    - Multi-threading support
    - Memory efficient operations
    - Progress tracking

    Technical Requirements:
    - Process 1GB+ log files
    - Memory usage under 500MB
    - Support for custom plugins
    - Comprehensive CLI interface"""

### Main ###

import sys
import traceback
from functools import wraps
from typing import Any, Callable

def debug_on_error(func: Callable) -> Callable:
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return func(*args, **kwargs)
        except Exception:
            type, value, tb = sys.exc_info()
            traceback.print_exception(type, value, tb)
            print("\n--- Entering post-mortem debugging ---")
            import pdb
            pdb.post_mortem(tb)
    return wrapper

@debug_on_error
def main():
    bot = generate_project(prompts.sample_feapy)
    import bots
    bots.dev.auto_terminal.main()

if __name__ == '__main__':
    main()