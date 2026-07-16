"""Command-line entry point: `python main.py analyze AAPL`."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys

from .orchestrator import AnalysisReport, FinancialAnalysisOrchestrator


def _print_text_report(report: AnalysisReport) -> None:
    print(f"\n{'=' * 70}")
    print(f"Financial Analysis Report — {report.ticker}")
    print(f"Generated: {report.generated_at}")
    print(f"{'=' * 70}\n")
    print(report.report)


def _print_json_report(report: AnalysisReport) -> None:
    print(
        json.dumps(
            {
                "ticker": report.ticker,
                "generated_at": report.generated_at,
                "report": report.report,
                "agent_findings": report.agent_findings,
            },
            indent=2,
        )
    )


async def _run(ticker: str, output_format: str) -> None:
    orchestrator = FinancialAnalysisOrchestrator()
    report = await orchestrator.analyze(ticker)
    if output_format == "json":
        _print_json_report(report)
    else:
        _print_text_report(report)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="financial-agent",
        description="Multi-agent financial analysis system powered by Claude.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    analyze_parser = subparsers.add_parser("analyze", help="Analyze a stock ticker")
    analyze_parser.add_argument("ticker", help="Stock ticker symbol, e.g. AAPL")
    analyze_parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        dest="output_format",
        help="Output format (default: text)",
    )

    args = parser.parse_args(argv)

    if args.command == "analyze":
        try:
            asyncio.run(_run(args.ticker, args.output_format))
        except Exception as exc:  # noqa: BLE001
            print(f"Error: {exc}", file=sys.stderr)
            return 1
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
