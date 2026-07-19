from threading import Event

from PySide6.QtCore import QObject, Signal, Slot


class TrainingWorker(QObject):
    finished = Signal()
    failed = Signal(str)
    canceled = Signal()

    def __init__(self, model_config, results_dir, dataset_settings):
        super().__init__()
        self.model_config = model_config
        self.results_dir = results_dir
        self.dataset_settings = dataset_settings
        self._cancel_requested = Event()
        self._engine = None

    def cancel(self):
        self._cancel_requested.set()
        trainer = getattr(self._engine, "_trainer", None)
        if trainer is not None:
            trainer.should_stop = True

    @Slot()
    def run(self):
        try:
            # Importing anomalib is expensive, so keep it off the GUI startup path.
            from anomalib.data import Folder
            from anomalib.engine import Engine

            if self._cancel_requested.is_set():
                self.canceled.emit()
                return
            datamodule = Folder(**self.dataset_settings)
            datamodule.setup()
            if self._cancel_requested.is_set():
                self.canceled.emit()
                return
            self._engine, model, _ = Engine.from_config(
                config_path=self.model_config,
                default_root_dir=self.results_dir,
            )
            model.visualizer = False
            if self._cancel_requested.is_set():
                self.canceled.emit()
                return
            self._engine.train(model=model, datamodule=datamodule)
            if self._cancel_requested.is_set():
                self.canceled.emit()
            else:
                self.finished.emit()
        except Exception as error:
            if self._cancel_requested.is_set():
                self.canceled.emit()
            else:
                self.failed.emit(str(error))
