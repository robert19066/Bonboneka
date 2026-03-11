

"""
bomk/cli.py – Bonboneka command-line interface.

Commands:
    bomk create <folder>              Build an Android app from local files
    bomk create --encased <url>       Wrap a remote URL inside an app
    bomk doctor <template>            Validate an Android template
    bomk gitlink <template>           Manage template git configuration
"""

import os
import re
import sys
import shutil
import subprocess
import argparse
import tempfile
from pathlib import Path

from .lib    import Logger, parse_groups, validate_groups, strip_shebang, SHEBANG_RE
from .inject import bundle_group, inject_assets
from .icon   import inject_icon
from .gitlink import set_origin, set_behaviour, get_behaviour, commit_template, disengage_template, push_template
from .config import TEMPLATE_REPO, ASSETS_REL_PATH


# ── Arg normalisation ─────────────────────────────────────────────────────────

def _normalize_argv(argv: list[str]) -> list[str]:
    out = []
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg == "/s":
            out.append("--silent")
        elif arg == "/verbose":
            out.append("--verbose")
        elif arg == "/encased":
            out.append("--encased")
            if i + 1 < len(argv):
                i += 1
                out.append(argv[i])
        else:
            out.append(arg)
        i += 1
    return out


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="bomk",
        description="Bonboneka Ver 1.6 'Antoneta' - Bundle HTML/CSS/JS into an Android WebView app",
    )
    sub = p.add_subparsers(dest="command")

    create = sub.add_parser(
        "create",
        help="Build an Android app from local files or a URL",
        description="""
Build an Android WebView app from local HTML/CSS/JS files or a remote URL.

EXAMPLES:
  bomk create ./my_app                          # Build from local folder
  bomk create ./my_app --icon ./icon.png        # With custom icon
  bomk create ./my_app --nobuild                # Debug: skip APK build
  bomk create /encased https://example.com      # Wrap a remote URL
  bomk create ./app -o ./build --verbose        # With detailed output
        """.strip(),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    create.add_argument(
        "folder", nargs="?",
        help="Folder containing shebang-tagged source files (omit when using --encased)",
    )
    create.add_argument(
        "--encased", metavar="URL",
        help="Wrap a remote URL inside a generated HTML file",
    )
    create.add_argument(
        "--silent", "-s",
        action="store_true",
        help="Suppress all output",
    )
    create.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed progress and debug messages",
    )
    create.add_argument(
        "--nobuild",
        action="store_true",
        help="Skip APK build; output prepared template to directory (useful for debugging)",
    )
    create.add_argument(
        "--icon",
        metavar="PATH",
        help="Icon image file (PNG/JPG/WebP) to use as app launcher icon. Auto-resizes to all Android densities",
    )
    create.add_argument(
        "-o", "--output",
        default=".",
        metavar="DIR",
        help="Directory to copy the APK into (default: current working directory)",
    )

    doctor = sub.add_parser(
        "doctor",
        help="Validate an Android WebView template",
        description="""
Check if an Android template is valid for use with Bonboneka.

Validates:
  • Assets folder exists
  • Assets folder contains HTML files with shebangs
  • At least one HTML has prime shebang (_$1)

EXAMPLES:
  bomk doctor ./my_template
        """.strip(),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    doctor.add_argument(
        "template",
        help="Path to Android template directory",
    )
    doctor.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed diagnostic information",
    )

    gitlink = sub.add_parser(
        "gitlink",
        help="Manage template git configuration and auto-commit",
        description="""
Configure git integration for your Android template.

Set a remote origin and configure auto-commit behavior.

EXAMPLES:
  bomk gitlink TEMPLATE_PATH --set https://github.com/user/template.git
  bomk gitlink TEMPLATE_PATH --behaviour commit-per-build
  bomk gitlink TEMPLATE_PATH --behaviour manual-commit
  bomk gitlink TEMPLATE_PATH --commit
  bomk gitlink TEMPLATE_PATH --push
  bomk gitlink TEMPLATE_PATH --disengage
        """.strip(),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    gitlink.add_argument(
        "template",
        help="Path to Android template directory",
    )
    gitlink.add_argument(
        "--set",
        metavar="URL",
        help="Set or update the git origin URL",
    )
    gitlink.add_argument(
        "--behaviour",
        choices=["commit-per-build", "manual-commit"],
        help="Set auto-commit behaviour",
    )
    gitlink.add_argument(
        "--commit",
        action="store_true",
        help="Manually commit all pending changes (use with manual-commit behaviour)",
    )
    gitlink.add_argument(
        "--disengage",
        action="store_true",
        help="Reset template to default origin and remove gitlink configuration",
    )
    gitlink.add_argument(
        "--push",
        action="store_true",
        help="Push all commits to the remote repository",
    )

    return p


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    argv = _normalize_argv(sys.argv[1:])
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    level = (
        Logger.SILENT  if getattr(args, "silent", False)  else
        Logger.VERBOSE if getattr(args, "verbose", False) else
        Logger.NORMAL
    )
    log = Logger(level)

    if args.command == "create":
        log.highlight('Bonboneka - Version 1.0 "Antoneta"')
        if getattr(args, "encased", None):
            _cmd_encased(args.encased, args.output, log, nobuild=getattr(args, "nobuild", False), icon=getattr(args, "icon", None))
        elif getattr(args, "folder", None):
            _cmd_create(args.folder, args.output, log, nobuild=getattr(args, "nobuild", False), icon=getattr(args, "icon", None))
        else:
            log.error(
                "Provide a folder path OR use --encased <url>.\n"
                "  bomk create ./my_app\n"
                "  bomk create --encased https://example.com"
            )
            sys.exit(1)
    elif args.command == "doctor":
        _cmd_doctor(args.template, log)
    elif args.command == "gitlink":
        _cmd_gitlink(args.template, log, set_url=args.set, behaviour=args.behaviour, do_commit=args.commit, disengage=args.disengage, do_push=args.push)


# ── create (local files) ──────────────────────────────────────────────────────

def _cmd_create(folder: str, output_dir: str, log: Logger, nobuild: bool = False, icon: str | None = None) -> None:
    folder_path = Path(folder).resolve()
    if not folder_path.is_dir():
        log.error(f"Folder not found: {folder_path}")
        sys.exit(1)

    log.step(f"Scanning: {folder_path}")

    try:
        groups = parse_groups(str(folder_path))
        validate_groups(groups)
    except ValueError as exc:
        log.error(str(exc))
        sys.exit(1)

    log.highlight(f"Found group(s): {sorted(groups.keys())}")

    bundled: dict[str, str] = {}
    for n in sorted(groups.keys()):
        log.step(f"Bundling group ${n} …")
        name, content = bundle_group(groups[n], n, log)
        bundled[name] = content
        log.info(f"  → {name}")

    entry_html = next(
        strip_shebang(f) for f in groups[1] if f.suffix.lower() == ".html"
    )
    log.highlight(f"Entry-point: {entry_html}")

    _run_build_pipeline(bundled=bundled, output_dir=output_dir, log=log, nobuild=nobuild, icon=icon)


# ── create /encased <url> ─────────────────────────────────────────────────────

def _cmd_encased(url: str, output_dir: str, log: Logger, nobuild: bool = False, icon: str | None = None) -> None:
    if not re.match(r"^https?://", url, re.IGNORECASE):
        log.error(f"Invalid URL: {url!r}\n  Must start with http:// or https://")
        sys.exit(1)

    log.step(f"Encased mode → generating wrapper HTML for: {url}")

    # Build a minimal HTML file that loads the URL in a full-screen iframe
    html_content = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    html, body, iframe {{ width: 100%; height: 100%; border: none; display: block; }}
  </style>
</head>
<body>
  <iframe src="{url}" allowfullscreen></iframe>
</body>
</html>
"""

    # Write to a temp folder structured like a normal bomk project:
    # the HTML is tagged as group 1 prime ($1) so the normal pipeline can consume it
    with tempfile.TemporaryDirectory(prefix="bomk_encased_src_") as src_tmp:
        src_path = Path(src_tmp)
        html_file = src_path / "index_$1.html"
        html_file.write_text(html_content, encoding="utf-8")
        log.verbose(f"Generated wrapper HTML → {html_file.name}")

        try:
            groups = parse_groups(str(src_path))
            validate_groups(groups)
        except ValueError as exc:
            log.error(str(exc))
            sys.exit(1)

        bundled: dict[str, str] = {}
        for n in sorted(groups.keys()):
            log.info(f"Bundling group ${n} …")
            name, content = bundle_group(groups[n], n, log)
            bundled[name] = content
            log.info(f"  → {name}")

        # Add INTERNET permission via a flag; pass bundled into the normal pipeline
        _run_build_pipeline(
            bundled=bundled,
            output_dir=output_dir,
            log=log,
            needs_internet=True,
            nobuild=nobuild,
            icon=icon,
        )


# ── doctor command ────────────────────────────────────────────────────────────

def _cmd_doctor(template_path_str: str, log: Logger) -> None:
    """Validate an Android template for use with Bonboneka."""
    template_path = Path(template_path_str).resolve()

    if not template_path.is_dir():
        log.error(f"Template directory not found: {template_path}")
        sys.exit(1)

    log.step(f"Checking template: {template_path.name}")

    # Check for assets folder
    assets_dir = template_path / ASSETS_REL_PATH
    if not assets_dir.exists():
        log.error(f"Assets folder not found: {ASSETS_REL_PATH}")
        sys.exit(1)

    log.success(f"Assets folder found: {ASSETS_REL_PATH}")

    # Check for HTML files in assets
    html_files = list(assets_dir.glob("*.html"))

    if not html_files:
        log.highlight(f"Assets folder is empty (no HTML files)")
        return

    log.success(f"Found {len(html_files)} HTML file(s)")

    # Check for shebangs
    files_with_shebang = []
    files_without_shebang = []
    prime_shebang_found = False

    for html_file in html_files:
        if SHEBANG_RE.match(html_file.name):
            files_with_shebang.append(html_file.name)
            # Check if it's the prime shebang
            m = SHEBANG_RE.match(html_file.name)
            if m and int(m.group(2)) == 1:
                prime_shebang_found = True
                log.verbose(f"  {html_file.name} (prime shebang: _$1)")
            else:
                log.verbose(f"  {html_file.name}")
        else:
            files_without_shebang.append(html_file.name)
            log.verbose(f"  {html_file.name} (no shebang)")

    if files_without_shebang:
        log.error(f"{len(files_without_shebang)} file(s) missing shebang:")
        for fname in files_without_shebang:
            log.info(f"    {fname} → should be renamed to {fname.replace('.html', '_$<N>.html')}")
        sys.exit(1)

    log.success(f"All HTML files have shebangs")

    if not prime_shebang_found:
        log.error("No prime shebang detected: at least one HTML must have _$1 tag")
        sys.exit(1)

    log.success("Prime shebang (_$1) detected")
    log.highlight("Template is valid and ready to use!")


# ── gitlink command ───────────────────────────────────────────────────────────

def _cmd_gitlink(
    template_path_str: str,
    log: Logger,
    set_url: str | None = None,
    behaviour: str | None = None,
    do_commit: bool = False,
    disengage: bool = False,
    do_push: bool = False,
) -> None:
    """Manage git configuration and auto-commit behavior for a template."""
    template_path = Path(template_path_str).resolve()

    if not template_path.is_dir():
        log.error(f"Template directory not found: {template_path}")
        sys.exit(1)

    try:
        if disengage:
            disengage_template(template_path, log)
            return

        if set_url:
            log.step("Setting git origin")
            set_origin(template_path, set_url, log)

        if behaviour:
            log.step(f"Changing behaviour to: {behaviour}")
            set_behaviour(template_path, behaviour, log)

        if do_commit:
            log.step("Committing changes")
            commit_template(template_path, log)

        if do_push:
            push_template(template_path, log)

        # Show current status
        if not do_commit and not set_url and not behaviour and not do_push:
            current_behaviour = get_behaviour(template_path)
            log.info(f"Current behaviour: {current_behaviour}")

    except ValueError as e:
        log.error(str(e))
        sys.exit(1)
    except Exception as e:
        log.error(f"Git operation failed: {e}")
        sys.exit(1)


# ── shared build pipeline ─────────────────────────────────────────────────────

def _run_build_pipeline(
    bundled: dict[str, str],
    output_dir: str,
    log: Logger,
    needs_internet: bool = False,
    nobuild: bool = False,
    icon: str | None = None,
) -> None:
    with tempfile.TemporaryDirectory(prefix="bomk_build_") as tmp:
        template_path = Path(tmp) / "template"

        _clone(template_path, log)
        _write_local_properties(template_path, log)
        _patch_gradle_properties(template_path, log)
        _patch_manifest(template_path, log, needs_internet=needs_internet)

        if icon:
            try:
                inject_icon(template_path, icon, log)
            except (FileNotFoundError, ValueError) as exc:
                log.error(str(exc))
                sys.exit(1)

        if bundled:
            assets_dir = template_path / ASSETS_REL_PATH
            try:
                inject_assets(assets_dir, bundled, log)
            except FileNotFoundError as exc:
                log.error(str(exc))
                sys.exit(1)

        if nobuild:
            # Copy template directory to output
            out = Path(output_dir).resolve()
            out.mkdir(parents=True, exist_ok=True)
            dest = out / "template_output"
            shutil.copytree(str(template_path), str(dest), dirs_exist_ok=True)
            log.success(f"Done!  Template → {dest}")
            log.info(f"Assets injected into: {dest / ASSETS_REL_PATH}")
            return

        apk = _build(template_path, verbose=(log.level == Logger.VERBOSE), log=log)

        if apk and apk.exists():
            out = Path(output_dir).resolve()
            out.mkdir(parents=True, exist_ok=True)
            dest = out / apk.name
            shutil.copy2(str(apk), str(dest))
            log.success(f"Done!  APK → {dest}")
            log.info(f"Output folder: {out}")
        else:
            log.error(
                "Build finished but APK was not found at the expected path.\n"
                f"  Check: {template_path / 'app' / 'build' / 'outputs' / 'apk' / 'debug'}"
            )


# ── Internal helpers ──────────────────────────────────────────────────────────

def _clone(dest: Path, log: Logger) -> None:
    if dest.exists():
        shutil.rmtree(dest)
    log.step(f"Cloning template → {dest.name} …")
    r = subprocess.run(
        ["git", "clone", "--depth", "1", TEMPLATE_REPO, str(dest)],
        capture_output=True, text=True,
    )
    if r.returncode != 0:
        log.error(f"git clone failed:\n{r.stderr.strip()}")
        sys.exit(1)
    log.verbose(f"Cloned to {dest}")
    r2 = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=str(dest), capture_output=True, text=True,
    )
    commit = r2.stdout.strip() if r2.returncode == 0 else "unknown"
    log.info(f"Template commit: {commit}")


def _write_local_properties(template_path: Path, log: Logger) -> None:
    sdk_dir = (
        os.environ.get("ANDROID_HOME") or
        os.environ.get("ANDROID_SDK_ROOT") or
        os.path.expanduser("~/Android/Sdk")
    )
    if not sdk_dir or not Path(sdk_dir).exists():
        log.error(
            "Android SDK not found.\n"
            "Set ANDROID_HOME to your SDK path, e.g.:\n"
            "  export ANDROID_HOME=~/Android/Sdk"
        )
        sys.exit(1)
    sdk_path = str(sdk_dir).replace("\\", "/")
    (template_path / "local.properties").write_text(
        f"sdk.dir={sdk_path}\n", encoding="utf-8"
    )
    log.verbose(f"local.properties: sdk.dir={sdk_path}")


def _patch_gradle_properties(template_path: Path, log: Logger) -> None:
    props_path = template_path / "gradle.properties"
    content = props_path.read_text(encoding="utf-8") if props_path.exists() else ""
    required = {
        "android.useAndroidX":                   "true",
        "android.enableJetifier":                "true",
        "android.suppressUnsupportedCompileSdk": "34",
    }
    for key, val in required.items():
        if key not in content:
            content += f"\n{key}={val}"
            log.verbose(f"gradle.properties: added {key}={val}")
    props_path.write_text(content, encoding="utf-8")


def _patch_manifest(template_path: Path, log: Logger, needs_internet: bool = False) -> None:
    manifests = list(template_path.rglob("AndroidManifest.xml"))
    if not manifests:
        return
    manifest = manifests[0]
    content = manifest.read_text(encoding="utf-8")

    def add_exported(m):
        tag = m.group(0)
        if "android:exported" not in tag:
            tag = tag.rstrip(">").rstrip()
            tag = (
                tag[:-1].rstrip() + ' android:exported="true"/>'
                if tag.endswith("/")
                else tag + '\n        android:exported="true">'
            )
        return tag

    content = re.sub(r"<activity\b[^>]*>", add_exported, content, flags=re.DOTALL)

    if needs_internet and "INTERNET" not in content:
        content = content.replace(
            "<application",
            '<uses-permission android:name="android.permission.INTERNET"/>\n    <application',
            1,
        )
        log.verbose("AndroidManifest.xml: INTERNET permission added")

    manifest.write_text(content, encoding="utf-8")
    log.verbose("AndroidManifest.xml patched")


def _build(template_path: Path, verbose: bool, log: Logger) -> Path | None:
    gradlew = template_path / ("gradlew.bat" if os.name == "nt" else "gradlew")
    if not gradlew.exists():
        log.error("gradlew not found – is the template a valid Android project?")
        sys.exit(1)
    if os.name != "nt":
        gradlew.chmod(gradlew.stat().st_mode | 0o111)

    subprocess.run(
        [str(gradlew), "--stop"],
        cwd=str(template_path), capture_output=True, text=True,
    )

    log.highlight("Building APK (this may take a while) …")
    cmd = [
        str(gradlew), "assembleDebug",
        "--no-daemon", "--warning-mode", "none", "--stacktrace",
    ]
    r = subprocess.run(cmd, cwd=str(template_path), capture_output=not verbose, text=True)

    if r.returncode != 0:
        output = (r.stderr or r.stdout or "").strip()
        m = re.search(r"\* What went wrong:\n(.+?)(?=\n\* |\Z)", output, re.DOTALL)
        detail = m.group(1).strip() if m else output[-3000:]
        log.error(f"Gradle build failed:\n{detail}")
        sys.exit(1)

    apk = template_path / "app" / "build" / "outputs" / "apk" / "debug" / "app-debug.apk"
    if apk.exists():
        log.success(f"APK ready: {apk}")
    else:
        log.info("Build finished (APK not at expected path; check build/outputs/)")
    return apk if apk.exists() else None


if __name__ == "__main__":
    main()