# markdown_to_code.py

This is a self‐contained Python script that:
1. Reads a single text input (e.g. from stdin, or from a file) that contains one or more code blocks delimited by triple backticks.
2.	Distinguishes between:
* Full file listings, which specify either inline or via a comment/metadata the target filename and the complete new contents.
* Git diffs (unified diff format, prefixed with diff --git ...), which are used to update existing files in place.

When the script encounters a full file listing, it simply writes that content to the specified file.
When it encounters a git diff, it applies it to the existing file on disk via a minimal unified-diff parser/patcher.

Note: This script implements a simple unified diff parser and applier from scratch (no external libraries). 
It assumes the input diff blocks are valid and well-formed. If there are lines that fail to match exactly, it will 
raise an exception.

# How it Works
1. Extract Code Blocks
* We look for sequences of triple backticks using a regex. Each captured block is then processed independently.
2. Identify Diff vs. Full File
* The block has a line starting with diff --git ..., we treat it as a unified diff and hand it off to apply_unified_diff().
* Otherwise, we attempt to parse a filename out of the block by scanning for lines like:
3.	Applying Diffs
* We parse the unified diff by looking for each diff --git a/... b/... line pair, then read each hunk.
* The script reads the existing file from disk, checks the hunk’s “old” lines match exactly, and if so, replaces them with the “new” lines.
* Finally, it writes the updated file back out.

# Usage
```shell
# Run:
python markdown_to_code.py < examples/r1_7b_bot_creator_response.txt

# Or
cat examples/r1_7b_bot_creator_response.txt | python apply_llm_code.py
```
     
