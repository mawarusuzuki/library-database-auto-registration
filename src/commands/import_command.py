from __future__ import annotations

import click

from src.services.book_service import BookService


def run_import(service: BookService) -> None:
    click.echo("=== CSV 一括インポート ===")
    csv_path = click.prompt("CSV ファイルパス").strip()

    try:
        result = service.import_csv(csv_path)
    except FileNotFoundError as e:
        click.secho(f"[エラー] {e}", fg="red")
        return

    click.echo("\nインポート完了")
    click.secho(f"  成功           : {result.success} 件", fg="green")
    click.secho(f"  スキップ（重複）: {result.skipped} 件", fg="yellow")
    click.secho(f"  エラー         : {result.errors} 件", fg="red" if result.errors else "white")

    if result.error_details:
        click.echo("\nエラー詳細:")
        for detail in result.error_details:
            click.secho(f"  - {detail}", fg="red")

    click.echo("詳細は logs/register.log を確認してください。")
