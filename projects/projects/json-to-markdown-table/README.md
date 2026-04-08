# JSON to Markdown Table

A small Python program that converts JSON data into a Markdown table.

## Features
- Converts a JSON array of objects into a Markdown table
- Reads JSON from a file or stdin
- Handles missing keys by leaving cells empty
- Works with nested values by serializing them as JSON strings

## Usage

### From a file
```bash
python main.py input.json
```

### From stdin
```bash
cat input.json | python main.py
```

## Example

Input:
```json
[
  {"name": "Alice", "age": 30},
  {"name": "Bob", "age": 25}
]
```

Output:
```markdown
| name | age |
| --- | --- |
| Alice | 30 |
| Bob | 25 |
```
