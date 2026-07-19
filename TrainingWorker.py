import os
import signal
import subprocess
import sys
from pathlib import Path
from threading import Event, Lock

from PySide6.QtCore import QObject, Signal, Slot


class TrainingWorker(QObject):
    """Run Anomalib out of process so cancellation can be immediate and safe."""

    finished = Signal()
    failed = Signal(str)
    canceled = Signal()

    def __init__(self, model_config, results_dir, dataset_settings):
        super().__init__()
        self.model_config = model_config
        self.results_dir = results_dir
        self.dataset_settings = dataset_settings
        self._cancel_requested = Event()
        self._process = None
        self._process_lock = Lock()

    def cancel(self):
        self._cancel_requested.set()
        with self._process_lock:
            process = self._process
            if process is None or process.poll() is not None:
                return
            try:
                if os.name == "posix":
                    os.killpg(process.pid, signal.SIGTERM)
                else:
                    process.terminate()
            except ProcessLookupError:
                pass

    @Slot()
    def run(self):
        if self._cancel_requested.is_set():
            self.canceled.emit()
            return

        entry_point = (
            [sys.executable, "--training-process"]
            if "__compiled__" in globals()
            else [sys.executable, str(Path(__file__).with_name("training_process.py"))]
        )
        command = [
            *entry_point,
            str(self.model_config),
            str(self.results_dir),
            *self._settings_arguments(),
        ]
        try:
            with self._process_lock:
                self._process = subprocess.Popen(
                    command,
                    start_new_session=os.name == "posix",
                )
                if self._cancel_requested.is_set():
                    try:
                        if os.name == "posix":
                            os.killpg(self._process.pid, signal.SIGTERM)
                        else:
                            self._process.terminate()
                    except ProcessLookupError:
                        pass
                process = self._process

            return_code = process.wait()
            if self._cancel_requested.is_set():
                self.canceled.emit()
            elif return_code == 0:
                self.finished.emit()
            else:
                self.failed.emit(f"Training process exited with code {return_code}.")
        except Exception as error:
            if self._cancel_requested.is_set():
                self.canceled.emit()
            else:
                self.failed.emit(str(error))
        finally:
            with self._process_lock:
                self._process = None

    def _settings_arguments(self):
        settings = self.dataset_settings
        return [
            str(settings["name"]),
            str(settings["root"]),
            str(settings["normal_dir"]),
            str(settings["abnormal_dir"]),
            str(settings["train_batch_size"]),
            str(settings["eval_batch_size"]),
            str(settings["num_workers"]),
            str(settings["seed"]),
        ]
