"""Run tests/sublime_integration in a portable Sublime Text.

    python tools/run_sublime_integration.py <portable Sublime Text folder> [--host33]

The folder is where sublime_text(.exe) lives, e.g. an unpacked
https://download.sublimetext.com/sublime_text_build_4215_x64.zip.
A "Data" folder next to the executable makes Sublime Text portable, so this
does not touch a normal installation. The package is linked (not copied)
into Data/Packages/Stata Improved Editor.

--host33 runs the package on the legacy Python 3.3 plugin host instead (what
Sublime Text 3 uses): a copy of the package with ".python-version" set to 3.3
is installed, the checks run inside that package, and the 3.3 host is enabled.
"""
import json
import os
import shutil
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HARNESS = os.path.join(ROOT, "tests", "sublime_integration", "stata_improved_integration.py")
PACKAGE = "Stata Improved Editor"


def link(target, link_path):
	if os.name == "nt":
		subprocess.check_call(["cmd", "/c", "mklink", "/J", link_path, target], stdout=subprocess.DEVNULL)
	else:
		os.symlink(target, link_path)


def stata_pids():
	if os.name != "nt":
		return set()
	output = subprocess.check_output(["tasklist", "/FO", "CSV", "/NH"]).decode("mbcs", "replace")
	return set(int(line.split('","')[1]) for line in output.splitlines() if line.lower().startswith('"stata'))


def remove_installed_package(path):
	"""Remove the link to the repository (never its contents) or an old copy."""
	if not os.path.lexists(path):
		return
	if os.path.islink(path) or getattr(os.path, "isjunction", lambda p: False)(path):
		os.unlink(path) if os.path.islink(path) else os.rmdir(path)
	elif os.path.realpath(path) != os.path.realpath(ROOT):
		shutil.rmtree(path)
	else:
		raise RuntimeError("refusing to delete %s" % path)


def main(sublime_dir, host33=False, timeout=120):
	executable = os.path.join(sublime_dir, "sublime_text.exe" if os.name == "nt" else "sublime_text")
	data = os.path.join(sublime_dir, "Data")
	packages = os.path.join(data, "Packages")
	user = os.path.join(packages, "User")
	results = os.path.join(data, "stata_improved_integration.json")
	os.makedirs(user, exist_ok=True)
	package_dir = os.path.join(packages, PACKAGE)
	remove_installed_package(package_dir)
	preferences = {"update_check": False, "hot_exit": "disabled", "remember_workspace": False}
	if host33:
		shutil.copytree(ROOT, package_dir, ignore=shutil.ignore_patterns(
			".git", "pictures", "tests", "tools", "docs", "__pycache__"))
		with open(os.path.join(package_dir, ".python-version"), "w") as f:
			f.write("3.3\n")
		harness_dir = package_dir
		preferences["disable_plugin_host_3.3"] = False
	else:
		link(ROOT, package_dir)
		harness_dir = user
	shutil.copy(HARNESS, harness_dir)
	with open(os.path.join(user, "Preferences.sublime-settings"), "w") as f:
		json.dump(preferences, f)
	if os.path.exists(results):
		os.remove(results)

	stata_before = stata_pids()
	process = subprocess.Popen([executable, "--multiinstance"])
	deadline = time.time() + timeout
	while not os.path.exists(results) and time.time() < deadline:
		time.sleep(1)
	try:
		process.wait(15)  # the harness quits Sublime Text itself
	except subprocess.TimeoutExpired:
		process.kill()
	# A Stata started from Sublime Text must keep running after it exits.
	started = stata_pids() - stata_before
	time.sleep(5)
	survived = started & stata_pids()
	for pid in stata_pids() - stata_before:
		subprocess.call(["taskkill", "/F", "/PID", str(pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
	os.remove(os.path.join(harness_dir, os.path.basename(HARNESS)))
	if host33:
		time.sleep(1)
		remove_installed_package(package_dir)
		link(ROOT, package_dir)
	if not os.path.exists(results):
		print("No results after %ds: see the Sublime Text console." % timeout)
		return 2

	with open(results, encoding="utf-8") as f:
		checks = json.load(f)
	if started:
		checks.append({"name": "windows: the Stata started from Sublime Text keeps running after it exits",
			"ok": survived == started, "detail": "started %s, alive 5 s after exit %s (then closed)"
			% (sorted(started), sorted(survived))})
	for c in checks:
		detail = c["detail"] if isinstance(c["detail"], str) else json.dumps(c["detail"], ensure_ascii=False)
		print("%s  %s\n      %s" % ("PASS" if c["ok"] else "FAIL", c["name"], detail.strip().replace("\n", "\n      ")))
	failed = [c for c in checks if not c["ok"]]
	print("\n%d checks, %d failed" % (len(checks), len(failed)))
	return 1 if failed else 0


if __name__ == "__main__":
	args = [a for a in sys.argv[1:] if a != "--host33"]
	if len(args) != 1:
		sys.exit(__doc__)
	sys.exit(main(args[0], host33="--host33" in sys.argv))
