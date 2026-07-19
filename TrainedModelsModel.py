from PySide6.QtCore import QAbstractListModel, QModelIndex, Qt


class TrainedModelsModel(QAbstractListModel):
    NameRole = Qt.UserRole + 1
    StatusRole = Qt.UserRole + 2

    def __init__(self, parent=None):
        super().__init__(parent)
        self._models = []

    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self._models)

    def data(self, index, role):
        if not index.isValid() or not 0 <= index.row() < len(self._models):
            return None
        model = self._models[index.row()]
        return {
            self.NameRole: model["name"],
            self.StatusRole: model["status"],
        }.get(role)

    def roleNames(self):
        return {self.NameRole: b"name", self.StatusRole: b"status"}

    def upsert(self, name, status):
        """Insert a model once, or update its existing row in place."""
        for row, model in enumerate(self._models):
            if model["name"] == name:
                if model["status"] != status:
                    model["status"] = status
                    index = self.index(row)
                    self.dataChanged.emit(index, index, [self.StatusRole])
                return

        row = len(self._models)
        self.beginInsertRows(QModelIndex(), row, row)
        self._models.append({"name": name, "status": status})
        self.endInsertRows()

    def replace(self, models):
        self.beginResetModel()
        self._models = list(models)
        self.endResetModel()

    def remove(self, name):
        for row, model in enumerate(self._models):
            if model["name"] == name:
                self.beginRemoveRows(QModelIndex(), row, row)
                self._models.pop(row)
                self.endRemoveRows()
                return
