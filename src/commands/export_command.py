from __future__ import annotations

import click

from src.services.book_service import BookService


def run_export(service: BookService) -> None:
    click.echo("=== CSV エクスポート ===")
    output_path = click.prompt("出力ファイルパス", default="export.csv").strip()

    count = service.export_csv(output_path)
    click.secho(f"{count} 件を {output_path} に出力しました。", fg="green")
