from datetime import datetime
from pathlib import Path

import yaml
from PySide6.QtCore import QObject, Property, QThread, Signal, Slot, QStringListModel

from TrainedModelsModel import TrainedModelsModel
from TrainingWorker import TrainingWorker


APP_DIR = Path(__file__).resolve().parent
MODELS_DIR = APP_DIR / "models"
RESULTS_DIR = APP_DIR / "results"


class Backend(QObject):
    selectedModelChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._model_files = {}
        self._model_details = {}
        self._selected_model = {}
        self._jobs = {}
        self._available_models = QStringListModel(self)
        self._trained_models = TrainedModelsModel(self)
        self._load_available_models()
        self._refresh_trained_models()

    @Property(QObject, constant=True)
    def availableModels(self):
        return self._available_models

    @Property(QObject, constant=True)
    def trainedModels(self):
        return self._trained_models

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
    def selectedModelVersion(self):
        return self._selected("version")

    @Property(str, notify=selectedModelChanged)
    def selectedModelPath(self):
        return self._selected("path")

    @Property(str, notify=selectedModelChanged)
    def selectedModelConfig(self):
        return self._selected("config")

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
        config_text = "Config file was not produced."
        created_path = config_path if config_path.exists() else version_path
        if config_path.exists():
            config_text = config_path.read_text(encoding="utf-8")
        return {
            "name": f"{model_dir.name} — {dataset_dir.name}",
            "model": model_dir.name,
            "dataset": dataset_dir.name,
            "version": version_path.name,
            "status": "trained",
            "created": datetime.fromtimestamp(created_path.stat().st_mtime).strftime(
                "%Y-%m-%d %H:%M"
            ),
            "path": str(version_path),
            "config": config_text,
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
        running = {
            name: details
            for name, details in self._model_details.items()
            if details.get("status") == "training"
        }
        discovered = {item["name"]: item for item in self._scan_results()}
        # A completed result supersedes its temporary training row with the same name.
        self._model_details = {**running, **discovered}
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
        display_name = f"{model_name} — {data_name}"
        if display_name in self._jobs:
            return

        self._model_details[display_name] = {
            "name": display_name,
            "model": model_name,
            "dataset": data_name,
            "version": "",
            "status": "training",
            "created": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "path": "",
            "config": "Training in progress…",
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
        worker = TrainingWorker(
            self._model_files[model_name], RESULTS_DIR, settings
        )
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.finished.connect(lambda: self._training_finished(display_name))
        worker.failed.connect(lambda error: self._training_failed(display_name, error))
        worker.finished.connect(thread.quit)
        worker.failed.connect(thread.quit)
        thread.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(lambda: self._jobs.pop(display_name, None))
        self._jobs[display_name] = (thread, worker)
        thread.start()

    @Slot(str)
    def _training_finished(self, name):
        self._model_details.pop(name, None)
        self._refresh_trained_models()

    @Slot(str, str)
    def _training_failed(self, name, error):
        details = self._model_details.get(name)
        if details:
            details["status"] = "failed"
            details["config"] = f"Training failed:\n{error}"
            self._trained_models.upsert(name, "failed")
