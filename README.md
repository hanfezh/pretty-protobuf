# Pretty Protobuf
It is a plugin for [Sublime Text](https://www.sublimetext.com) 4, used to prettify the debug string of [Protobuf](https://developers.google.com/protocol-buffers) messages.

Use [Python Lex-Yacc](https://www.dabeaz.com/ply) to parse the debug string.

## Installation

Install "Pretty Protobuf" via [Package Control](https://packagecontrol.io/).

Or manually, take macOS as an example:

```bash
# Go to the packages directory of Sublime Text
# Sublime Text -> Preferences -> Browse Packages...
cd $HOME/Library/Application\ Support/Sublime\ Text/Packages
git clone https://github.com/hanfezh/pretty-protobuf.git Pretty\ Protobuf
```

## Usage

To prettify proto's debug string, select message's debug string and run command "Pretty Protobuf: Format Message Debug String" through Command Palette <kbd>Command+Shift+P</kbd> (macOS). If no selection, the entire file is used by default.

To map a key combination like <kbd>Ctrl+Shift+J</kbd> to the Minify command, you can add a setting like this to your .sublime-keymap file (eg: `Packages/User/Default (OSX).sublime-keymap`):

```json
[
    {
        "keys": [
            "ctrl+shift+j"
        ],
        "command": "pretty_debug_string"
    }
]
```

![demo image](https://i.redd.it/on25vd96x6b81.gif)

To prettify Protobuf, execute command "Pretty Protobuf: Format Protobuf":

- Requirements: [clang-format](https://clang.llvm.org/docs/ClangFormat.html)

## Configuration

Default settings for prettifying message debug string:

- *indent*: 4 spaces
- *sort_keys*: false, set true to sort keys
- *use_entire_file_if_no_selection*: true
- *clang_format_path*: clang-format, change to canonical path, such as */usr/local/bin/clang-format*

```json
{
    "indent": 4,
    "sort_keys": false,
    "use_entire_file_if_no_selection": true,
    "clang_format_path": "clang-format"
}
```

