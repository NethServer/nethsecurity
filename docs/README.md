# Build the documentation

The documentation is built and published to GitHub Pages on each commit to the
`main` branch by the `Build documentation` workflow.

The site includes the auto-generated `python3-nethsec` API reference, produced
with [pydoctor](https://pydoctor.readthedocs.io) and published under
`/apidocs/python3-nethsec/` (linked from *Design → python3-nethsec API*).

## Build locally

The Jekyll dependencies (`github-pages`) pin old gems that do not build on
recent Ruby (4.x). The reliable way to build locally is inside a container with
an older Ruby, then generate the API docs on top of the built site.

```bash
cd docs

# 1. Build the Jekyll site in a container (avoids host Ruby version issues)
podman run --rm -v "$PWD/..":/repo:Z -w /repo/docs ruby:3.3 bash -c '
  gem install bundler -v 2.5.20 --no-document &&
  bundle install &&
  ./prepare.sh &&
  bundle exec jekyll build'

# 2. Generate the python3-nethsec API docs into the built site
pip install docutils pydoctor
pydoctor \
  --project-name=python3-nethsec \
  --make-html \
  --html-output=./_site/apidocs/python3-nethsec \
  --project-base-dir="$PWD/../packages/python3-nethsec" \
  --docformat=restructuredtext \
  --intersphinx=https://docs.python.org/3/objects.inv \
  ../packages/python3-nethsec/src/nethsec

# 3. Serve the built site
python3 -m http.server 4000 --directory ./_site
# open http://localhost:4000
```

The site is served statically (step 3) rather than with `jekyll serve` so that
a rebuild does not wipe the generated API docs.

### Native build (only if the host Ruby can build the gems)

On a host with Ruby 3.x you can build without a container:

```bash
cd docs
bundle config set --local path 'vendor/bundle'
bundle install
./prepare.sh && bundle exec jekyll build
# then run steps 2 and 3 above
```
