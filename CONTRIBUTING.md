# Contributing Guidelines

Thank you for your interest in contributing to our project. Whether it's a bug report, new feature, correction, or additional
documentation, we greatly value feedback and contributions from our community.

Please read through this document before submitting any issues or pull requests to ensure we have all the necessary
information to effectively respond to your bug report or contribution.

## Table of Contents
1. [Reporting Bugs/Feature Requests](#Reporting)
2. [Contributing via Pull Requests](#Pulls)
3. [Testing](#Testing)
4. [Style and Formatting](#Style)
5. [Intentionally Vulnerable Dependencies](#Vulnerable)

## Reporting Bugs/Feature Requests <a name="Reporting"></a>

We welcome you to use the GitHub issue tracker to report bugs or suggest features.

When filing an issue, please check [existing open](https://github.com/avishayil/cdk-goat/issues), or [recently closed](https://github.com/avishayil/cdk-goat/issues?utf8=%E2%9C%93&q=is%3Aissue%20is%3Aclosed%20), issues to make sure somebody else hasn't already reported the issue. Please try to include as much information as you can. Details like these are incredibly useful:

* A reproducible test case or series of steps
* The version of our code being used
* Any modifications you've made relevant to the bug
* Anything unusual about your environment or deployment

## Contributing via Pull Requests <a name="Pulls"></a>

Contributions via pull requests are much appreciated. Before sending us a pull request, please ensure that:

1. You are working against the latest source on the *master* branch.
2. You check existing open, and recently merged, pull requests to make sure someone else hasn't addressed the problem already.

To send us a pull request, please:

1. Fork the repository.
2. Modify the source; please focus on the specific change you are contributing. If you also reformat all the code, it will be hard for us to focus on your change.
3. Ensure your changes passes `cdk synth` or indicate in the PR why it does not.
4. Ensure local tests pass automated tests (by running `pytest -v`)
5. Add any relevant test to keep the CDK application in high coverage rate for vulnerable resources.
6. Commit to your fork using clear commit messages.
7. Send us a pull request, answering any default questions in the pull request interface.
8. Pay attention to any automated CI failures reported in the pull request, and stay involved in the conversation.

GitHub provides additional document on [forking a repository](https://help.github.com/articles/fork-a-repo/) and
[creating a pull request](https://help.github.com/articles/creating-a-pull-request/).

We use [Conventional Commits](https://www.conventionalcommits.org/) for commit
messages (e.g. `feat: ...`, `fix: ...`, `chore: ...`, `docs: ...`). This is
enforced locally by a `commit-msg` pre-commit hook (see
[Style and Formatting](#Style)).

## Testing <a name="Testing"></a>

The CDK application ships with a `pytest` suite (`tests/unit/`) that uses
`aws_cdk.assertions.Template` to assert that the synthesized CloudFormation
template still contains the **intended** insecure configurations (public S3
bucket, publicly accessible RDS instance, world-open security groups,
wildcard IAM permissions, etc.). These tests act as guardrails so that a
refactor does not accidentally "fix" a deliberate vulnerability.

To set up your environment and run everything locally:

```bash
# 1. Install CDK and the project (dev) dependencies
npm install -g aws-cdk
poetry install --no-root

# 2. Activate the virtual environment
source .venv/bin/activate

# 3. Install and run the pre-commit hooks (lint + formatting + commit-msg)
pre-commit install
pre-commit run -a

# 4. Synthesize the CloudFormation template
cdk synth

# 5. Run the test suite
pytest -v
```

When adding or changing a construct, add a corresponding assertion so the
vulnerable resource stays covered. All of the above (`pre-commit`, `cdk synth`
and `pytest`) also run automatically in CI on every push to `main`.

## Style and Formatting <a name="Style"></a>

We strive to keep consistent in style and formatting. This hopefully makes navigating CDK Goat easier for users.

CDK Goat uses `Python 3.12` as a programming language and `flake8`, `black`, `isort` as code style linters. You can ensure the linters run smoothly by:
- Installing dev dependencies by running `poetry install --sync`
- Installing pre-commit environment by running `pre-commit install`
- Running linters and automated fixes by running `pre-commit run -a`

## Intentionally Vulnerable Dependencies <a name="Vulnerable"></a>

The bundled DVPWA application under [`cdk/containers/dvpwa`](cdk/containers/dvpwa)
— in particular its [`requirements.txt`](cdk/containers/dvpwa/requirements.txt)
(e.g. `aiohttp==3.5.3`, `jinja2==2.10`, `pyyaml==3.13`) — is **deliberately
vulnerable** and serves as the training target that the Snyk OSS/Code/IaC
scans surface.

**Do not upgrade or "fix" these dependencies.** For this reason:

- `.github/dependabot.yml` intentionally does **not** cover the
  `cdk/containers/dvpwa` directory, so Dependabot will never bump them.
- Only the root and `cdk/` Poetry projects (developer tooling and
  `aws-cdk-lib`) are kept up to date.

We thank you for your contribution and look forward to cooperate with you on this exciting project for the good of all!