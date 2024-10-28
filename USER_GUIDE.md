# User Guide: Using Unified Markdown Documentation Generator for Language Models

The Unified Markdown Documentation Generator is a Python tool that enables you to convert an entire source project into a single markdown file. This consolidated markdown document can be easily used as an input for web interfaces such as ChatGPT or Claude, making it convenient for creating cohesive project overviews or for use in projects leveraging large language models like GPTs or Claude.

This user guide provides an exhaustive overview of how to configure and use the tool effectively, including the configuration options, command-line arguments, and their effect on the output. Example data structures, files, and the resulting output are also provided for better understanding.

## Overview

The tool takes a source project directory and generates a markdown file that represents the structure and contents of the project. This file can then be used as a reference or documentation, helping large language models like ChatGPT or Claude to better understand the project context, code structure, and key elements in a single document.

## Installation Steps

1. Clone the repository or download the script files.
2. Navigate to the script directory in your terminal.
3. Run the following command to install:
   ```
   pip install .
   ```
4. To make the script accessible from anywhere in your terminal, add it to your path or create a symbolic link:
   ```sh
   export PATH=$PATH:/path/to/script/directory
   ```
   Or create a symlink:
   ```sh
   ln -s $(pwd)/create_project_markdown.py /usr/local/bin/create-project-markdown
   ```
5. Restart your terminal or run `source ~/.zshrc` to apply the changes.

## Configuration and Command-Line Arguments

The script can be run with command-line arguments or configured using a YAML file. The YAML configuration allows for default settings, which can then be overridden using command-line arguments.

### Configuration File (`.pmarkdownc/config.yaml`)
The configuration file is used to set default values for the markdown generator, such as file types to include, directories to exclude, and other parameters.

Example of a configuration file:
```yaml
supported_extensions:
  .py: python
  .sh: bash
forbidden_dirs:
  - __pycache__
  - dist
  - node_modules
  - .git
project_path: .
include_pattern: ".*\.py$"
exclude_pattern: null
outfile: project_overview.md
log_level: INFO
```

### Command-Line Arguments
- **`project_path`** (Positional, Optional): Path to the project directory. Defaults to the current directory (`.`) if not provided.
- **`--include` or `-i`**: Regular expression pattern to include specific files or directories. If not provided, the default value from the configuration file will be used.
- **`--exclude` or `-e`**: Regular expression pattern to exclude specific files or directories. If not provided, defaults from the configuration file will be used.
- **`--outfile` or `-o`**: Specify the output markdown file name. Defaults to `project_structure.md` if not provided.
- **`--log` or `-l`**: Set the logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`). The default value is `INFO` and can be adjusted using the configuration file or the argument.

### Command-Line Usage Example
```sh
create-project-markdown --include ".*\.py$" --exclude "tests/" --outfile "python_project_overview.md" --log DEBUG
```
This command will:
- Include only `.py` files.
- Exclude files in the `tests/` directory.
- Set the output file to `python_project_overview.md`.
- Use `DEBUG` level logging for detailed information during execution.

## Generating a Markdown File

To generate a markdown file, you can either use command-line arguments directly or rely on a pre-configured YAML file. Below are examples illustrating both approaches:

### Example 1: YAML Configuration
Suppose you have the following project structure:
```
MyProject/
├── src/
│   ├── main.py
│   ├── helper.py
├── scripts/
│   └── run.sh
```
You can create a `.pmarkdownc/config.yaml` file as follows:
```yaml
supported_extensions:
  .py: python
  .sh: bash
forbidden_dirs:
  - tests
outfile: "MyProject_overview.md"
log_level: INFO
```

Then run the command:
```sh
create-project-markdown
```
This will:
- Generate a file named `MyProject_overview.md`.
- Include all Python (`.py`) and Shell (`.sh`) files.

### Example 2: Command-Line Argument Overrides
You can override the configuration settings with command-line arguments. For instance:
```sh
create-project-markdown --include ".*\.py$" --exclude "dist/" --outfile "filtered_overview.md"
```
This will:
- Include only Python files (`.py`).
- Exclude the `dist` directory.
- Generate the markdown file named `filtered_overview.md`.

## Example Outputs

### Example Project Structure
Suppose you have a simple project structure as follows:
```
MyProject/
├── src/
│   ├── main.py
│   └── helper.py
├── scripts/
│   └── run.sh
```
- **`main.py`**:
  ```python
  print("Hello, World!")
  ```
- **`helper.py`**:
  ```python
  def greet(name):
      return f"Hello, {name}!"
  ```
- **`run.sh`**:
  ```sh
  echo "Hello from Bash!"
  ```

### Example Markdown Output
The generated markdown (`MyProject_overview.md`) might look like this:

# MyProject

## src

### src/main.py
```python
print("Hello, World!")
```

### src/helper.py
```python
def greet(name):
    return f"Hello, {name}!"
```

## scripts

### scripts/run.sh
```sh
echo "Hello from Bash!"
```

This output can then be easily fed into tools like ChatGPT or Claude, giving a high-level overview of the project, the structure, and all included files. It helps in providing context when working on enhancing the code, writing documentation, or generating new features based on the existing codebase.

## Using with ChatGPT or Claude
### Using the Generated Markdown as Input for Large Language Models
Once you have the generated markdown file, you can use it in tools like ChatGPT or Claude by simply pasting the content or uploading the markdown file if the interface allows it.

- **ChatGPT**: The consolidated markdown file provides a clear, hierarchical representation of the code, making it easy for ChatGPT to follow the structure and context. This is particularly useful for understanding the relationships between different components of a project.
- **Claude**: Similarly, for Claude, you can input this markdown to have a comprehensive overview of your project, making it easier to answer specific questions about code logic, architecture, or suggestions for improvements.

### Integration with Claude Projects or GPTs
- **Claude Projects**: You can use the generated markdown as the input data for a Claude project to provide context and ask for suggestions, code refactoring, or writing documentation.
- **ChatGPT's Custom GPTs**: This markdown can be used to fine-tune GPTs with structured and comprehensive information about a codebase, allowing the model to become more context-aware and produce better-targeted responses during interaction.

## Configuration in Depth
The configuration YAML file provides robust customization capabilities:

- **`supported_extensions`**: Define which file extensions should be included and the corresponding language for syntax highlighting in the generated markdown.
  - Example:
    ```yaml
    supported_extensions:
      .py: python
      .sh: bash
    ```
  - Only Python and Shell files will be included.

- **`forbidden_dirs`**: Specify which directories should be ignored.
  - Example:
    ```yaml
    forbidden_dirs:
      - node_modules
      - dist
    ```
  - The script will ignore these directories.

- **`include_pattern`** and **`exclude_pattern`**: Use regular expressions to control which files or directories should be included or excluded.
  - Example:
    ```yaml
    include_pattern: ".*\.py$"
    exclude_pattern: "tests/"
    ```
  - Include only Python files and exclude anything in a `tests` directory.

- **`outfile`**: The name of the output file. This can be overridden with `--outfile` in the command line.
  - Example:
    ```yaml
    outfile: "project_summary.md"
    ```

- **`log_level`**: Set the verbosity of the logging output.
  - Options include `DEBUG`, `INFO`, `WARNING`, `ERROR`. This helps in determining the detail level of feedback during the script’s execution.

## Example Logs
When running the script with `DEBUG` level logging, you might see output like this:
```
2024-10-28 14:22:01,123 - DEBUG - Checking if path should be ignored: src/__pycache__ with patterns ['__pycache__', 'dist', 'node_modules']
2024-10-28 14:22:01,456 - INFO - Markdown file generated: filtered_overview.md
```
This helps in understanding which files are being processed, which are being skipped, and if there are any issues.

## Conclusion
The Unified Markdown Documentation Generator is an effective tool for converting a codebase into a comprehensive markdown document that can easily be fed into tools like ChatGPT and Claude. It simplifies the process of understanding, documenting, and enhancing projects by providing a consolidated view of the entire source in one place.

Feel free to experiment with different configurations and options to suit the needs of your specific projects. This document should help you leverage the power of language models more effectively by providing well-structured, comprehensive project overviews.

