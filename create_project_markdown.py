#!/usr/bin/env python3

import os
import re
import argparse
from typing import List, Optional, Dict
from pathlib import Path
import fnmatch
import yaml
import logging

# Default supported file extensions and their corresponding language identifiers
DEFAULT_SUPPORTED_EXTENSIONS: Dict[str, str] = {
    '.py': 'python',
    '.java': 'java',
    '.js': 'javascript',
    '.kt': 'kotlin',
    '.kts': 'kotlin',
    '.ts': 'typescript',
    '.go': 'go',
    '.cs': 'csharp',
    '.xml': 'xml',
    '.yaml': 'yaml',
    '.toml': 'toml',
    '.sh': 'bash',
    '.sql': 'sql',
    '.avsc': 'avro'
}

# Default directories to be ignored
DEFAULT_FORBIDDEN_DIRS: List[str] = [
    '__pycache__', 'dist', 'node_modules', 'cdk.out', 'env', 'venv'
]

CONFIG_PATH = Path.cwd() / '.pmarkdownc' / 'config.yaml'
GITIGNORE_PATH = Path.cwd() / '.gitignore'

# Configure logging
DEFAULT_LOG_LEVEL = 'INFO'
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


# Function to create default config file if it doesn't exist
def create_default_config():
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, 'w') as config_file:
        yaml.dump({
            'supported_extensions': DEFAULT_SUPPORTED_EXTENSIONS,
            'forbidden_dirs': DEFAULT_FORBIDDEN_DIRS,
            'project_path': '.',
            'include_pattern': None,
            'exclude_pattern': None,
            'outfile': 'project_structure.md',
            'log_level': DEFAULT_LOG_LEVEL
        }, config_file)

    # Add .pmarkdownc to .gitignore if it exists
    if GITIGNORE_PATH.exists():
        with open(GITIGNORE_PATH, 'a') as gitignore_file:
            gitignore_file.write('\n# Added by pmarkdown\n.pmarkdownc/\n')


# Function to load the supported extensions and forbidden directories from the config file
def load_config() -> Dict[str, Optional[str]]:
    if not CONFIG_PATH.exists():
        create_default_config()

    with open(CONFIG_PATH, 'r') as config_file:
        config = yaml.safe_load(config_file)
    return {
        'supported_extensions': config.get('supported_extensions', DEFAULT_SUPPORTED_EXTENSIONS),
        'forbidden_dirs': config.get('forbidden_dirs', DEFAULT_FORBIDDEN_DIRS),
        'project_path': config.get('project_path', '.'),
        'include_pattern': config.get('include_pattern', None),
        'exclude_pattern': config.get('exclude_pattern', None),
        'outfile': config.get('outfile', 'project_structure.md'),
        'log_level': config.get('log_level', DEFAULT_LOG_LEVEL)
    }


def parse_gitignore(project_path: str) -> List[str]:
    gitignore_path = os.path.join(project_path, '.gitignore')
    if not os.path.exists(gitignore_path):
        return []

    with open(gitignore_path, 'r') as f:
        return [line.strip() for line in f if line.strip() and not line.startswith('#')]


def should_ignore(path: str, gitignore_patterns: List[str]) -> bool:
    logging.debug(f"Checking if path should be ignored: {path} with patterns {gitignore_patterns}")
    for pattern in gitignore_patterns:
        if fnmatch.fnmatch(path, pattern):
            return True
    return False


def generate_markdown(project_path: str, include_pattern: Optional[str] = None, exclude_pattern: Optional[str] = None,
                      output_file: str = 'project_structure.md') -> None:
    gitignore_patterns = parse_gitignore(project_path)
    config = load_config()
    supported_extensions = config['supported_extensions']
    forbidden_dirs = config['forbidden_dirs']

    project_path = project_path or config['project_path']
    include_pattern = include_pattern or config['include_pattern']
    exclude_pattern = exclude_pattern or config['exclude_pattern']
    output_file = output_file or config['outfile']

    with open(output_file, 'w') as f:
        f.write(f'# {os.path.basename(project_path)}\n\n')
        for root, dirs, files in os.walk(project_path):
            rel_path = os.path.relpath(root, project_path)
            if rel_path == '.':
                rel_path = ''

            dirs[:] = [d for d in dirs if not d.startswith('.') and
                       d not in forbidden_dirs and
                       not should_ignore(os.path.join(rel_path, d), gitignore_patterns)]

            # Check if directory should be skipped if it has no README.md or files to include
            if 'README.md' not in files and not any(
                    os.path.splitext(file)[1] in supported_extensions for file in files):
                continue

            # Write directory path relative from the project root
            f.write(f'## {os.path.join(rel_path)}\n\n')

            # If README.md exists, write its contents first
            if 'README.md' in files:
                readme_path = os.path.join(root, 'README.md')
                with open(readme_path, 'r') as readme_file:
                    readme_content = readme_file.read()
                f.write(readme_content + '\n\n')
                files.remove('README.md')

            for file in files:
                file_rel_path = os.path.join(rel_path, file)
                if should_ignore(file_rel_path, gitignore_patterns):
                    continue

                _, ext = os.path.splitext(file)
                if ext in supported_extensions:
                    if include_pattern and not re.search(include_pattern, file):
                        continue
                    if exclude_pattern and re.search(exclude_pattern, file):
                        continue
                    file_path: str = os.path.join(root, file)
                    with open(file_path, 'r') as code_file:
                        code_content: str = code_file.read()
                    # Write file name as fully qualified path relative from the project root
                    f.write(f'### {file_rel_path}\n\n')
                    f.write(f'```{supported_extensions[ext]}\n')
                    f.write(code_content)
                    f.write("\n```")
                    f.write("\n")
    logging.info(f'Markdown file generated: {output_file}')


def main() -> None:
    config = load_config()
    logging_level = config['log_level'].upper()
    logging.getLogger().setLevel(logging_level)

    parser = argparse.ArgumentParser(description='Generate a single markdown file for a project.')
    parser.add_argument('project_path', nargs='?', default=config['project_path'],
                        help='Path to the project directory (default: current directory from config)')
    parser.add_argument('-i', '--include', default=config['include_pattern'],
                        help='Regular expression pattern to include specific files or directories')
    parser.add_argument('-e', '--exclude', default=config['exclude_pattern'],
                        help='Regular expression pattern to exclude specific files or directories')
    parser.add_argument('-o', '--outfile', default=config['outfile'], help='Output markdown file name')
    parser.add_argument('-l', '--log', default=config['log_level'], help='Set the logging level (default from config)')
    args = parser.parse_args()

    logging.getLogger().setLevel(args.log.upper())

    generate_markdown(args.project_path, args.include, args.exclude, args.outfile)


if __name__ == '__main__':
    main()
