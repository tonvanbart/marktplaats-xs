# deploy-workflow Spec Delta

## ADDED Requirements

### Requirement: Daily cron and manual dispatch triggers
A GitHub Actions workflow SHALL run the fetch pipeline on both a daily
cron schedule and on `workflow_dispatch` (manual trigger).

#### Scenario: Scheduled run
- **WHEN** 06:00 UTC arrives
- **THEN** GitHub Actions SHALL (best-effort) trigger the workflow and
  a fresh build SHALL be deployed to GitHub Pages

#### Scenario: Manual run
- **WHEN** a maintainer clicks "Run workflow" in the Actions tab
- **THEN** the workflow SHALL execute immediately without waiting for
  the next cron tick

### Requirement: Stateless Pages deployment via `actions/deploy-pages`
The workflow SHALL publish the generated `site/` directory using
`actions/upload-pages-artifact` and `actions/deploy-pages`. It SHALL
NOT commit generated files to any branch. It SHALL NOT rely on any
persistent state between runs.

#### Scenario: Two consecutive runs
- **WHEN** the workflow runs twice in sequence
- **THEN** each run SHALL produce a fresh artifact from the current
  Marktplaats data
- **AND** no state from the first run SHALL be required by the second

### Requirement: Correct Pages permissions and environment
The workflow SHALL declare `permissions: contents: read, pages: write,
id-token: write` and SHALL reference `environment: name: github-pages`
on the deploy job, as required by `actions/deploy-pages`.

#### Scenario: Missing permissions
- **WHEN** the `pages: write` permission is absent from the workflow
- **THEN** the deploy step SHALL fail — this is a known failure mode
  and SHALL be guarded against by the workflow as written

### Requirement: Build SHALL NOT fail on partial fetch failure
The workflow SHALL treat a partial fetch failure (some queries
succeeded, some errored) as a successful build and SHALL proceed to
deploy the resulting page.

#### Scenario: One of two queries fails to fetch
- **WHEN** `python fetch.py` completes with one query errored and one
  query successfully rendered
- **THEN** the script SHALL exit 0
- **AND** the workflow SHALL proceed to upload and deploy the artifact
