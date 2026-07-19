from datetime import datetime
from pathlib import Path
import shutil

import yaml
from PySide6.QtCore import (
    QObject, Property, QSettings, QThread, Signal, Slot, QStringListModel,
)

from TrainedModelsModel import TrainedModelsModel
from TrainingWorker import TrainingWorker
from ExportWorker import ExportWorker


APP_DIR = Path(__file__).resolve().parent
MODELS_DIR = APP_DIR / "models"
RESULTS_DIR = APP_DIR / "results"


class Backend(QObject):
    selectedModelChanged = Signal()
    trainingCompleted = Signal(str)
    trainingFailed = Signal(str, str)
    trainingCanceled = Signal(str)
    exportCompleted = Signal(str, str)
    exportFailed = Signal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._model_files = {}
        self._model_details = {}
        self._selected_model = {}
        self._jobs = {}
        self._export_jobs = {}
        self._available_models = QStringListModel(self)
        self._trained_models = TrainedModelsModel(self)
        self._settings = QSettings("AnomalibTrainer", "AnomalibTrainer")
        self.trainingCompleted.connect(self._training_finished)
        self.trainingFailed.connect(self._training_failed)
        self.trainingCanceled.connect(self._training_canceled)
        self.exportCompleted.connect(self._export_finished)
        self.exportFailed.connect(self._export_failed)
        self._load_available_models()
        self._refresh_trained_models()

    @Property(QObject, constant=True)
    def availableModels(self):
        return self._available_models

    @Property(QObject, constant=True)
    def trainedModels(self):
        return self._trained_models

    @Property("QVariantMap", constant=True)
    def trainingDefaults(self):
        return {
            "model": self._settings.value("training/model", "", type=str),
            "dataset": self._settings.value("training/dataset", "", type=str),
            "rootPath": self._settings.value("training/rootPath", "", type=str),
            "normalFolder": self._settings.value(
                "training/normalFolder", "normal", type=str
            ),
            "abnormalFolder": self._settings.value(
                "training/abnormalFolder", "abnormal", type=str
            ),
            "trainBatchSize": self._settings.value(
                "training/trainBatchSize", 1, type=int
            ),
            "evalBatchSize": self._settings.value(
                "training/evalBatchSize", 1, type=int
            ),
            "workers": self._settings.value("training/workers", 16, type=int),
            "seed": self._settings.value("training/seed", 42, type=int),
        }

    def _save_training_defaults(self, values):
        for key, value in values.items():
            self._settings.setValue(f"training/{key}", value)
        self._settings.sync()

    def _selected(self, key):
        return str(self._selected_model.get(key, ""))

    @Property(str, notify=selectedModelChanged)
    def selectedModelName(self):
        return self._selected("name")

    @Property(str, notify=selectedModelChanged)
    def selectedModelStatus(self):
        return self._selected("status")

    @Property(str, notify=selectedModelChanged)
    def selectedModelCreated(self):
        return self._selected("created")

    @Property(str, notify=selectedModelChanged)
    def selectedModelDataset(self):
        return self._selected("dataset")

    @Property(str, notify=selectedModelChanged)
    def selectedModelDataRoot(self):
        return self._selected("data_root")

    @Property(str, notify=selectedModelChanged)
    def selectedModelVersion(self):
        return self._selected("version")

    @Property(str, notify=selectedModelChanged)
    def selectedModelPath(self):
        return self._selected("path")

    def _load_available_models(self):
        for config_path in MODELS_DIR.glob("*.yaml"):
            with config_path.open(encoding="utf-8") as config_file:
                config = yaml.safe_load(config_file) or {}
            class_path = config.get("model", {}).get("class_path", "")
            if class_path:
                self._model_files[class_path.rsplit(".", 1)[-1]] = config_path
        self._available_models.setStringList(sorted(self._model_files))

    @staticmethod
    def _version_path(dataset_dir):
        latest = dataset_dir / "latest"
        if latest.exists():
            return latest.resolve()
        versions = [path for path in dataset_dir.iterdir() if path.is_dir()]
        return max(versions, key=lambda path: path.stat().st_mtime, default=None)

    def _read_result(self, model_dir, dataset_dir):
        version_path = self._version_path(dataset_dir)
        if version_path is None:
            return None
        config_path = version_path / "config.yaml"
        checkpoints = list(version_path.rglob("*.ckpt"))
        if not config_path.exists() or not checkpoints:
            return None
        created_path = config_path if config_path.exists() else version_path
        with config_path.open(encoding="utf-8") as config_file:
            config = yaml.safe_load(config_file) or {}
        data = config.get("data", {})
        data_args = data.get("init_args", data) if isinstance(data, dict) else {}
        data_root = data_args.get("root", "") if isinstance(data_args, dict) else ""
        export_path = (
            version_path / "export" / "weights" / "onnx"
            / f"{model_dir.name}-{dataset_dir.name}.onnx"
        )
        return {
            "name": f"{model_dir.name}-{dataset_dir.name}",
            "model": model_dir.name,
            "dataset": dataset_dir.name,
            "version": version_path.name,
            "status": "exported" if export_path.exists() else "trained",
            "created": datetime.fromtimestamp(created_path.stat().st_mtime).strftime(
                "%Y-%m-%d %H:%M"
            ),
            "path": str(version_path),
            "dataset_path": str(dataset_dir),
            "data_root": str(data_root),
            "config_path": str(config_path),
            "checkpoint_path": str(max(checkpoints, key=lambda path: path.stat().st_mtime)),
            "export_path": str(export_path) if export_path.exists() else "",
        }

    def _scan_results(self):
        if not RESULTS_DIR.is_dir():
            return []
        results = []
        for model_dir in sorted(RESULTS_DIR.iterdir()):
            if not model_dir.is_dir():
                continue
            for dataset_dir in sorted(model_dir.iterdir()):
                if dataset_dir.is_dir():
                    result = self._read_result(model_dir, dataset_dir)
                    if result:
                        results.append(result)
        return results

    def _refresh_trained_models(self):
        transient = {
            name: details
            for name, details in self._model_details.items()
            if details.get("status") in {"training", "exporting", "failed"}
        }
        discovered = {item["name"]: item for item in self._scan_results()}
        # A completed result supersedes its temporary training row with the same name.
        self._model_details = {**discovered, **transient}
        rows = [
            {"name": name, "status": details["status"]}
            for name, details in sorted(self._model_details.items())
        ]
        self._trained_models.replace(rows)

    @Slot(str)
    def loadModel(self, name):
        details = self._model_details.get(name)
        if details is not None:
            self._selected_model = details
            self.selectedModelChanged.emit()

    @Slot(str, str, str, str, str, int, int, int, int)
    def startTraining(
        self, model_name, data_name, root_path, normal_name, abnormal_name,
        train_batch_size, eval_batch_size, workers, seed,
    ):
        self._save_training_defaults({
            "model": model_name,
            "dataset": data_name,
            "rootPath": root_path,
            "normalFolder": normal_name,
            "abnormalFolder": abnormal_name,
            "trainBatchSize": train_batch_size,
            "evalBatchSize": eval_batch_size,
            "workers": workers,
            "seed": seed,
        })
        display_name = f"{model_name}-{data_name}"
        if display_name in self._jobs:
            return

        previous_details = self._model_details.get(display_name)
        previous_details = dict(previous_details) if previous_details else None
        dataset_dir = RESULTS_DIR / model_name / data_name
        existing_versions = {
            str(path.resolve())
            for path in dataset_dir.iterdir()
            if dataset_dir.is_dir() and path.name != "latest" and path.is_dir()
        } if dataset_dir.is_dir() else set()
        latest = dataset_dir / "latest"
        previous_latest = str(latest.resolve()) if latest.exists() else ""

        self._model_details[display_name] = {
            "name": display_name,
            "model": model_name,
            "dataset": data_name,
            "version": "",
            "status": "training",
            "created": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "path": "",
            "data_root": root_path,
        }
        self._trained_models.upsert(display_name, "training")

        settings = {
            "name": data_name,
            "root": root_path,
            "normal_dir": normal_name,
            "abnormal_dir": abnormal_name,
            "train_batch_size": train_batch_size,
            "eval_batch_size": eval_batch_size,
            "num_workers": workers,
            "seed": seed,
        }
        thread = QThread(self)
        thread.setObjectName(display_name)
        worker = TrainingWorker(
            self._model_files[model_name], RESULTS_DIR, settings
        )
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.finished.connect(lambda: self.trainingCompleted.emit(display_name))
        worker.failed.connect(lambda error: self.trainingFailed.emit(display_name, error))
        worker.finished.connect(worker.deleteLater)
        worker.failed.connect(worker.deleteLater)
        worker.finished.connect(thread.quit)
        worker.failed.connect(thread.quit)
        worker.canceled.connect(lambda: self.trainingCanceled.emit(display_name))
        worker.canceled.connect(worker.deleteLater)
        worker.canceled.connect(thread.quit)
        thread.finished.connect(self._training_thread_finished)
        thread.finished.connect(thread.deleteLater)
        self._jobs[display_name] = {
            "thread": thread,
            "worker": worker,
            "previous": previous_details,
            "dataset_dir": dataset_dir,
            "existing_versions": existing_versions,
            "previous_latest": previous_latest,
            "cancel_requested": False,
            "cleanup_done": False,
        }
        thread.start()

    @Slot()
    def _training_thread_finished(self):
        thread = self.sender()
        if thread is not None:
            name = thread.objectName()
            job = self._jobs.get(name)
            if job and job["cancel_requested"] and not job["cleanup_done"]:
                self._restore_canceled_training(name, job)
            self._jobs.pop(name, None)

    @Slot(str)
    def cancelTraining(self, name):
        job = self._jobs.get(name)
        if job is not None:
            job["cancel_requested"] = True
            job["worker"].cancel()
            self._restore_previous_entry(name, job)

    @Slot(str)
    def _training_canceled(self, name):
        job = self._jobs.get(name)
        if job is not None:
            self._restore_canceled_training(name, job)

    def _restore_previous_entry(self, name, job):
        previous = job["previous"]
        if previous:
            self._model_details[name] = previous
            self._trained_models.upsert(name, previous["status"])
        else:
            self._model_details.pop(name, None)
            self._trained_models.remove(name)

    def _restore_canceled_training(self, name, job):
        """Remove only files made by the canceled run and restore the old latest link."""
        dataset_dir = job["dataset_dir"]
        if dataset_dir.is_dir():
            for path in list(dataset_dir.iterdir()):
                if path.name == "latest" or not path.is_dir():
                    continue
                if str(path.resolve()) not in job["existing_versions"]:
                    shutil.rmtree(path)

            latest = dataset_dir / "latest"
            if latest.is_symlink():
                latest.unlink()
            previous_latest = Path(job["previous_latest"]) if job["previous_latest"] else None
            if previous_latest and previous_latest.is_dir():
                latest.symlink_to(previous_latest, target_is_directory=True)
            try:
                dataset_dir.rmdir()
            except OSError:
                pass

        job["cleanup_done"] = True
        self._restore_previous_entry(name, job)

    @Slot(str)
    def _training_finished(self, name):
        self._model_details.pop(name, None)
        self._refresh_trained_models()

    @Slot(str, str)
    def _training_failed(self, name, error):
        details = self._model_details.get(name)
        if details:
            details["status"] = "failed"
            self._trained_models.upsert(name, "failed")

    @Slot(str)
    def exportModel(self, name):
        details = self._model_details.get(name)
        if (
            not details
            or details["status"] not in {"trained", "exported"}
            or name in self._jobs
            or name in self._export_jobs
        ):
            return
        details["status_before_export"] = details["status"]
        details["status"] = "exporting"
        self._trained_models.upsert(name, "exporting")

        thread = QThread(self)
        thread.setObjectName(name)
        worker = ExportWorker(
            details["config_path"],
            details["checkpoint_path"],
            Path(details["path"]) / "export",
            name,
        )
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.finished.connect(lambda path: self.exportCompleted.emit(name, path))
        worker.failed.connect(lambda error: self.exportFailed.emit(name, error))
        worker.finished.connect(worker.deleteLater)
        worker.failed.connect(worker.deleteLater)
        worker.finished.connect(thread.quit)
        worker.failed.connect(thread.quit)
        thread.finished.connect(self._export_thread_finished)
        thread.finished.connect(thread.deleteLater)
        self._export_jobs[name] = (thread, worker)
        thread.start()

    @Slot()
    def _export_thread_finished(self):
        thread = self.sender()
        if thread is not None:
            self._export_jobs.pop(thread.objectName(), None)

    @Slot(str, str)
    def _export_finished(self, name, path):
        details = self._model_details.get(name)
        if details:
            details["status"] = "exported"
            details.pop("status_before_export", None)
            details["export_path"] = path
            self._trained_models.upsert(name, "exported")

    @Slot(str, str)
    def _export_failed(self, name, error):
        details = self._model_details.get(name)
        if details:
            details["status"] = details.pop("status_before_export", "trained")
            self._trained_models.upsert(name, details["status"])

    @Slot(str)
    def deleteModel(self, name):
        details = self._model_details.get(name)
        if not details or name in self._jobs or name in self._export_jobs:
            return

        dataset_path_text = details.get("dataset_path", "")
        if dataset_path_text:
            dataset_path = Path(dataset_path_text).resolve()
            results_path = RESULTS_DIR.resolve()
            try:
                dataset_path.relative_to(results_path)
            except ValueError:
                return
            if dataset_path != results_path and dataset_path.is_dir():
                shutil.rmtree(dataset_path)

        self._model_details.pop(name, None)
        self._trained_models.remove(name)
