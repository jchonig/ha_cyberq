# Contribution guidelines

Contributing to this project should be as easy and transparent as possible,
whether it's:

- Reporting a bug
- Discussing the current state of the code
- Submitting a fix
- Proposing new features

## Github is used for everything

Github is used to host code, to track issues and feature requests, as well as
accept pull requests.

Pull requests are the best way to propose changes to the codebase.

1. Fork the repo and create your branch from `main`.
2. If you've changed something, update the documentation.
3. Make sure your code lints (using `scripts/lint`).
4. Test you contribution.
5. Issue that pull request!

## Any contributions you make will be under the MIT Software License

In short, when you submit code changes, your submissions are understood to be
under the same [MIT License](http://choosealicense.com/licenses/mit/) that
covers the project. Feel free to contact the maintainers if that's a concern.

## Report bugs using Github's [issues](../../issues)

GitHub issues are used to track public bugs.
Report a bug by [opening a new issue](../../issues/new/choose); it's that easy!

## Write bug reports with detail, background, and sample code

**Great Bug Reports** tend to have:

- A quick summary and/or background
- Steps to reproduce
  - Be specific!
  - Give sample code if you can.
- What you expected would happen
- What actually happens
- Notes (possibly including why you think this might be happening, or stuff
  you tried that didn't work)

People *love* thorough bug reports. I'm not even kidding.

## Use a Consistent Coding Style

Use [black](https://github.com/ambv/black) to make sure the code follows the style.

## Test your code modification

This custom component is based on [integration_blueprint template](https://github.com/ludeeus/integration_blueprint).

It comes with development environment in a container, easy to launch
if you use Visual Studio Code. With this container you will have a stand alone
Home Assistant instance running and already configured with the included
[`configuration.yaml`](./config/configuration.yaml)
file.

## Home Assistant compatibility checks

CI imports every module of the integration on three Home Assistant
releases: the minimum version (the `homeassistant` key in `hacs.json`), the
latest stable release and the latest beta. It runs on every push and
nightly, so a Home Assistant release that breaks the integration fails the
build the night it comes out, and a beta failure gives about a week's
warning (beta failures don't fail the run).

The check fails on an import error and on any warning that mentions the
integration, such as a Home Assistant deprecation notice. To run it
locally in a Docker container:

```sh
scripts/ha_compat minimum
scripts/ha_compat latest
scripts/ha_compat beta
```

A deprecation that can't be fixed yet without raising the minimum Home
Assistant version can be listed in `scripts/ha_deprecations_allowed.txt`,
with a comment saying when it can be removed. Listed notices show as
warnings instead of failing the build.

## Release notes

Release notes are built from the merged pull requests since the previous
tag, grouped by the `enhancement`, `bug` and `documentation` labels. Pull
requests labeled `dependencies` (Dependabot) are left out, and so are
commits pushed to `main` without a pull request, so make user-facing
changes through a pull request.

## License

By contributing, you agree that your contributions will be licensed under its
MIT License.
