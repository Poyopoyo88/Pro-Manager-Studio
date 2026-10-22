"""Permite ejecutar ``python -m pro_manager``."""

import os

import uvicorn


def main() -> None:  # pragma: no cover - arranque del servidor
    uvicorn.run(
        "pro_manager.main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8000")),
    )


if __name__ == "__main__":  # pragma: no cover
    main()
