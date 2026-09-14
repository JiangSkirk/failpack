"""failpack completion — print shell completion scripts."""

from __future__ import annotations

from typing import Literal

ShellName = Literal["bash", "zsh"]

# Keep in sync with cli.build_parser subcommands (plus nested license check).
_COMMANDS = (
    "init doctor demo export import list packs status show capture promote "
    "re-promote watch replay explain diff report lint migrate rm rename "
    "completion license"
).split()


def bash_completion_script() -> str:
    cmds = " ".join(_COMMANDS)
    return f"""\
# FailPack bash completion — install with:
#   eval "$(failpack completion bash)"
# or:
#   failpack completion bash > ~/.local/share/bash-completion/completions/failpack

_failpack() {{
  local cur prev words cword
  COMPREPLY=()
  cur="${{COMP_WORDS[COMP_CWORD]}}"
  prev="${{COMP_WORDS[COMP_CWORD-1]}}"

  local cmds="{cmds}"

  # Top-level: failpack <command>
  if [[ ${{COMP_CWORD}} -eq 1 ]]; then
    COMPREPLY=( $(compgen -W "${{cmds}} --help --version" -- "${{cur}}") )
    return 0
  fi

  local cmd="${{COMP_WORDS[1]}}"
  case "${{cmd}}" in
    completion)
      COMPREPLY=( $(compgen -W "bash zsh" -- "${{cur}}") )
      return 0
      ;;
    license)
      COMPREPLY=( $(compgen -W "check" -- "${{cur}}") )
      return 0
      ;;
    promote|re-promote|status|show|export|rm|rename|replay|explain|diff|report|lint)
      # Pack ids from failpack list (first column)
      local packs
      packs="$(failpack list 2>/dev/null | awk 'NR>2 {{print $1}}')"
      if [[ "${{cmd}}" == "promote" || "${{cmd}}" == "re-promote" ]]; then
        COMPREPLY=( $(compgen -W "--dry-run --suggest --write ${{packs}}" -- "${{cur}}") )
      elif [[ "${{cmd}}" == "rm" ]]; then
        COMPREPLY=( $(compgen -W "--force ${{packs}}" -- "${{cur}}") )
      elif [[ "${{cmd}}" == "replay" ]]; then
        COMPREPLY=( $(compgen -W "--all --json --no-diff ${{packs}}" -- "${{cur}}") )
      elif [[ "${{cmd}}" == "report" ]]; then
        COMPREPLY=( $(compgen -W "--github -o --output --no-diff ${{packs}}" -- "${{cur}}") )
      elif [[ "${{cmd}}" == "show" ]]; then
        COMPREPLY=( $(compgen -W "--json ${{packs}}" -- "${{cur}}") )
      elif [[ "${{cmd}}" == "diff" ]]; then
        COMPREPLY=( $(compgen -W "--json --no-diff ${{packs}}" -- "${{cur}}") )
      elif [[ "${{cmd}}" == "export" ]]; then
        COMPREPLY=( $(compgen -W "-o --output ${{packs}}" -- "${{cur}}") )
      else
        COMPREPLY=( $(compgen -W "${{packs}}" -- "${{cur}}") )
      fi
      return 0
      ;;
    list|packs)
      COMPREPLY=( $(compgen -W "--json --help" -- "${{cur}}") )
      return 0
      ;;
    capture|watch)
      COMPREPLY=( $(compgen -W "--id --force --claude-latest --cursor-latest --from-claude-project --stdin --glob --help" -- "${{cur}}") )
      return 0
      ;;
    import)
      COMPREPLY=( $(compgen -W "--force --rename" -- "${{cur}}") )
      return 0
      ;;
    init)
      COMPREPLY=( $(compgen -W "--ci" -- "${{cur}}") )
      return 0
      ;;
    doctor)
      COMPREPLY=( $(compgen -W "--score --strict --help" -- "${{cur}}") )
      return 0
      ;;
    demo)
      COMPREPLY=( $(compgen -W "--id --no-keep --skip-break --fast" -- "${{cur}}") )
      return 0
      ;;
  esac
  return 0
}}

complete -F _failpack failpack
"""


def zsh_completion_script() -> str:
    cmds = " ".join(_COMMANDS)
    return f"""\
#compdef failpack
# FailPack zsh completion — install with:
#   eval "$(failpack completion zsh)"
# or:
#   failpack completion zsh > "${{fpath[1]}}/_failpack"

_failpack() {{
  local -a commands packs
  commands=({cmds})

  _pack_ids() {{
    local -a ids
    ids=(${{(f)"$(failpack list 2>/dev/null | awk 'NR>2 {{print $1}}')"}} )
    _describe -t packs 'pack id' ids
  }}

  local curcontext="$curcontext" state line
  typeset -A opt_args

  _arguments -C \\
    '(-h --help)'{{-h,--help}}'[show help]' \\
    '(- *)--version[show version]' \\
    '--root[project root]:path:_files -/' \\
    '1:command:->cmds' \\
    '*::arg:->args'

  case $state in
    cmds)
      _describe -t commands 'failpack command' commands
      ;;
    args)
      case $words[1] in
        completion)
          _values 'shell' bash zsh
          ;;
        license)
          _values 'license command' check
          ;;
        promote)
          _arguments \\
            '--dry-run[print assertions without writing]' \\
            '--suggest[recommend assertions from transcript]' \\
            '--write[apply suggested assertions]' \\
            '1:pack id:_pack_ids'
          ;;
        re-promote)
          _arguments \\
            '--dry-run[print assertions without writing]' \\
            '--suggest[recommend assertions from transcript]' \\
            '--write[apply suggested assertions]' \\
            '1:pack id:_pack_ids'
          ;;
        status|rename)
          _arguments '1:pack id:_pack_ids'
          ;;
        show)
          _arguments '--json[JSON output]' '1:pack id:_pack_ids'
          ;;
        diff)
          _arguments \\
            '--json[JSON output]' \\
            '--no-diff[omit unified diffs]' \\
            '1:pack id:_pack_ids'
          ;;
        list|packs)
          _arguments '--json[JSON pack index]'
          ;;
        export)
          _arguments '-o[output path]:path:_files' '--output[output path]:path:_files' \\
            '1:pack id:_pack_ids'
          ;;
        rm)
          _arguments '--force[delete golden packs]' '1:pack id:_pack_ids'
          ;;
        replay)
          _arguments \\
            '--all[replay every golden pack]' \\
            '--json[JSON output]' \\
            '--no-diff[disable fingerprint diffs]' \\
            '1:pack id:_pack_ids'
          ;;
        explain)
          _arguments '1:pack id:_pack_ids'
          ;;
        report)
          _arguments \\
            '--github[write to GITHUB_STEP_SUMMARY]' \\
            '-o[output path]:path:_files' \\
            '--output[output path]:path:_files' \\
            '--no-diff[omit fingerprint diffs]' \\
            '1:pack id:_pack_ids'
          ;;
        lint)
          _arguments '1:pack id:_pack_ids'
          ;;
        capture|watch)
          _arguments \\
            '--id[pack id]:id:' \\
            '--force[overwrite]' \\
            '--claude-latest[newest Claude session]' \\
            '--cursor-latest[newest Cursor agent transcript]' \\
            '--from-claude-project[Claude projects dir]:path:_files -/' \\
            '--stdin[read stdin]' \\
            '--glob[glob pattern]:pattern:' \\
            '1:transcript:_files'
          ;;
        import)
          _arguments \\
            '--force[overwrite]' \\
            '--rename[new id]:id:' \\
            '1:archive:_files'
          ;;
        init)
          _arguments '--ci[write starter workflow]'
          ;;
        doctor)
          _arguments \\
            '--score[print 0-100 readiness score]' \\
            '--strict[exit non-zero on FAIL]'
          ;;
        demo)
          _arguments \\
            '--id[pack id]:id:' \\
            '--no-keep[remove demo pack]' \\
            '--skip-break[skip break/restore]' \\
            '--fast[~60s stranger path]'
          ;;
      esac
      ;;
  esac
}}

_failpack "$@"
"""


def cmd_completion(shell: str) -> str:
    name = shell.strip().lower()
    if name == "bash":
        return bash_completion_script()
    if name == "zsh":
        return zsh_completion_script()
    raise ValueError(f"Unsupported shell {shell!r}. Use: bash or zsh.")
