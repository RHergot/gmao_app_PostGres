#!/usr/bin/env python3
"""
DatabaseWorker - QThread générique pour exécuter des requêtes DB en arrière-plan.

Utilisation future:
    worker = DatabaseWorker(my_db_function, arg1, arg2, kw1=val1)
    worker.finished.connect(handle_result)
    worker.error.connect(handle_error)
    worker.start()
"""

import logging
from typing import Any, Callable

from PySide6.QtCore import QThread, Signal

logger = logging.getLogger(__name__)


class DatabaseWorker(QThread):
    """
    Worker générique pour exécuter une fonction callable dans un thread séparé.

    Signaux émis:
        finished (object): Émis avec le résultat de la fonction callable.
        error (Exception): Émis avec l'exception si une erreur survient.

    Utilisation:
        worker = DatabaseWorker(lambda: my_service.get_data())
        worker.finished.connect(self.on_data_loaded)
        worker.error.connect(self.on_error)
        worker.start()
    """

    # Signal émis quand la fonction se termine avec succès
    finished = Signal(object)

    # Signal émis quand une exception est levée dans la fonction
    error = Signal(Exception)

    def __init__(
        self,
        func: Callable,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """
        Initialise le worker avec la fonction à exécuter et ses arguments.

        Args:
            func: Fonction callable à exécuter dans le thread.
            *args: Arguments positionnels passés à func.
            **kwargs: Arguments nommés passés à func.
        """
        super().__init__()
        self._func = func
        self._args = args
        self._kwargs = kwargs

    def run(self) -> None:
        """
        Exécute la fonction dans le thread et émet les signaux appropriés.
        Appelée automatiquement par QThread.start().
        """
        try:
            result = self._func(*self._args, **self._kwargs)
            self.finished.emit(result)
        except Exception as exc:
            logger.error(
                "DatabaseWorker: erreur dans le thread %s: %s",
                self._func.__name__ if hasattr(self._func, '__name__') else 'unknown',
                exc,
            )
            self.error.emit(exc)
