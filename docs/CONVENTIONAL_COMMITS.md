# Conventional Commits

This project follows the [Conventional Commits v1.0.0](https://www.conventionalcommits.org/en/v1.0.0/) specification for all commit messages.

## Format

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

## Types

- `feat`: a new feature
- `fix`: a bug fix
- `docs`: documentation only
- `style`: formatting, no code change
- `refactor`: code change that neither fixes nor adds
- `perf`: performance improvement
- `test`: adding/correcting tests
- `build`: build system or dependencies
- `ci`: CI configuration
- `chore`: maintenance, no src/test change
- `revert`: reverts a previous commit

## Rules

- Use a lowercase type followed by a colon and a space.
- Scope is optional and in parentheses, e.g. `feat(email-collector): ...`.
- Description is imperative, present tense, no trailing period.
- Breaking changes are marked with `!` after type/scope or a `BREAKING CHANGE:` footer.
- One logical change per commit; keep commits atomic.

## Examples

- `feat(email-collector): add per-post dedup and show-more expansion`
- `fix(scraper): retry on Playwright TimeoutError`
- `docs: document conventional commits`
- `feat!: drop Python 3.9 support`
- `fix(api): prevent race on run cancel\n\nBREAKING CHANGE: cancel endpoint now returns 202`
