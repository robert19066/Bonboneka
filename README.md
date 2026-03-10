
# 🍬 Bonboneka (bomk)

Bonboneka allows you to bundle your HTML, CSS, and JS assets into a native Android WebView app with a single command(yea its that cool).

# 🚀 Features

- **Automatic Inlining**: Converts external CSS and JS into a single, self-contained HTML file.

- **Asset Encoding**: Automatically converts images into Base64 data URIs.

- **Multi-Bundle Support**: Define multiple entry points and bundles using a simple naming convention.

# 📋 Requirements

- Python: 3.10+

- Git(of course you need git)

- Android SDK + Java: Necessary for...I don't know, BUILDING THE APP?!

# 🛠 Installation

Install the package in editable mode from your local directory(use an env if on Linux):

```bash
pip install -e .
```

# 💻 Usage
```bash
bomk create <path/to/folder> [options]
```
### Options
- `/s`	Silent mode: Suppress all terminal output.
- `/verbose`	Verbose mode: Show detailed build logs.
- `-o <dir>`	Output: Specify the directory for the generated APK.

# 📂 File Naming Convention

To define which bundle a file belongs to, tag the filename with _$<N> before the extension.

Example Structure:
```plaintext

my_app/
├── index_$1.html          ← Main entry point (Group 1)
├── styles_$1.css          ← Styles for Group 1
├── script_$1.js           ← Logic for Group 1
├── start_$2.html          ← Secondary page (Group 2)
├── styleofstart_$2.css    ← Styles for Group 2
└── backend_$2.js          ← Logic for Group 2
```

### NOTE!
Group $1 is always treated as the app's primary entry point.
All assets in a group are bundled into one self-contained HTML file.
----
# ⚙️ Configuration

Customize your build environment by editing bomk/config.py:
```Python
# The repository used as the Android project scaffold
TEMPLATE_REPO      = "https://github.com/YourUser/Example-Android-WV-App.git"

# Relative paths within the template
ASSETS_REL_PATH    = "app/src/main/assets"
MAIN_JAVA_REL_PATH = "app/src/main/java/exampleWV/app/Main.java"
```

# 🌐 Encased Mode

#### Bonboneka can create a wrapper for an website
```bash
bomk create --encased <url> [options]
```
#### Example:
```bash
bomk create --encased https://example.com -o ./dist /verbose
```
Bonboneka will:
- Generate an html file
- Take the url
- Add an `iframe`
- Add the website to the `iframe`
- Generate a WebView Android project
- Build the APK automatically

# `bomk doctor` - Troubleshooting advisor

The `bomk doctor` command will troubleshoot any **valid** Bonboneka projects.
Usage:
```bash
bomk doctor <path-to-project>
```

#### Output:
```plaintext
folder from bomk is runned/
└── example.apk
```
# 🌟 Quick Start 
#### Example

To build the app located in ./my_app and output the APK to the ./dist folder with full logging:
```bash
bomk create ./my_app -o ./dist /verbose
```