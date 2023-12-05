#!/usr/bin/env bash
set -o errexit
set -o nounset
set -o pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"

printf 'The current stmp version is: '
poetry version -s
read -er -p 'What should the next stmp version be? ' new_version

if [[ -n "$new_version" ]]; then
  poetry version "$new_version"
  git add pyproject.toml
  message="release: v$new_version"
  git commit -m "$message"
  git tag -a -m "$message" "v$new_version"
  git push --atomic --follow-tags
else
  printf 'Aborting release due to empty version name.\n' >&2
  exit 1
fi
