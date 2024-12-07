import traceback
import textwrap
import os
import bots.tools.code_tools as code_tools
import bots.tools.terminal_tools as terminal_tools
import bots.tools.python_tools as python_tools
from bots.foundation.anthropic_bots import AnthropicBot
from bots.foundation.base import load
import bots.functional_prompts.functional_prompts as fp

# Should perhaps be multi-threaded

### Bot tools ###

def message_bot(bot_path, message):
    """
    Loads a bot, sends it a message, and allows it to work.

    Use to prepare a bot to do a task and to allow it to work. Returns control when the
    bot replies with 'DONE'.

    Parameters:
    - bot_path (str): File path to the saved bot
    - message (str): The message to send to the bot

    Returns the bot's first response, a list of tool-uses in order, and final response as a string.
    """

    try:
        bot = load(bot_path)
        first_response = bot.respond(message)
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
        return first_response +"\n" + tools + last_response
    except Exception as error:
        return _process_error(error)

def memorialize_requirements(name: str, requirements: str):
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

    try:
        file_path = f"{name}_file_requirements.txt"
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(requirements)
        return f'Created requirements file {file_path} successfully'
    except Exception as error:
        return _process_error(error)

def initialize_file_bot(file_name: str) -> str:
    """
    Creates and initializes a new file-editing bot, saving it to disk.

    Use when you need to create a new bot to handle implementation of a specific file.
    The bot will be initialized with appropriate file-level tools and context.

    Parameters:
    - file_name (str): Name of the file this bot will manage

    Returns success message with bot's file path or an error message string.
    """

    try:
        name, _ = os.path.splitext(file_name)
        file_bot = AnthropicBot(name=f"{name}_file")
        file_bot.set_system_message(prompts.file_initialization)
        file_bot.add_tools(code_tools)
        file_bot.add_tools(terminal_tools)    
        file_bot.add_tools(python_tools)   
        path = file_bot.save(file_bot.name)
        return f"Success: file bot created at {path}"
    except Exception as error:
        return _process_error(error)

def initialize_validator_bot(files: str, name: str) -> str:
    """
    Creates and initializes a new validator bot, saving it to disk.

    Use when you need to create a new bot to handle validation of a set of files.
    The bot will be initialized with appropriate tools and context, as well as
    with the 'files' string.

    Parameters:
    - files (str): A list of files to be validated.
    - bot_name (str): Name of the bot. Will be saved as [bot_name].bot

    Returns success message with bot's file path or an error message string.
    """

    try:
        validator_bot = AnthropicBot(name=f"{name}")
        responsibility = f"\n\nYou are responsible for:\n\n{files}"
        validator_bot.set_system_message(prompts.validator_initialization + responsibility)
        validator_bot.add_tool(code_tools.view)
        validator_bot.add_tool(message_bot)
        path = validator_bot.save(validator_bot.name)
        return f"Success: file bot created at {path}"
    except Exception as error:
        return _process_error(error)

def _initialize_root_bot():
    root_bot = AnthropicBot(name="project_Claude")
    root_bot.add_tool(initialize_file_bot)
    root_bot.add_tool(initialize_validator_bot)
    root_bot.add_tool(message_bot)
    root_bot.add_tool(memorialize_requirements)
    root_bot.add_tools(terminal_tools)
    root_bot.save(root_bot.name)
    root_bot.set_system_message(prompts.root_initialization)
    return root_bot

def _process_error(error):
    error_message = f'Tool Failed: {str(error)}\n'
    error_message += (
        f"Traceback:\n{''.join(traceback.format_tb(error.__traceback__))}")
    return error_message

### Project Creation ###

def generate_project(spec: str):
    """
    Executes the standard process for project generation:
    1. Root bot processes spec and creates module requirements 
    2. Root bot creates and calls file bots for each module
    4. File bots implement code
   
    Parameters:
    - spec (str): Project specification text
   
    Returns success or error message string.
    """
    
    try:
        root_bot = _initialize_root_bot()
        response = root_bot.respond(prompts.root_first_message(spec))
        print("root: " + response)

        def stop_condition(bot, reply):
            print("root: " + reply) #cheaty debug
            bot.save(bot.name)
            return "DONE" in reply

        fp.chain_while(root_bot, prompts.root_instruction_array, \
                       stop_condition, prompts.root_continue)

    except Exception as error:
       raise error
   
    return "success"


### Prompt Library ###

class prompts:

    requirements_guidance_file = textwrap.dedent("""
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
    """)

    project_context = textwrap.dedent("""
    You are part of a hierarchical system of specialized AI assistants 
    working together to create a Python project.
    The system has multiple bot types:
    1. Root: Handles project architecture and module design. Oversees multiple files.
    2. File: Handles specific file implementation and testing. 
    3. Validator: Verifies that file implementations meet requirements
    """)

    root_initialization = project_context + textwrap.dedent("""
    You are the root bot responsible for:
    1. Analyzing project specifications
    2. Breaking down the project into logical modules
    3. Creating clear requirements for each module
    4. Creating and coordinating other bots
                                                            
    DO NOT:
    - try to edit or write files (other than requirements). Even for
        small changes - use message_bot with a message which is an instruction 
        to the appropriate bot.
                                                            
    We will walk through a process step by step. Always focus on the latest task.

    """) + requirements_guidance_file

    def root_first_message(spec: str):
        return textwrap.dedent(f"""
        
        Please analyze this project specification:

        ```specification
        {spec}
        ```

        First, list all modules for the project.
        Then, list all files for each module.
        """)

    root_instruction_array = [
        textwrap.dedent("""For each non-test file you identified: 
            INSTRUCTION 1. Use initialize_file_bot to create a set of file bots. These bots will also
            be responsible for writing their own tests in a partner file to their own. You
            should use multiple tool calls in a single message."""),
        textwrap.dedent("""INSTRUCTION 2. Use message_bot and discuss requirements. Go back and forth
            with each bot at least twice. You should instruct the bot not to use tools yet."""),
        textwrap.dedent("""INSTRUCTION 3. Use memorialize_requirements to memorialize the agreed-upon
            requirements."""),
        textwrap.dedent("""INSTRUCTION 4. Use message_bot and instruct the module bots to create
            two files: the one discussed and a a set of tests for the one discussed."""),
        textwrap.dedent("""INSTRUCTION 5. Use initialize_validator_bot to make a validator"""),
        textwrap.dedent("""INSTRUCTION 6. Use message_bot to instruct the validator to confirm 
            files meet requirements"""),
        textwrap.dedent("""INSTRUCTION 7. Message the file bots telling them to run their test files and debug. If the 
            bots run out of memory or otherwise 'crash', make a note and continue working."""),
        textwrap.dedent("""INSTRUCTION 8. Finally, use memorialize_requirements to write a set of instructions
            for humans to read noting all failed bots and other issues.""")
    ]

    root_continue = 'Work until the current INSTRUCTION is complete, then say \
            "DONE" to move on to the next INSTRUCTION'

    file_initialization = project_context + textwrap.dedent("""
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
    PREFER the python ast editing tools for python code, using line editing as a fallback

    You may
    - use external dependencies
    - install items with pip
    - make multiple editing passes
    - examine the current working directory and view other files, if needed, for coordination or imports

    You will be contacted by the module manager soon to discuss requirements.
    """)

    validator_initialization = project_context + textwrap.dedent(\
    """
    You are a requirements checking bot responsible for:
    1. Verifying python files meet their associated requirements
    2. Communicating deviations from requirements with the associated file bot.
    3. Ensuring requirements are met after the file bot makes changes.
    
    Requirements files are located at [filename]_requirements.txt (without the .py)
    View both files, then message the filebot at [filename].bot (no .py) using message_bot
    and request corrections. Repeat until the requirements are met.
    """)

    sample_fuzznet = textwrap.dedent("""
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
    """)

    sample_feapy = textwrap.dedent("""
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
    - Project structure shall be flat - a single folder with all files.

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
    """)

    sample_logsage = textwrap.dedent("""
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
    - Comprehensive CLI interface""")

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

if __name__ == '__main__':
    main()