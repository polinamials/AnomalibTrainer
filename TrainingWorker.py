from PySide6.QtCore import QObject, Signal, Slot


class TrainingWorker(QObject):
    finished = Signal()
    failed = Signal(str)

    def __init__(self, model_config, results_dir, dataset_settings):
        super().__init__()
        self.model_config = model_config
        self.results_dir = results_dir
        self.dataset_settings = dataset_settings

    @Slot()
    def run(self):
        try:
            # Importing anomalib is expensive, so keep it off the GUI startup path.
            from anomalib.data import Folder
            from anomalib.engine import Engine

            datamodule = Folder(**self.dataset_settings)
            datamodule.setup()
            engine, model, _ = Engine.from_config(
                config_path=self.model_config,
                default_root_dir=self.results_dir,
            )
            model.visualizer = False
            engine.train(model=model, datamodule=datamodule)
            self.finished.emit()
        except Exception as error:
            self.failed.emit(str(error))
