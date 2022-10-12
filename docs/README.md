# Build the documentation

The documentation is built using Github pages on each commit to the main branch.

## Build locally

Tested on Fedora 36.

Install the dependciesm make sure to install ruby >= 3.0
```
dnf module install ruby
dnf install ruby-devel
```

Install jekyll and all dependencies:
```
bundle config set --local path 'vendor/bundle'
bundle install --path vendor
```

Build and serve the site locally:
```
bundle exec jekyll serve
```
