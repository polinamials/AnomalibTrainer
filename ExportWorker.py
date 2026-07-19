from PySide6.QtCore import QObject, Signal, Slot


class ExportWorker(QObject):
    finished = Signal(str)
    failed = Signal(str)

    def __init__(self, config_path, checkpoint_path, export_dir, file_name):
        super().__init__()
        self.config_path = config_path
        self.checkpoint_path = checkpoint_path
        self.export_dir = export_dir
        self.file_name = file_name

    @Slot()
    def run(self):
        try:
            from anomalib.deploy import ExportType
            from anomalib.engine import Engine

            engine, model, _ = Engine.from_config(config_path=self.config_path)
            output = engine.export(
                model=model,
                export_type=ExportType.ONNX,
                export_root=self.export_dir,
                model_file_name=self.file_name,
                ckpt_path=self.checkpoint_path,
            )
            if output is None:
                raise RuntimeError("Anomalib did not produce an ONNX file.")
            self.finished.emit(str(output))
        except Exception as error:
            self.failed.emit(str(error))
