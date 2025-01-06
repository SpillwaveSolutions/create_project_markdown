#!/usr/bin/env python3

import os
import re
import argparse
import math
import logging
from typing import List, Optional, Dict, Tuple
from pathspec import PathSpec
from pathspec.patterns import GitWildMatchPattern

# Constants
MAX_FILE_SIZE = 200 * 1024  # 200KB in bytes
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
    '.kt': 'java',
    '.yaml': 'yaml',
    '.toml': 'toml',
    '.sh': 'bash',
    '.sql': 'sql',
    '.avsc': 'avro',
    '.md': 'markdown'
}

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class MarkdownWriter:
    def __init__(self, base_filename: str, max_size: int = MAX_FILE_SIZE):
        self.base_filename = base_filename
        self.max_size = max_size
        self.current_chunk = 0  # Start at 0 since _start_new_chunk increments
        self.current_size = 0
        self.chunks: List[str] = []
        self.current_file = None
        self._start_new_chunk()
        logging.info(f"Initialized MarkdownWriter with max size: {self.max_size / 1024:.2f}KB")

    def _get_chunk_filename(self, chunk_num: int) -> str:
        if chunk_num == 1:
            return self.base_filename
        base, ext = os.path.splitext(self.base_filename)
        return f"{base}_part{chunk_num}{ext}"

    def _start_new_chunk(self) -> None:
        # Close current file if open
        if self.current_file is not None:
            self.current_file.close()
            current_size = os.path.getsize(self._get_chunk_filename(self.current_chunk))
            logging.info(f"Closed chunk {self.current_chunk}, final size: {current_size / 1024:.2f}KB")
            self.chunks.append(self._get_chunk_filename(self.current_chunk))

        self.current_chunk += 1
        filename = self._get_chunk_filename(self.current_chunk)
        logging.info(f"Starting new chunk {self.current_chunk}: {filename}")
        self.current_file = open(filename, 'w', encoding='utf-8')
        self.current_size = 0

        # Write header for new chunk
        if self.current_chunk > 1:  # Not the first chunk
            header = f"# Project Structure (Part {self.current_chunk})\n\n"
            self.current_file.write(header)
            self.current_size = len(header.encode('utf-8'))

    def _check_and_rotate(self, content_size: int) -> None:
        if self.current_size + content_size > self.max_size:
            logging.info(
                f"Size limit would be exceeded: current={self.current_size / 1024:.2f}KB + new={content_size / 1024:.2f}KB > max={self.max_size / 1024:.2f}KB")
            self._start_new_chunk()

    def write(self, content: str) -> None:
        content_bytes = content.encode('utf-8')
        content_size = len(content_bytes)
        logging.debug(f"Writing content of size: {content_size / 1024:.2f}KB")

        # If single content is larger than max_size, split it
        if content_size > self.max_size:
            logging.info(f"Content too large ({content_size / 1024:.2f}KB), splitting")
            lines = content.splitlines(True)  # Keep line endings
            current_lines = []
            current_size = 0

            for line in lines:
                line_bytes = line.encode('utf-8')
                line_size = len(line_bytes)

                if current_size + line_size > self.max_size * 0.9:  # Use 90% threshold
                    # Write accumulated lines
                    chunk_content = ''.join(current_lines)
                    chunk_bytes = chunk_content.encode('utf-8')
                    self._check_and_rotate(len(chunk_bytes))
                    self.current_file.write(chunk_content)
                    self.current_file.flush()
                    self.current_size += len(chunk_bytes)
                    logging.info(
                        f"Wrote chunk of {len(chunk_bytes) / 1024:.2f}KB, total: {self.current_size / 1024:.2f}KB")

                    current_lines = []
                    current_size = 0

                current_lines.append(line)
                current_size += line_size

            # Write remaining lines
            if current_lines:
                chunk_content = ''.join(current_lines)
                chunk_bytes = chunk_content.encode('utf-8')
                self._check_and_rotate(len(chunk_bytes))
                self.current_file.write(chunk_content)
                self.current_file.flush()
                self.current_size += len(chunk_bytes)
                logging.info(
                    f"Wrote final chunk of {len(chunk_bytes) / 1024:.2f}KB, total: {self.current_size / 1024:.2f}KB")
        else:
            # Regular write with size check
            self._check_and_rotate(content_size)
            self.current_file.write(content)
            self.current_file.flush()
            self.current_size += content_size
            logging.debug(f"Current chunk size: {self.current_size / 1024:.2f}KB")

    def close(self) -> None:
        if self.current_file is not None:
            self.current_file.close()
            current_size = os.path.getsize(self._get_chunk_filename(self.current_chunk))
            logging.info(f"Closed final chunk {self.current_chunk}, size: {current_size / 1024:.2f}KB")
            self.chunks.append(self._get_chunk_filename(self.current_chunk))

        # If we created multiple chunks, create an index
        if len(self.chunks) > 1:
            index_content = ["# Project Structure Index\n\n"]
            total_size = 0

            for i, chunk in enumerate(self.chunks, 1):
                chunk_name = os.path.basename(chunk)
                chunk_size = os.path.getsize(chunk)
                total_size += chunk_size
                size_kb = chunk_size / 1024

                if i == 1:
                    index_content.append(f"Main file: [{chunk_name}]({chunk_name}) ({size_kb:.2f}KB)\n")
                else:
                    index_content.append(f"Part {i}: [{chunk_name}]({chunk_name}) ({size_kb:.2f}KB)\n")

            index_content.append(f"\nTotal size: {total_size / 1024:.2f}KB")

            # Write the index file
            with open(self.base_filename, 'w', encoding='utf-8') as f:
                f.write('\n'.join(index_content))
            logging.info(f"Created index file with {len(self.chunks)} chunks, total size: {total_size / 1024:.2f}KB")


def load_gitignore(project_path: str) -> PathSpec:
    gitignore_path = os.path.join(project_path, '.gitignore')
    patterns = []
    if os.path.exists(gitignore_path):
        with open(gitignore_path, 'r') as f:
            patterns = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    return PathSpec.from_lines(GitWildMatchPattern, patterns)


def is_ignored(path: str, root_path: str, gitignore_spec: PathSpec) -> bool:
    """
    Check if a path should be ignored according to gitignore rules.
    Handles both files and directories correctly.
    """
    # Get the path relative to the project root
    rel_path = os.path.relpath(path, root_path)
    if rel_path == '.':
        return False

    # Ensure forward slashes for consistency (especially important on Windows)
    rel_path = rel_path.replace(os.sep, '/')

    # For directories, append a slash to ensure directory patterns match correctly
    if os.path.isdir(path):
        rel_path += '/'

    return gitignore_spec.match_file(rel_path)


def generate_markdown(project_path: str, include_pattern: Optional[str] = None, exclude_pattern: Optional[str] = None,
                      output_file: str = 'project_structure.md') -> None:
    project_path = os.path.abspath(project_path)
    gitignore_spec = load_gitignore(project_path)

    # Clean up any existing output files
    base_name, ext = os.path.splitext(output_file)
    existing_files = [f for f in os.listdir('.') if
                      f == output_file or (f.startswith(f"{base_name}_part") and f.endswith(ext))]
    for file in existing_files:
        try:
            os.remove(file)
            logging.info(f"Removed existing file: {file}")
        except OSError as e:
            logging.warning(f"Error removing file {file}: {e}")

    writer = MarkdownWriter(output_file)

    try:
        project_name = os.path.basename(project_path)
        if project_name != os.path.splitext(os.path.basename(__file__))[0]:
            writer.write(f'# {project_name}\n\n')

        for root, dirs, files in os.walk(project_path):
            # Filter out directories that should be ignored
            dirs[:] = [d for d in dirs
                       if not d.startswith('.')
                       and not d.startswith("node_mod")
                       and not is_ignored(os.path.join(root, d), project_path, gitignore_spec)]

            # Skip this directory if it should be ignored
            if is_ignored(root, project_path, gitignore_spec):
                continue

            level: int = root.replace(project_path, '').count(os.sep)
            indent: str = '#' * (level + 2)

            # Write directory header
            rel_path = os.path.relpath(root, project_path)
            writer.write(f'{indent} {rel_path}/\n\n')

            # Process files in smaller batches
            current_batch = []
            current_batch_size = 0
            max_batch_size = MAX_FILE_SIZE // 2  # Use half max size for batches

            for file in sorted(files):  # Sort files for consistent ordering
                file_path = os.path.join(root, file)
                # Skip the script itself and any gitignored files before processing
                if os.path.samefile(file_path, os.path.abspath(__file__)) or is_ignored(file_path, project_path, gitignore_spec):
                    continue

                _, ext = os.path.splitext(file)
                if ext in SUPPORTED_EXTENSIONS:
                    if include_pattern and not re.search(include_pattern, file):
                        continue
                    if exclude_pattern and re.search(exclude_pattern, file):
                        continue

                    try:
                        with open(file_path, 'r') as code_file:
                            code_content: str = code_file.read()

                        # Create the markdown content for this file
                        file_content = f'{indent}# {file}\n\n```{SUPPORTED_EXTENSIONS[ext]}\n{code_content}\n```\n\n'
                        file_size = len(file_content.encode('utf-8'))

                        # If single file is larger than batch size, write it directly
                        if file_size > max_batch_size:
                            logging.info(f"Large file {file_path}: {file_size / 1024:.2f}KB")
                            writer.write(file_content)
                            continue

                        # If adding this file would exceed batch size, write current batch
                        if current_batch_size + file_size > max_batch_size and current_batch:
                            writer.write(''.join(current_batch))
                            current_batch = []
                            current_batch_size = 0

                        # Add to current batch
                        current_batch.append(file_content)
                        current_batch_size += file_size

                    except UnicodeDecodeError:
                        logging.warning(f"Skipping binary file {file_path}")
                    except Exception as e:
                        logging.error(f"Error processing file {file_path}: {str(e)}")

            # Write any remaining files in the last batch
            if current_batch:
                writer.write(''.join(current_batch))

    finally:
        writer.close()


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
