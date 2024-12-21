import traceback
import textwrap
import os
import time
import bots.tools.code_tools as code_tools
import bots.tools.terminal_tools as terminal_tools
import bots.tools.python_tools as python_tools
from bots.foundation.anthropic_bots import AnthropicBot
from bots.foundation.base import load
from bots.foundation.base import Bot
import bots.functional_prompts.functional_prompts as fp

# Should perhaps be multi-threaded

### Bot tools ###

def message_bot(bot_path, message):
    """
    Loads a bot, sends it a message, and allows it to work.

    Use to prepare a bot to do a task and to allow it to work. Returns control when the
    bot replies with '/DONE'.

    Parameters:
    - bot_path (str): File path to the saved bot
    - message (str): The message to send to the bot

    Returns the bot's first response, a list of tool-uses in order, and final response as a string.
    """

    try:
        # Set up prompt_while arguments
        bot = load(bot_path)
        first_message = "MESSAGE:\n\n" + message
        continue_prompt = prompts.message_continue
        
        def stop_condition(bot:Bot):
            
            # Side effect: print
            tool_name = ''
            tools = ''
            if bot.tool_handler.requests:
                for request in bot.tool_handler.requests:
                    tool_name, _ = bot.tool_handler.tool_name_and_input(request)
                tools += "- " + tool_name + "\n"
            response = bot.conversation.content
            print(bot.name + ": " + response + "\n" + tool_name)

            # Stop when /DONE in response
            return "/DONE" in response
        
        # prompt_while bot hasn't said "/DONE"
        _, nodes = fp.prompt_while(bot, first_message, continue_prompt, stop_condition)

        # get desired information from returned conversation nodes
        tools = ''
        for node in nodes:
            tool_name = ''
            if node.tool_calls:
                for call in node.tool_calls:
                    tool_name, _ = bot.tool_handler.tool_name_and_input(call)
                    tools += "- " + tool_name + "\n"
        
        return nodes[0].content +":\n" + tools + "\n---" + nodes[-1].content
    
    except Exception as error:
        return _process_error(error)

def memorialize_requirements(name: str, requirements: str):
    """
    Creates or updates a requirements file for a module.
    
    Use when you need to document requirements for a new file or update
    existing requirements.
    
    Parameters:
    - name (str): Name of the file (.md or .txt)
    - requirements (str): The requirements content to write. This must be comprehensive
        and complete. Saying 'everything else stays the same' is NOT allowed.
    
    Returns the filename or an error message string.
    """

    try:
        file_path = f"{name}"
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(requirements)
        return f'Created requirements file {file_path} successfully'
    except Exception as error:
        return _process_error(error)

def initialize_file_bot(file_name: str) -> str:
    """
    Creates and initializes a new file-editing bot, saving it to disk.
    Creates any necessary directories from the file_name path if they don't exist.

    Use when you need to create a new bot to handle implementation of a specific file.
    The bot will be initialized with appropriate file-level tools and context.

    Parameters:
    - file_name (str): Name of the file this bot will manage (can include directory path)

    Returns success message with bot's file path or an error message string.
    """

    try:
        # Create directories from the file path if they don't exist
        directory = os.path.dirname(file_name)
        if directory:
            os.makedirs(directory, exist_ok=True)
            
        name, _ = os.path.splitext(file_name)
        file_bot = AnthropicBot(name=f"{name}")
        file_bot.set_system_message(prompts.file_initialization)
        file_bot.add_tools(code_tools)
        file_bot.add_tools(terminal_tools)    
        file_bot.add_tools(python_tools)   
        path = file_bot.save(file_bot.name)
        return f"Success: file bot created at {path}"
    except Exception as error:
        return _process_error(error)

def initialize_validator_bot(name: str) -> str:
    """
    Creates and initializes a new validator bot, saving it to disk.
    Creates any necessary directories from the name path if they don't exist.

    Use when you need to create a new bot to handle validation of a set of files
    against a set of requirements.

    Parameters:
    - name (str): Name of the bot including optional path (will be saved as [name].bot)

    Returns success message with bot's file path or an error message string.
    """

    try:
        # Create directories from the name path if they don't exist
        directory = os.path.dirname(name)
        if directory:
            os.makedirs(directory, exist_ok=True)
            
        validator_bot = AnthropicBot(name=f"{name}")
        validator_bot.set_system_message(prompts.validator_initialization)
        validator_bot.add_tools(code_tools)
        validator_bot.add_tool(message_bot)
        path = validator_bot.save(validator_bot.name)
        return f"Success: validator bot created at {path}"
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

def _get_new_files(start_time, directory="."):
    """Get all files created after start_time in directory"""
    new_files = []
    
    for root, _, files in os.walk(directory):
        for file in files:
            path = os.path.join(root, file)
            if os.path.getctime(path) >= start_time:
                new_files.append(path)
                
    return new_files

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

        # Decide on structure
        print("----- Making Spec -----")
        root_bot = _initialize_root_bot()
        response = root_bot.respond(prompts.root_breakdown_spec(spec))
        print("root: " + response)

        # Make other bots
        print("----- Making Bots -----")
        start_time = time.time()
        responses, _ = fp.prompt_while(
            bot = root_bot, 
            first_prompt = prompts.root_make_bots(), 
            continue_prompt = prompts.root_continue, 
            stop_condition = fp.conditions.tool_not_used
            )
        print("root: "+ '\n'.join(responses))

        # get all new file bots
        bot_list = _get_new_files(start_time)

        # Create requirements for each bot
        print("----- Making requirements -----")
        _, nodes = fp.prompt_for(
            bot = root_bot, 
            items = bot_list, 
            dynamic_prompt = prompts.root_make_req, 
            should_branch = False
            )
        
        # return to branch
        #root_bot.conversation = nodes[0].parent.parent
        
        # Create files by instructing each bot to make them
        print("----- Making Files -----")

        _, nodes = fp.prompt_for(
            bot = root_bot, 
            items = bot_list, 
            dynamic_prompt = prompts.root_make_files, 
            should_branch = True
        )

        # return to branch
        root_bot.conversation = nodes[0].parent.parent

        # run requirements validator
        print("----- Running Validator -----")
        fp.prompt_while(
            bot = root_bot,
            first_prompt = prompts.root_validate(),
            continue_prompt = "say command 'DONE' when validator is done", 
            stop_condition = fp.conditions.said_DONE    
            )
        
        # run tests sequentially (bot needs knowledge for reports)
        print("----- Running Tests -----")
        fp.prompt_for(
            bot = root_bot, 
            items = bot_list, 
            dynamic_prompt = prompts.root_run_tests, 
            should_branch = False
        )

        print("----- Final Touches -----")
        fp.prompt_while(
            bot = root_bot,
            first_prompt = prompts.root_cleanup(),
            continue_prompt = "say command 'DONE' when cleanup is done",
            stop_condition = fp.conditions.said_DONE
        )
        
        print("----- Making Demo -----")
        fp.prompt_while(
            bot = root_bot, 
            first_prompt = prompts.root_demo(""),
            continue_prompt = "say command 'DONE' when demo bot has run demo successfully", 
            stop_condition = fp.conditions.said_DONE
            )
        
        print("----- Wrapping Up -----")
        print(root_bot.respond(prompts.root_wrap_up()))

    except Exception as error:
       raise error
   
    return "success"


### Prompt Library ###

class prompts:

    requirements_guidance = textwrap.dedent("""
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
            '''
        ```

    3. Test Requirements:
        For each test:
        ```
        test_[feature]_[scenario]:
            Action: [specific method call with specific values]
            Assert: [exact condition to verify]
        ```

    Format requirements exactly like this:
    ```
    # filename.py

    ## Purpose

    ## Dependencies
    - [Import 1: reason needed]
    - [Import 2: reason needed]

    ## Classes and Functions

    ### class ClassName
    Purpose: [description]

    Methods:
    #### method_name(param1: type, param2: type) -> return_type
    [Follow function template above]

    ## Tests
    [Follow test template for each test case]
    ```

    BE SPECIFIC
    """)

    project_context = textwrap.dedent("""
    You are part of a hierarchical system of specialized AI assistants 
    working together to create an industry-ready Python project. 
    The system has multiple bot types:
    1. Root: Handles project architecture and module design. Oversees multiple files.
    2. File: Handles specific file implementation and testing. 
    3. Validator: Verifies that file implementations meet requirements

    You are all responsible for keeping things simple (KISS) and minimal (YAGNI)
    to the extent that requirements allow.
    """)

    root_initialization = project_context + textwrap.dedent("""
    You are the root bot responsible for:
    1. Analyzing project specifications
    2. Breaking down the project into logical modules
    3. Creating clear requirements for each module
    4. Creating and coordinating bots
    5. Creatively solving problems in the workflow.
                                                            
    We will walk through a process step by step. Focus always on the latest INSTRUCTION.
    
    YOU ARE RESPONSIBLE FOR SOLVING YOUR OWN PROBLEMS
    ex) If a file is missing, view_dir and try to find it. search C:, figure it out.
                                      
    "It's not my job" IS NOT ALLOWED:
    If you believe there is a problem with this framework or a tool, work around it.
    """)

    def root_breakdown_spec(spec: str):
        return textwrap.dedent(f"""
        Please analyze this project specification:

        ```specification
        {spec}
        ```

        Save a technical architecture document based on the specification, 
        including:
        1. Top-level project requirements
        2. A free-form, 'thinking' section in which you consider different 
        ideas and concepts which might be used to accomplish the project.
        3. An explanation of the general flow of control, starting with the 
        entry point and moving through the modules in the order that 
        information does.
        4. A list of all modules for the project.
        5. A list all files for each module.

        Save as project_req.txt.
        """)

    def root_make_bots():
        return textwrap.dedent("""
            For each non-test file you identified: 
            INSTRUCTION 1. Use initialize_file_bot to create a set of file bots. These bots will also
            be responsible for writing their own tests in a partner file to their own. You
            should use multiple parallel tool calls in a single message.""")
    
    def root_make_req(bot_name: str):
        # Intended to be used in a prompt_for loop
        bot_name = bot_name.removesuffix('.bot')
        return textwrap.dedent(f"""INSTRUCTION 2. Consider {bot_name}. Determine how top level
        requirements flow down to that file. Then use memorialize_requirements to set the requirements
        for {bot_name}.bot. Name the file {bot_name}_req.txt. Note: mocking during tests is not allowed""")

    def root_make_files(bot_name: str):
        # Intended to be used in a prompt_for loop
        bot_name = bot_name.removesuffix('.bot')
        return textwrap.dedent(f"""INSTRUCTION 3. We just created requirements for each bot in in other threads. 
            Use message_bot telling {bot_name} their name and to find their requirements file. Instruct them to 
            create two files: one to meet the requirements, and one to test the previous file against those 
            requirements. (If appropriate -- don't worry about telling a README bot to make tests, for instance). 
            Tell them not to run tests yet. Remind them about YAGNI and KISS, and note that 
            for our purposes 'mocking' is considered an unecessary element of tests - use real integration
            tests instead.""")
        
    def root_validate():
        return textwrap.dedent("""INSTRUCTION 4. We just had the file bots write files and tests in another
            thread. Use initialize_validator_bot to make a validator bot. INSTRUCTION 4.5 Use message_bot to 
            instruct the validator to confirm ALL files with a corresponding _req.txt file meet requirements 
            (but do not run any tests), and to give you a summary. Tell it to message any bots with issues 
            and point out the requirements issues.""")
    
    def root_run_tests(bot_name: str):
        # prompt_for
        return textwrap.dedent(f"""INSTRUCTION 5. Message {bot_name} telling them to run their test files
            and debug. If the bot runs out of memory, it means the initial approach was too complex. Apply
            RAGNI and KISS and attempt to simplify the requirements. Then initialize a new one. They may 
            sometimes accidentally end their session early. Just message them to get them to continue.""")
    
    def root_cleanup():
        return textwrap.dedent(f"""INSTRUCTION 6. Clean up any borked components -- message bots to finish
            their work if they haven't already, attempt to fix any issues that arose, etc.""")

    def root_demo(bot_name: str):
        return textwrap.dedent(f"""INSTRUCTION 7. Make the full system demo""")

    def root_wrap_up():
        return textwrap.dedent("""INSTRUCTION 8. Finally, use memorialize_requirements to write a report
            for humans to read noting all failed bots, potential tool issues, odd behaviors in the framework,
            or other issues. Also include a project status report. Include instructions for running the demo.
            Name the file 'final-report.md'""")

    root_continue = 'Work until the current INSTRUCTION is complete, then say \
            "DONE" to move on to the next INSTRUCTION'
    
    message_continue = 'Reply with command "/DONE" when MESSAGE has been addressed'

    file_initialization = project_context + textwrap.dedent("""
    You are a file bot responsible for:
    1. Understanding file requirements
    2. Implementing the specified functionality
    3. Writing appropriate tests
    4. Ensuring code quality and documentation
        
    Focus on:
    - Clean, maintainable code
    - Clear documentation
    - Following KISS and YAGNI principles
    - Making a functional, testable file

    DO NOT leave any implementation incomplete
    DO NOT leave placeholders in your code
    PREFER the python ast editing tools for python code

    You may
    - use external dependencies
    - install items with pip
    - make multiple editing passes
    - examine the current working directory and view other files, if needed, for coordination or imports
    - use scratch.py as a testing space to determine if small snippets of code work or to explore data
    structures you aren't 100 percent familiar with.
    
                                          
    YOU ARE RESPONSIBLE FOR SOLVING YOUR OWN PROBLEMS
    ex) If a file is missing, view_dir and try to find it. If you need credentials, figure out how
    to make your own account. Think creatively. You have my permission to use your tools to the full extent
    of their capabilities
    """)

    validator_initialization = project_context + textwrap.dedent(\
    """
    You are a requirements checking bot responsible for:
    1. Verifying python files meet their associated requirements
    2. Communicating deviations from requirements with the associated file bot.
    3. Ensuring requirements are met after the file bot makes changes.

    NEVER RUN TESTS. Just examine files and requirements files.
    You may need to clarify filenames - use view_dir if you can't find a file.

    1. Read a *_req.txt file and the associated *.py file
    2. If all requirements are not met, use message_bot on *.bot to let them know.
    They will make changes and then reply, at which point you can check the file
    again.
    3. If all requirements are met, go on to the next file.
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

    sample_ainet = """
# ainet Technical Specification
Version 2.0

## 1. Problem Statement

### 1.1 Background
Large Language Models (LLMs) need clean, structured text to work effectively. Web pages contain noise and complex structures that interfere with LLM processing. ainet solves this by transforming web content into LLM-friendly formats.

### 1.2 Design Principles
1. KISS: Keep solutions simple and focused
2. YAGNI: Only implement proven necessary features
3. SOLID: Design modular, maintainable components
4. flat: Use a single directory for all files to avoid annoying python path issues.

## 2. Technical Requirements

### 2.1 Input Requirements
- HTTPS URLs only
- Single URL processing per request
- Content-Type: application/json
- Required headers: 
  - Authorization: API key
  - Accept: application/json

### 2.2 Output Format
```json
{
  "url": "string",
  "text": "string",
  "title": "string",
  "error": "string?"
}
```

## 3. System Architecture

### 3.1 Core Components
```
[Client] → [FastAPI] → [Content Extractor] → [Response]
```

### 3.2 Component Specifications

#### 3.2.1 API Layer
- Framework: FastAPI
- Endpoints:
  ```
  POST /v1/extract  # URL processing
  ```
#### 3.2.2 Content Extractor
- Single extractor: Trafilatura

## 4. Performance Requirements - None

## 5. Monitoring and Logging - None

## 6. Testing Requirements

### 6.1 Core Testing
- Unit tests
- Complete integration tests
- Successful "full system" demo

## 7. Security Requirements

### 7.1 Authentication
- HTTPS only

### 7.2 Data Protection
- No content storage
- Input sanitization

## 8. Development Guidelines

### 8.1 Code Quality
- Follow KISS, YAGNI, and SOLID principles

### 8.2 Documentation
- API reference
- Setup guide

## 9. Future Considerations
Features intentionally deferred (DO NOT IMPLEMENT):
1. Batch processing
2. Advanced metadata extraction
3. Memory caching
4. Advanced monitoring
5. Complex authentication
6. Comprehensive test coverage
7. Rate Limit
8. Logging
9. Performance Requirements
10.   GET  /v1/health   # Service health check
11. Redis Cache Layer
12. API key authentication

## 10. Definition of Done

Core functionality is complete when:
1. Single URLs can be processed reliably
2. Content is extracted correctly
3. Basic security is implemented
4. Critical paths are tested
5. demo.py successfully extracts content from an arbitrary webpage and displays it in the terminal

## 11. Special Instructions
1. Write demo.py LAST

## 12. Version History

- 2.2: Core specification 
- Date: Dec 17 2024
- Previous: v2.0 Core specification (YAGNI-focused)
- Approved By: Ben Rinauto
    """

    llm_email = """
# LLM Email System Technical Specification

## 1. Problem Statement

Create a SIMPLE python email client for llms.

### 1.1 Background
- Current LLM interactions are limited to terminal or bespoke interfaces
- Human users need to communicate with LLMs through their native email clients
- LLMs need a standardized way to send and receive emails
- This solution will benefit both LLM developers and end-users by enabling 
email-based interactions

### 1.2 Design Principles
The overarching goal is for this project to be "LLM - implementable". 
The following principles are designed to keep this project specification 
implementable by LLMs that exist as of 18Dec2024. LLMs tend to both add 
unecessary complexity AND fail on complex projects, the combination of 
which means llms need some design principles to keep them on the right
track. With that in mind: 

1. KISS: Keep solutions simple and focused
2. YAGNI: Only implement proven necessary features
3. SOLID: Design modular, maintainable components
4. flat: All program files in a single directory.

Follow these design principles even if they contradict requirements!

## 2. Technical Requirements

### 2.1 Misc Requirements
- System will integrate with benbuzz790's 'bots' library
- Interface to system will be a small set of functions which
receive and return strings.
- An example tool file can be found in "C:/Users/benbu/Code/
llm-utilities-git/bots/bots/tools/utf8_tools.py"
- 'bots' is designed to work with arbitrary *stateless* python functions - 
no further interface design is required for llms to use the functions.
- System will use authentication method as demonstrated in (existing) example.py

## 3. System Architecture

### 3.1 Core Components
```
[Email Service]
    │
    ├── Email Handler
    │
    └── LLM tool interface (single file)
        ├── send_email(cred_filepath:str, to:str, cc:str, bcc:str, subject:str, body:str) -> str (confirmation / error msg)
        ├── reply_to_email(cred_filepath:str, email_id:str, body:str) -> str (confirmation/err)
        ├── check_inbox(cred_filepath:str) -> str (newline separated list of sender: subject)
        ├── read_email(cred_filepath:str, email_id:str) -> str (output format per below)
        └── archive_emails(cred_filepath:str, email_id:str) -> str (confirmation / error)
```


#### 3.1.1 Email Format
- eml

### 3.2 Component Specifications

#### 3.2.1 Email Handler
- Framework: Standard email libraries
- Local storage
- Simple folder structure (inbox, sent, archive)
- GMAIL email protocol support -- see existing example.py

## 4. Performance Requirements
- None

## 5. Monitoring and Logging
- None

## 6. Testing Requirements

### 6.1 Core Testing
- Unit tests for each core function
- Integration tests for email sending/receiving
- Required DEMO: Successful email exchange with external systems
- (send test emails to benbuzz790@gmail.com with subject "TEST EMAIL")

## 7. Security Requirements

### 7.1 Authentication
- API key authentication for service access (credentials.json already exists, use it as shown in example.py)
- **Be sure any auth bots know of example.py**!
- Standard email security (TLS) for transmission

### 7.2 Data Protection
- Emails stored locally in standard format
- No encryption

## 8. Development Guidelines

### 8.1 Code Quality
- Follow PEP 8 for Python code
- Use type hints 

### 8.2 Documentation
- Example usage documentation

## 9. Future Considerations
Features intentionally deferred (DO NOT IMPLEMENT):
1. Attachment support
2. Custom email templates
3. Multiple provider-specific implementations
4. Advanced filtering and search
5. Unread status management
6. File transformation -- use eml directly when possible
7. Custom exceptions
8. Sanitization
9. Logging
10. Schema definitions
11. Thread safety, atomic operations, etc. for file control
12. Validators

## 10. Definition of Done
LLM Email System is complete when:
1. All core functions are implemented and tested
2. System can successfully exchange emails with external email systems
3. Authentication and security measures are in place
4. A full system demonstration shows successful bi-directional communication

## 11. Special Instructions
- Keep the interface and implementation simple

## 12. Version History

- Version: 1.2 (cred.json auth)
- Date: 20-Dec-2024
- Previous: 1.1 (simpler)
- Approved By: Ben Rinauto
"""

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
    generate_project(prompts.llm_email)

if __name__ == '__main__':
    main()