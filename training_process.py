"""Child-process entry point for one Anomalib training run."""

import sys
from pathlib import Path

import yaml
from anomalib.data import Folder
from anomalib.engine import Engine


def main(arguments):
    (
        model_config,
        results_dir,
        data_name,
        root_path,
        normal_name,
        abnormal_name,
        train_batch_size,
        eval_batch_size,
        workers,
        seed,
    ) = arguments

    datamodule = Folder(
        name=data_name,
        root=root_path,
        normal_dir=normal_name,
        abnormal_dir=abnormal_name,
        train_batch_size=int(train_batch_size),
        eval_batch_size=int(eval_batch_size),
        num_workers=int(workers),
        seed=int(seed),
    )
    datamodule.setup()
    engine, model, _ = Engine.from_config(
        config_path=Path(model_config),
        default_root_dir=Path(results_dir),
    )
    model.visualizer = False
    engine.train(model=model, datamodule=datamodule)

    latest = Path(results_dir) / model.__class__.__name__ / data_name / "latest"
    if latest.exists():
        metadata_path = latest.resolve() / "training_metadata.yaml"
        with metadata_path.open("w", encoding="utf-8") as metadata_file:
            yaml.safe_dump(
                {"dataset": data_name, "data_root": str(Path(root_path).resolve())},
                metadata_file,
                sort_keys=False,
            )


if __name__ == "__main__":
    main(sys.argv[1:])
