"""Hook PostToolUse (Edit|Write): roda o pyflakes no arquivo .py que o Claude acabou de editar.

Se houver avisos, sai com código 2 e escreve em stderr, para o Claude ver e corrigir.
Qualquer outro caso (arquivo não-.py, sem avisos, pyflakes ausente) termina em silêncio.
"""
import json
import subprocess
import sys


def main() -> int:
    try:
        dados = json.load(sys.stdin)
    except ValueError:
        return 0
    caminho = (dados.get("tool_response") or {}).get("filePath") \
        or (dados.get("tool_input") or {}).get("file_path") or ""
    if not caminho.endswith(".py"):
        return 0
    try:
        r = subprocess.run([sys.executable, "-m", "pyflakes", caminho],
                           capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.SubprocessError):
        return 0
    saida = (r.stdout + r.stderr).strip()
    if r.returncode != 0 and saida and "No module named" not in saida:
        print("pyflakes encontrou problemas:\n" + saida, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
