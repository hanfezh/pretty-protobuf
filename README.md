# Pretty Proto
It is a plugin for [Sublime Text](https://www.sublimetext.com) 3 & 4, used to prettify the debug string of [Protobuf](https://developers.google.com/protocol-buffers) messages.

Use [Python Lex-Yacc](https://www.dabeaz.com/ply) to parse the debug string.

## Installation

Install "Pretty Proto" via [Package Control](https://packagecontrol.io/)

## Usage

To prettify proto, select message's debug string and run command *pretty_proto* through Command Palette <kbd>Command+Shift+P</kbd> (macOS). If no selection, the entire file is used by default.

To map a key combination like <kbd>Command+Alt+J</kbd> to the Minify command, you can add a setting like this to your .sublime-keymap file (eg: `Packages/User/Default (OSX).sublime-keymap`):

```json
[
    {
        "keys": [
            "super+shift+j"
        ],
        "command": "pretty_proto"
    }
]
```

![demo image](./demo.gif)

## Settings

Default settings:

- *indent*: 4 spaces
- *sort_keys*: false, do not sort keys

```json
{
    "indent": 4,
    "sort_keys": false
}
```

