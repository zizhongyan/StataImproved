"""macOS backend: talk to the Stata application through AppleScript.

Stata for Mac understands `DoCommandAsync "<command>" with addToReview`,
which behaves like typing the command into the Command window.
"""

import queue
import subprocess
import threading

# Probed from oldest to newest so the newest installed version wins; the
# range leaves room for future releases.
_PROBED_VERSIONS = range(11, 31)


def _applescript_string(text):
	return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _osascript(script):
	# No "-": the original invoked `osascript<< END`, i.e. no argument and the
	# script on stdin. Same invocation, minus the shell.
	process = subprocess.Popen(["osascript"], stdin=subprocess.PIPE,
		stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	try:
		out, err = process.communicate(script.encode("utf-8"), timeout=60)
	except subprocess.TimeoutExpired:
		process.kill()
		process.communicate()
		raise
	if process.returncode != 0:
		raise RuntimeError(err.decode("utf-8", "replace").strip() or "osascript failed")
	return out.decode("utf-8", "replace").strip()


class MacBackend(object):
	"""Commands are sent in order by one background thread, so a slow
	osascript (Stata starting, an Automation permission prompt) never
	freezes the editor."""

	def __init__(self, settings, report_error):
		self._settings = settings
		self._report_error = report_error
		self._detected_app_id = None
		self._jobs = queue.Queue()
		self._thread = threading.Thread(target=self._work, name="StataImproved-AppleScript")
		self._thread.daemon = True
		self._thread.start()

	def app_id(self):
		version = self._settings().get("stata_version", "auto")
		if str(version).strip().lower() not in ("", "auto"):
			return "com.stata.stata%d" % int(version)
		if self._detected_app_id is None:
			probes = "".join(
				'try\n tell me to get application id "com.stata.stata{0}"\n set stata to {0}\nend try\n'.format(v)
				for v in _PROBED_VERSIONS)
			version = int(_osascript("set stata to 0\n" + probes + "return stata"))
			if version == 0:
				raise RuntimeError("No version of Stata found.")
			self._detected_app_id = "com.stata.stata%d" % version
		return self._detected_app_id

	def send(self, command, activate=False):
		self._jobs.put((command, activate))

	def _work(self):
		while True:
			job = self._jobs.get()
			try:
				if job is None:
					return
				self._send(*job)
			finally:
				self._jobs.task_done()

	def _send(self, command, activate):
		try:
			script = 'tell application id "{0}"\n{1}DoCommandAsync {2} with addToReview\nend tell\n'.format(
				self.app_id(), "activate\n" if activate else "", _applescript_string(command))
			_osascript(script)
		except (OSError, RuntimeError, ValueError, subprocess.TimeoutExpired) as e:
			self._report_error("Could not send the command to Stata:\n%s" % e)

	def close(self):
		self._jobs.put(None)
