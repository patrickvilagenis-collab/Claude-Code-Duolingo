"""Arranque de la aplicación."""
from __future__ import annotations


def main() -> None:
    # Import diferido para que los errores de dependencias se muestren claros.
    try:
        from .ui.app import App
    except ImportError as exc:  # pragma: no cover
        raise SystemExit(
            "Faltan dependencias. Instala con:\n"
            "    pip install -r requirements.txt\n"
            f"Detalle: {exc}"
        )

    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
