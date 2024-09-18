# Unified Markdown Documentation Generator

The Unified Markdown Documentation Generator is a Python utility script designed to automate 
the consolidation of a project's codebase into a single, navigable markdown file. 
This script scans through all directories within a specified project folder, seamlessly 
incorporating the contents of various file types into a unified markdown document.

## Installation

1. Clone the repository or download the script files.
2. Navigate to the script directory in your terminal.
3. Run the following command to install the script:

   ```
   pip install .
   ```

4. Add the following line to your `.zshrc` file to make the script executable from anywhere:

   ```sh
   export PATH=$PATH:/path/to/script/directory
   ```

   Replace `/path/to/script/directory` with the actual path to the directory containing the script.
   Or create a symbolic link to this file assuming you are in the root directory of this project.
   ```sh
     ln -s $(pwd)/create_project_markdown.py /usr/local/bin/create-project-markdown
   ```

5. Restart your terminal or run `source ~/.zshrc` to apply the changes.

## Usage

To generate a markdown file for your project, navigate to the project's root directory in 
your terminal and run the following command:

```sh
create-project-markdown [--include REGEX] [--exclude REGEX] [--outfile FILENAME]
```

- `--include REGEX` or `-i REGEX`: (Optional) Regular expression pattern to include specific files or directories.
- `--exclude REGEX` or `-e REGEX`: (Optional) Regular expression pattern to exclude specific files or directories.
- `--outfile FILENAME`: (Optional) Specify a custom output filename. Default is `project_structure.md`.

If no include or exclude filters are provided, the script will process all supported file types.

## Supported File Types

The script supports the following file types:

- Python files (.py)
- Java files (.java)
- JavaScript files (.js)
- TypeScript files (.ts)
- Markdown files (.md)
- Go files (.go)
- C# files (.cs)
- XML files (.xml)
- YAML files (.yaml, .yml)
- TOML files (.toml)
- Shell scripts (.sh)

## Example

To generate a markdown file for a project named "MyProject" with only Python and Markdown files, run:

```sh
create-project-markdown --include ".*\.(py|md)$"
```


This will generate a file named `project_structure.md` in the project's root directory, 
containing the contents of all Python and Markdown files in the project.

## Troubleshooting

If you encounter any issues or errors while using the script, please refer to the 
error messages provided for guidance. If the issue persists, please open an issue on 
the GitHub repository.

## Contributing

Contributions are welcome! If you find any bugs or have suggestions for improvements, 
please open an issue or submit a pull request on the GitHub repository.

## License

This project is licensed under the [MIT License](LICENSE).

