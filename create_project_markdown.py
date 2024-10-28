#!/usr/bin/env python3

import os
import re
import argparse
from typing import List, Optional, Dict
from pathlib import Path
import fnmatch

# Supported file extensions and their corresponding language identifiers
SUPPORTED_EXTENSIONS: Dict[str, str] = {
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

forbidden_dirs = ['__pycache__', 'dist']

def parse_gitignore(project_path: str) -> List[str]:
    gitignore_path = os.path.join(project_path, '.gitignore')
    if not os.path.exists(gitignore_path):
        return []

    with open(gitignore_path, 'r') as f:
        return [line.strip() for line in f if line.strip() and not line.startswith('#')]

def should_ignore(path: str, gitignore_patterns: List[str]) -> bool:
    print(f"Should ignore {gitignore_patterns} PATH={path}")
    for pattern in gitignore_patterns:
        if fnmatch.fnmatch(path, pattern):
            return True
    return False

def generate_markdown(project_path: str, include_pattern: Optional[str] = None, exclude_pattern: Optional[str] = None,
                      output_file: str = 'project_structure.md') -> None:
    gitignore_patterns = parse_gitignore(project_path)

    with open(output_file, 'w') as f:
        f.write(f'# {os.path.basename(project_path)}\n\n')
        for root, dirs, files in os.walk(project_path):
            rel_path = os.path.relpath(root, project_path)
            if rel_path == '.':
                rel_path = ''

            dirs[:] = [d for d in dirs if not d.startswith('.') and
                       "node_modules" not in d and
                       "cdk.out" not in d and
                        "env" not in d and
                        "venv" not in d
                       and
                       d not in forbidden_dirs and
                       not should_ignore(os.path.join(rel_path, d), gitignore_patterns)]

            level: int = rel_path.count(os.sep)
            indent: str = '#' * (level + 2)
            f.write(f'{indent} {os.path.basename(root)}/\n\n')

            for file in files:
                file_rel_path = os.path.join(rel_path, file)
                if should_ignore(file_rel_path, gitignore_patterns):
                    continue

                _, ext = os.path.splitext(file)
                if ext in SUPPORTED_EXTENSIONS:
                    if include_pattern and not re.search(include_pattern, file):
                        continue
                    if exclude_pattern and re.search(exclude_pattern, file):
                        continue
                    file_path: str = os.path.join(root, file)
                    with open(file_path, 'r') as code_file:
                        code_content: str = code_file.read()
                    f.write(f'{indent}# {file}\n\n')
                    f.write(f'```{SUPPORTED_EXTENSIONS[ext]}\n')
                    f.write(code_content)
                    f.write('\n```\n\n')

def main() -> None:
    parser = argparse.ArgumentParser(description='Generate a single markdown file for a project.')
    parser.add_argument('project_path', nargs='?', default='.',
                        help='Path to the project directory (default: current directory)')
    parser.add_argument('-i', '--include', help='Regular expression pattern to include specific files or directories')
    parser.add_argument('-e', '--exclude', help='Regular expression pattern to exclude specific files or directories')
    parser.add_argument('-o', '--outfile', default='project_structure.md', help='Output markdown file name')
    args = parser.parse_args()

    generate_markdown(args.project_path, args.include, args.exclude, args.outfile)
    print(f'Markdown file generated: {args.outfile}')

if __name__ == '__main__':
    main()