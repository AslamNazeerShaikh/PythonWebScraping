# Tokei — count your code, quickly

[Tokei](https://github.com/XAMPPRocky/tokei) is the CLI used to produce the
language-usage table in [`README.md`](../README.md#codebase-stats-tokei). It
counts files, lines, code, comments, and blanks grouped by language, and is
very fast (millions of lines in seconds). Installed here via Homebrew:
`brew install tokei` (v15.0.0 at time of writing).

Source documentation: https://github.com/XAMPPRocky/tokei#how-to-use-tokei

## Basic usage

Report on the code in `./foo` and all subfolders:

```bash
tokei ./foo
```

Multiple folders in one call:

```bash
tokei ./foo ./bar ./baz
```

This repo:

```bash
tokei .
```

## Excluding folders

Tokei respects all `.gitignore` and `.ignore` files. Use `--exclude` to
exclude additional files (same semantics as `.gitignore`):

```bash
tokei ./foo --exclude *.rs
```

Paths to exclude can also be listed in a `.tokeignore` file.

## Sorting output

By default tokei sorts alphabetically by language name; `--sort` can sort by
any column (`blanks`, `code`, `comments`, `lines`):

```bash
tokei ./foo --sort code
```

## File statistics

By default tokei only outputs language totals. Use `--files` to also print
individual file statistics:

```bash
tokei ./foo --files
```

## Output formats

Tokei normally prints a human-readable table. Other formats are available via
`--output` (`json`, `yaml`, `cbor`) for piping into other programs:

```bash
tokei ./foo --output json
```

## Reading stored output

Tokei can ingest a previous run's output (file path, inline value, or stdin):

```bash
tokei ./foo --input ./stats.json
```

## Useful flags

- `-f, --files` — print individual file statistics.
- `--hidden` — count hidden files.
- `-l, --languages` — list supported languages and extensions.
- `--no-ignore` / `--no-ignore-dot` / `--no-ignore-parent` / `--no-ignore-vcs` — control ignore-file handling.
- `-e, --exclude <pattern>` — ignore files/directories matching the pattern.
- `-o, --output <format>` — `cbor`, `json`, `yaml`.
- `-s, --sort <column>` — `files`, `lines`, `blanks`, `code`, `comments`.
- `-t, --type <types>` — filter by language type, comma-separated (e.g. `-t=Python,Markdown`).
- `-c, --columns <n>` — strict column width for terminal output.
- `-v, --verbose` — log verbosity (1 = unknown extensions, 3 = file trace).

## Common issue

Tokei may report a lot of D code when there is none — usually `gcc`
generating `.d` files. Exclude them with:

```bash
tokei . -e *.d
```
