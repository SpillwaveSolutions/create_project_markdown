#!/usr/bin/env python3
import re
import os
import sys
from pygments.lexers import guess_lexer_for_filename, guess_lexer
from pygments.util import ClassNotFound

TRIPLE_BACKTICK_PATTERN = re.compile(
    r'```(.*?)```',
    re.DOTALL | re.MULTILINE
)

# More comprehensive filename pattern matching including markdown headers
FILENAME_PATTERN = re.compile(
    r'^(?:###\s*[^\(]+\((?P<fname1>[^\)]+)\)\s*$|'  # Matches ### Some Comment (filename.py)
    r'\s*#\s*File:\s*(?P<fname2>[^\r\n]+)|'
    r'\s*filename:\s*(?P<fname3>[^\r\n]+)|'
    r'^\s*(?P<fname4>[^:\r\n]+)\s*$|'
    r'^\s*```(?P<lang>[a-zA-Z0-9\+\-\.]+)\s*$)',  # Captures language from opening ```
    re.MULTILINE
)

# Mapping of common language names to extensions
LANG_TO_EXT = {
    'python': '.py',
    'py': '.py',
    'numpy': '.py',  # Numpy is Python code
    'python3': '.py',
    'py3': '.py',
    'java': '.java',
    'javascript': '.js',
    'js': '.js',
    'typescript': '.ts',
    'ts': '.ts',
    'go': '.go',
    'csharp': '.cs',
    'cs': '.cs',
    'bash': '.sh',
    'sh': '.sh',
    'sql': '.sql',
    'yaml': '.yaml',
    'yml': '.yaml',
    'toml': '.toml',
    'markdown': '.md',
    'md': '.md',
    'xml': '.xml',
    'html': '.html',
    'css': '.css',
    'json': '.json'
}

# Detect if a code block is a diff (unified diff) by this first line signature.
DIFF_HEADER_PATTERN = re.compile(r'^diff --git ', re.MULTILINE)

# Detect diff file lines:
#   --- a/path
#   +++ b/path
DIFF_OLD_FILE_PATTERN = re.compile(r'^--- a/(.*)')
DIFF_NEW_FILE_PATTERN = re.compile(r'^\+\+\+ b/(.*)')

# Detect hunk lines of form: @@ -start,len +start,len @@
DIFF_HUNK_PATTERN = re.compile(
    r'^@@ -(?P<old_start>\d+)(?:,(?P<old_len>\d+))? '
    r'\+(?P<new_start>\d+)(?:,(?P<new_len>\d+))? @@'
)


def parse_triple_backticks(text):
    """
    Finds all triple-backtick code blocks in 'text' and returns a list of
    their string contents (no backticks).
    """
    blocks = TRIPLE_BACKTICK_PATTERN.findall(text)
    # Strip off leading/trailing whitespace in each code block for neatness
    return [block.strip('\r\n') for block in blocks]


def is_diff_block(block):
    """
    Quick check to see if this code block starts with 'diff --git ' line,
    which typically indicates a unified diff.
    """
    return bool(DIFF_HEADER_PATTERN.search(block))


def parse_filename_from_block(block):
    """
    Tries to parse a filename from a code block that is presumably
    a full file listing (not a diff).

    Returns (filename, code_without_filename_line).
    If no filename is found, returns (None, original block).
    If filename has no extension, tries to detect language and add appropriate extension.
    """
    # Search for a line that looks like a filename indicator
    match = FILENAME_PATTERN.search(block)
    if not match:
        return None, block

    fname = match.group('fname1') or match.group('fname2') or match.group('fname3') or match.group('fname4')
    if not fname:
        return None, block

    # Extract base filename and check for extension
    base_name = os.path.basename(fname)
    name, ext = os.path.splitext(base_name)
    
    # If no extension, try to detect from language hint or content
    if not ext:
        # First try to get language from code block opening ```
        lang_match = FILENAME_PATTERN.search(block)
        lang = lang_match.group('lang') if lang_match else None
        
        # If no language hint, try to detect from content
        if not lang:
            try:
                # Extract just the code content between triple backticks
                code_content = '\n'.join([line for line in block.splitlines() 
                                        if not line.strip().startswith('#') and 
                                        not line.strip().startswith('filename:') and
                                        not line.strip().startswith('File:')])
                
                # First try to detect from filename if present
                if base_name:
                    try:
                        lexer = guess_lexer_for_filename(base_name, code_content)
                        lang = lexer.name.lower()
                        print(f"[INFO] Detected language from filename: {lang}")
                    except ClassNotFound:
                        # Fall back to content-only detection
                        lexer = guess_lexer(code_content)
                        lang = lexer.name.lower()
                        print(f"[INFO] Detected language from content: {lang}")
            except ClassNotFound:
                # If we have a filename, try to get extension from it
                if '.' in base_name:
                    ext = '.' + base_name.split('.')[-1]
                    print(f"[INFO] Using extension from filename: {ext}")
                else:
                    lang = None
                    print(f"[INFO] Could not detect language from content")
        
        # Get extension from language mapping
        if lang and lang in LANG_TO_EXT:
            ext = LANG_TO_EXT[lang]
            print(f"[INFO] Using extension {ext} for language {lang}")
        elif ext:  # If we got an extension from filename
            pass  # Keep it
        else:
            # Default to .txt only if we really can't determine
            ext = '.txt'
            print(f"[WARNING] Using .txt extension as fallback")
        
        fname = fname + ext

    # Handle markdown header case differently
    if match.group('fname1'):
        # For markdown headers with (filename), we want to keep all code lines
        # since the filename is in the header line
        new_block = block
    else:
        # The line with the filename might be anywhere; remove that line from the content
        lines = block.splitlines(True)  # keep line endings
        # We'll remove the matched line so it won't end up in the file content.
        matched_line = match.group(0)
        # Rebuild content without that line
        new_lines = []
        for ln in lines:
            if matched_line.strip() == ln.strip():
                # skip that line
                continue
            new_lines.append(ln)
        new_block = "".join(new_lines)

    return fname.strip(), new_block


def apply_unified_diff(diff_text):
    """
    Parses a unified diff text (one or more diff entries) and applies it
    to each corresponding file on disk, *in place*.

    If any mismatch occurs (the patch does not match the file as expected),
    this function raises an Exception.
    """
    lines = diff_text.splitlines()
    idx = 0
    n = len(lines)

    while idx < n:
        line = lines[idx]
        if line.startswith('diff --git '):
            idx += 1
            # Expect lines: --- a/..., +++ b/..., then possibly more data
            old_file_line = lines[idx] if idx < n else ''
            idx += 1
            new_file_line = lines[idx] if idx < n else ''
            idx += 1

            old_file_m = DIFF_OLD_FILE_PATTERN.match(old_file_line)
            new_file_m = DIFF_NEW_FILE_PATTERN.match(new_file_line)
            if not old_file_m or not new_file_m:
                raise ValueError("Invalid diff file lines:\n{}\n{}".format(old_file_line, new_file_line))

            old_file = old_file_m.group(1)
            new_file = new_file_m.group(1)

            # In many diffs, old_file and new_file are the same, but let's treat them as the same path.
            # If they differ, your logic might need to rename files. For simplicity, we'll assume same path.
            target_file = new_file if new_file else old_file

            # Now gather hunk lines until next 'diff --git ' or end
            diff_chunks = []
            while idx < n and not lines[idx].startswith('diff --git '):
                diff_chunks.append(lines[idx])
                idx += 1

            # Apply these hunk lines to the file
            apply_diff_hunks_to_file(target_file, diff_chunks)
        else:
            # If we land on something that's not 'diff --git ', skip it
            # or break. (Some diff tools add 'index ...' lines, we can skip them).
            idx += 1


def apply_diff_hunks_to_file(filename, hunk_lines):
    """
    Given the lines that belong to a single diff for 'filename' and
    possibly multiple @@ hunks, apply them to the existing file on disk.
    """
    # Read existing file content
    if not os.path.exists(filename):
        raise FileNotFoundError(f"File to patch does not exist: {filename}")
    with open(filename, 'r', encoding='utf-8') as f:
        original_lines = f.readlines()

    patched_lines = original_lines[:]  # start with a copy, apply changes
    offset = 0  # we'll track shifting offsets as we insert/delete lines

    idx = 0
    n = len(hunk_lines)

    while idx < n:
        line = hunk_lines[idx]
        # Look for the hunk header
        hunk_m = DIFF_HUNK_PATTERN.match(line)
        if not hunk_m:
            # Could be 'index ...' lines or blank lines, skip.
            idx += 1
            continue

        old_start = int(hunk_m.group('old_start'))
        old_len = hunk_m.group('old_len')
        new_start = int(hunk_m.group('new_start'))
        new_len = hunk_m.group('new_len')

        old_len = int(old_len) if old_len else 1
        new_len = int(new_len) if new_len else 1

        # Convert from 1-based to 0-based
        old_start -= 1
        new_start -= 1

        idx += 1
        hunk_body = []
        while idx < n and not hunk_lines[idx].startswith('@@ '):
            hunk_body.append(hunk_lines[idx])
            idx += 1

        # Now we have the lines belonging to this hunk in hunk_body.
        # Let's verify that the old lines match, then replace with new lines.
        # The typical scheme: lines beginning with ' ' or '-' correspond to old lines,
        # lines beginning with ' ' or '+' correspond to new lines.
        # We'll collect them separately.
        old_chunk = []
        new_chunk = []
        for hl in hunk_body:
            if hl.startswith('-') or hl.startswith(' '):
                old_chunk.append(hl[1:])
            if hl.startswith('+') or hl.startswith(' '):
                if hl.startswith('+'):
                    new_chunk.append(hl[1:])
                else:
                    new_chunk.append(hl[1:])  # space line is also part of new

        # Validate old lines in patched_lines
        # Because we've potentially inserted or removed lines in previous hunks,
        # we must account for 'offset' in referencing patched_lines.
        # The old lines we expect to see in the patched file:
        patched_slice = patched_lines[old_start + offset: old_start + offset + old_len]
        if patched_slice != old_chunk:
            raise ValueError(
                f"Patch hunk does not match file contents:\n"
                f"Expected (old): {old_chunk}\n"
                f"Found in file : {patched_slice}"
            )

        # Now do the replacement in patched_lines
        patched_lines[old_start + offset: old_start + offset + old_len] = new_chunk

        # Adjust offset
        # net change in line count = len(new_chunk) - old_len
        offset += (len(new_chunk) - old_len)

    # Finally write out the patched file
    with open(filename, 'w', encoding='utf-8') as f:
        f.writelines(patched_lines)


def process_llm_response(text):
    """
    Main driver that:
    1. Extracts triple-backtick blocks.
    2. Distinguishes between full-file blocks and diff blocks.
    3. Writes new files or applies patches as needed.
    """
    blocks = parse_triple_backticks(text)
    for block in blocks:
        if is_diff_block(block):
            # It's a diff; parse and apply
            print("[INFO] Applying diff block...")
            apply_unified_diff(block)
        else:
            # It's presumably a full file listing
            print("[INFO] Processing full file block...")
            filename, content = parse_filename_from_block(block)
            if not filename:
                print("[WARNING] Could not determine filename; skipping block.")
                continue
            # Ensure target directory exists
            dirname = os.path.dirname(filename)
            if dirname and not os.path.exists(dirname):
                os.makedirs(dirname, exist_ok=True)
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"[INFO] Wrote file: {filename}")


if __name__ == "__main__":
    """
    Usage:
        Run: python markdown_to_code.py < my_llm_response.txt
           or  cat my_llm_response.txt | python apply_llm_code.py
    """
    input_text = sys.stdin.read()
    process_llm_response(input_text)
