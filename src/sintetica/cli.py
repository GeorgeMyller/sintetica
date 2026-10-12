"""Linha de comando `sintetica`: protocolo `request`/`submit` do harness (D-22), contrato
de dados `schema build | show | approve` (feature 003, D-19) e entrevista de intenção
`start` e `intent questions | set | show | confirm` (feature 004, D-14).

Códigos de saída: 0 sucesso, 2 dataset ou argumento inválido, 3 limite do harness,
4 pedido inexistente, 5 resposta inválida, 6 definição de schema inválida,
7 código de schema gerado inválido ou desatualizado, 8 resposta da entrevista inválida,
9 mascaramento de PII indisponível, 10 falha de escrita, 11 contrato não aprovado ou
desatualizado, 12 falha do provedor, 13 amostra não aprovável (feature 005), 14 amostra
ausente ou de outra versão do contrato, 15 custo exige autorização, 16 lote em andamento,
interrompido ou já existente (feature 006), 17 dataset reprovado, 18 dataset final
ausente (feature 007).
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from decimal import Decimal, InvalidOperation
from pathlib import Path

from sintetica.command import cli_command
from sintetica.dotenv import load_dotenv
from sintetica.providers.domain import GenerationRequest
from sintetica.providers.errors import RequestStoreError
from sintetica.providers.harness.store import MAX_HARNESS_RECORDS, MAX_SUBMIT_BYTES, RequestStore

EXIT_OK = 0
EXIT_USAGE = 2
EXIT_LIMIT = 3


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="sintetica")
    sub = parser.add_subparsers(dest="command", required=True)

    req = sub.add_parser("request", help="grava um pedido de registros para o agente do harness")
    req.add_argument("slug")
    req.add_argument("--n-records", type=int, required=True)
    req.add_argument("--instructions", required=True)
    req.add_argument("--schema", type=Path, required=True, help="arquivo JSON Schema do registro")
    req.add_argument("--seeds", type=Path, help="arquivo JSONL com registros de exemplo")
    req.add_argument("--project-dir", type=Path, default=Path.cwd())

    sub_ = sub.add_parser("submit", help="envia os registros gerados (JSONL na entrada padrão)")
    sub_.add_argument("slug")
    sub_.add_argument("request_id")
    sub_.add_argument("--project-dir", type=Path, default=Path.cwd())

    schema = sub.add_parser("schema", help="contrato de dados do dataset")
    schema_sub = schema.add_subparsers(dest="schema_command", required=True)
    for name, text in (
        ("build", "valida o rascunho e gera schema.json, schema.py e record.schema.json"),
        ("show", "mostra a tabela do contrato atual"),
        ("approve", "aprova o contrato atual"),
    ):
        cmd = schema_sub.add_parser(name, help=text)
        cmd.add_argument("slug")
        cmd.add_argument("--project-dir", type=Path, default=Path.cwd())

    modes = ("guiado", "expresso")
    start = sub.add_parser("start", help="cria a pasta do dataset e inicia a entrevista")
    start.add_argument("name", nargs="?", default=None, help="nome do dataset")
    start.add_argument("--mode", choices=modes, default="guiado")
    start.add_argument("--project-dir", type=Path, default=Path.cwd())

    intent = sub.add_parser("intent", help="entrevista de intenção")
    intent_sub = intent.add_subparsers(dest="intent_command", required=True)
    questions = intent_sub.add_parser("questions", help="mostra as 5 perguntas")
    questions.add_argument("--mode", choices=modes, default="guiado")
    set_ = intent_sub.add_parser("set", help="registra respostas")
    set_.add_argument("slug")
    for item in ("objective", "structure", "rules", "format", "volume"):
        set_.add_argument(f"--{item}")
    set_.add_argument(
        "--unknown",
        action="append",
        default=[],
        choices=("objective", "structure", "rules", "format", "volume"),
        help="item respondido com 'não sei' (repetível)",
    )
    set_.add_argument("--project-dir", type=Path, default=Path.cwd())
    for name, text in (("show", "mostra o resumo"), ("confirm", "confirma a intenção")):
        cmd = intent_sub.add_parser(name, help=text)
        cmd.add_argument("slug")
        cmd.add_argument("--project-dir", type=Path, default=Path.cwd())

    sample = sub.add_parser("sample", help="amostra de 3 a 5 registros para aprovação")
    sample_sub = sample.add_subparsers(dest="sample_command", required=True)
    run = sample_sub.add_parser("run", help="pede, lê e revisa a amostra")
    run.add_argument("slug")
    run.add_argument("--n", type=int, default=None, help="registros na amostra (3 a 5)")
    adjust = sample_sub.add_parser("adjust", help="pede uma nova amostra com um ajuste")
    adjust.add_argument("slug")
    adjust.add_argument("text", help="pedido de ajuste em linguagem natural")
    for name, text in (("approve", "aprova a amostra"), ("show", "mostra a amostra atual")):
        cmd = sample_sub.add_parser(name, help=text)
        cmd.add_argument("slug")
    for cmd in (run, adjust):
        cmd.add_argument("--project-dir", type=Path, default=Path.cwd())
    for name in ("approve", "show"):
        sample_sub.choices[name].add_argument("--project-dir", type=Path, default=Path.cwd())

    gen = sub.add_parser("generate", help="gera o lote completo do dataset")
    gen.add_argument("slug")
    gen.add_argument("--resume", action="store_true", help="retoma o lote interrompido")
    gen.add_argument("--new", action="store_true", help="apaga output/ e gera de novo")
    gen.add_argument(
        "--authorize-usd", type=_usd, default=None, help="valor de custo autorizado em US$"
    )
    gen.add_argument("--block-size", type=int, default=None, help="registros por pedido (1 a 100)")
    status = sub.add_parser("status", help="mostra o progresso do lote")
    status.add_argument("slug")
    ev = sub.add_parser("eval", help="avalia a qualidade do dataset final")
    ev.add_argument("slug")
    for cmd in (gen, status, ev):
        cmd.add_argument("--project-dir", type=Path, default=Path.cwd())
    return parser


def _usd(text: str) -> Decimal:
    try:
        value = Decimal(text.replace(",", "."))
    except InvalidOperation:
        raise argparse.ArgumentTypeError(f"valor inválido: {text}") from None
    return value


def _progress(line: str) -> None:
    print(line, flush=True)


def _generate(args: argparse.Namespace) -> int:
    from sintetica.batch import service

    result = service.generate(
        args.project_dir,
        args.slug,
        resume=args.resume,
        new=args.new,
        authorize_usd=args.authorize_usd,
        block_size_override=args.block_size,
        progress=_progress,
    )
    return _print_result(result.out, result.err, result.code)


def _eval(args: argparse.Namespace) -> int:
    from sintetica.quality import service

    result = service.evaluate(args.project_dir, args.slug)
    return _print_result(result.out, result.err, result.code)


def _status(args: argparse.Namespace) -> int:
    from sintetica.batch import service

    result = service.status(args.project_dir, args.slug)
    return _print_result(result.out, result.err, result.code)


def _sample(args: argparse.Namespace) -> int:
    from sintetica.sample import service

    if args.sample_command == "run":
        result = service.run(args.project_dir, args.slug, args.n)
    elif args.sample_command == "adjust":
        result = service.adjust(args.project_dir, args.slug, args.text)
    elif args.sample_command == "approve":
        result = service.approve(args.project_dir, args.slug)
    else:
        result = service.show(args.project_dir, args.slug)
    return _print_result(result.out, result.err, result.code)


def _print_result(out: list[str], err: list[str], code: int) -> int:
    for line in out:
        print(line)
    for index, line in enumerate(err):
        print(f"erro: {line}" if index == 0 else line, file=sys.stderr)
    return code


def _start(args: argparse.Namespace) -> int:
    from sintetica.intent import service

    result = service.start(args.project_dir, args.name, args.mode)
    return _print_result(result.out, result.err, result.code)


def _intent(args: argparse.Namespace) -> int:
    from sintetica.intent import Answers, service

    if args.intent_command == "questions":
        result = service.questions(args.mode)
    elif args.intent_command == "set":
        texts = {
            name: getattr(args, name)
            for name in ("objective", "structure", "rules")
            if getattr(args, name) is not None
        }
        answers = Answers(texts, args.format, args.volume, set(args.unknown))
        result = service.set_answers(args.project_dir, args.slug, answers)
    elif args.intent_command == "show":
        result = service.show(args.project_dir, args.slug)
    else:
        result = service.confirm(args.project_dir, args.slug)
    return _print_result(result.out, result.err, result.code)


def _schema(args: argparse.Namespace) -> int:
    # Importação tardia: o Pydantic só carrega quando o subcomando schema é usado (R-07).
    from sintetica.schema import service

    command = {"build": service.build, "show": service.show, "approve": service.approve}
    result = command[args.schema_command](args.project_dir, args.slug)
    for line in result.out:
        print(line)
    for line in result.err:
        print(f"erro: {line}" if line is result.err[0] else line, file=sys.stderr)
    return result.code


def _dataset_dir(project_dir: Path, slug: str) -> Path | None:
    path = project_dir / "datasets" / slug
    return path if path.is_dir() else None


def _fail(message: str, code: int) -> int:
    print(f"erro: {message}", file=sys.stderr)
    return code


def _load_json_object(path: Path, what: str) -> dict[str, object]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{what} deve conter um objeto JSON")
    return data


def _load_seeds(path: Path | None) -> list[dict[str, object]]:
    if path is None:
        return []
    seeds = [json.loads(line) for line in path.read_text("utf-8").splitlines() if line.strip()]
    if not all(isinstance(s, dict) for s in seeds):
        raise ValueError("cada linha de --seeds deve ser um objeto JSON")
    return seeds


def _request(args: argparse.Namespace) -> int:
    dataset = _dataset_dir(args.project_dir, args.slug)
    if dataset is None:
        return _fail(f"dataset inexistente: datasets/{args.slug}", EXIT_USAGE)
    if args.n_records < 1:
        return _fail("--n-records deve ser maior ou igual a 1", EXIT_USAGE)
    if args.n_records > MAX_HARNESS_RECORDS:
        return _fail(
            f"o harness atende até {MAX_HARNESS_RECORDS} registros por pedido; "
            f"pedido: {args.n_records}",
            EXIT_LIMIT,
        )
    try:
        schema = _load_json_object(args.schema, "--schema")
        seeds = _load_seeds(args.seeds)
    except (OSError, ValueError) as exc:
        return _fail(str(exc), EXIT_USAGE)
    store = RequestStore(dataset)
    rid = store.save_request(GenerationRequest(schema, seeds, args.instructions, args.n_records))
    print("Pedido do harness gravado.")
    print(f"  id: {rid}")
    print(f"  registros: {args.n_records}")
    print(f"  arquivo: {store.request_path(rid).resolve()}")
    print("Gere os registros conforme o arquivo e envie 1 objeto JSON por linha:")
    print(f"  {cli_command()} submit {args.slug} {rid} < registros.jsonl")
    return EXIT_OK


def _submit(args: argparse.Namespace) -> int:
    dataset = _dataset_dir(args.project_dir, args.slug)
    if dataset is None:
        return _fail(f"dataset inexistente: datasets/{args.slug}", EXIT_USAGE)
    store = RequestStore(dataset)
    replacing = store.response_path(args.request_id).exists()
    raw = sys.stdin.buffer.read(MAX_SUBMIT_BYTES + 1)
    try:
        count = store.submit(args.request_id, raw)
    except RequestStoreError as exc:
        return _fail(str(exc), exc.exit_code)
    if replacing:
        print(f"Aviso: a resposta anterior do pedido {args.request_id} foi substituída.")
    print(f"Resposta gravada: {count} registros em {store.response_path(args.request_id)}")
    return EXIT_OK


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    proj = getattr(args, "project_dir", None)
    load_dotenv((proj / ".env") if isinstance(proj, Path) else None)
    if args.command == "request":
        return _request(args)
    if args.command == "schema":
        return _schema(args)
    if args.command == "start":
        return _start(args)
    if args.command == "intent":
        return _intent(args)
    if args.command == "sample":
        return _sample(args)
    if args.command == "generate":
        return _generate(args)
    if args.command == "status":
        return _status(args)
    if args.command == "eval":
        return _eval(args)
    return _submit(args)


if __name__ == "__main__":
    sys.exit(main())
