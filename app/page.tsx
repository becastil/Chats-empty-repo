"use client";

import { useState } from "react";

const releaseVersion = "0.3.7";
const portableUrl =
  `https://github.com/becastil/Chats-empty-repo/releases/download/v${releaseVersion}/repo-scout-${releaseVersion}.pyz`;
const quickStart = `curl -fL ${portableUrl} -o /tmp/repo-scout.pyz
python3 /tmp/repo-scout.pyz --languages .`;

const snapshotText = `Repo Scout Snapshot
Root: /workspace/checkout
Git: main, clean
Docs: 5 present, 0 missing
Files: 13 scanned, 25,311 bytes
Policy: pass (4 rules)

Languages:
  Python: 6
  Markdown: 5
  TOML: 1
  Other: 1`;

const snapshotJson = `{
  "git": { "branch": "main", "dirty_files": 0 },
  "docs": { "present": 5, "missing": 0 },
  "policy": { "status": "pass", "rules_checked": 4 },
  "files": {
    "total": 13,
    "total_bytes": 25311,
    "by_language": {
      "Python": 6,
      "Markdown": 5,
      "TOML": 1,
      "Other": 1
    }
  }
}`;

const controls = [
  {
    flag: "--ignore",
    title: "Leave local noise out",
    copy: "Filter logs, build folders, or private notes without touching .gitignore.",
  },
  {
    flag: "--policy",
    title: "Enforce one team standard",
    copy: "Commit one TOML policy and run the same repository checks everywhere in CI.",
  },
  {
    flag: "--languages",
    title: "See the shape quickly",
    copy: "Add best-effort language totals while keeping raw extension counts intact.",
  },
];

const pilotRequestUrl =
  "https://github.com/becastil/Chats-empty-repo/issues/new?template=founding-team-pilot.yml";

const pilotBenefits = [
  "One shared TOML policy for up to 10 repositories",
  "Cross-repository rollout evidence with shared-policy verification",
  "CI rollout guidance for your existing workflow",
  "One custom policy pack for your repository standards",
  "Direct feedback access and priority fixes",
];

export default function Home() {
  const [format, setFormat] = useState<"text" | "json">("text");
  const [copied, setCopied] = useState(false);
  const output = format === "text" ? snapshotText : snapshotJson;

  async function copyCommand() {
    await navigator.clipboard?.writeText(quickStart);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1800);
  }

  return (
    <main>
      <a className="skip-link" href="#content">
        Skip to content
      </a>

      <header className="site-header">
        <a className="brand" href="#top" aria-label="Repo Scout home">
          <span className="brand-mark" aria-hidden="true">
            RS
          </span>
          <span>repo-scout</span>
        </a>
        <nav aria-label="Primary navigation">
          <a href="#snapshot">Snapshot</a>
          <a href="#team-pilot">Team pilot</a>
          <a className="nav-link-strong" href="https://github.com/becastil/Chats-empty-repo">
            Source <span aria-hidden="true">-&gt;</span>
          </a>
        </nav>
      </header>

      <div id="top" className="page-shell">
        <section className="hero" aria-labelledby="hero-title">
          <div className="hero-copy">
            <p className="eyebrow"><span className="eyebrow-dot" /> Local repository intelligence</p>
            <h1 id="hero-title">Repo Scout for every handoff.</h1>
            <p className="hero-lede">
              Repo Scout gives reviews, agents, and new teammates one compact page of context before anyone starts guessing.
            </p>
            <div className="hero-actions">
              <a className="button button-primary" href="#snapshot">Explore a snapshot <span aria-hidden="true">-&gt;</span></a>
              <button className="button button-secondary" type="button" onClick={copyCommand}>
                {copied ? "Copied" : "Copy no-install setup"}
              </button>
            </div>
            <p className="microcopy">One file. Python 3.11+. No API key.</p>
            <a className="pilot-inline-link" href="#team-pilot">
              Team policy pilot: $299 for 90 days <span aria-hidden="true">-&gt;</span>
            </a>
          </div>

          <div className="hero-panel" aria-label="Sample repository summary">
            <div className="panel-topline">
              <span><span className="status-dot" /> sample checkout</span>
              <span className="panel-branch">main / clean</span>
            </div>
            <div className="panel-heading">
              <p className="panel-kicker">Repository pulse</p>
              <h2>Small enough to read. Rich enough to act.</h2>
            </div>
            <div className="metric-grid">
              <div><strong>13</strong><span>files scanned</span></div>
              <div><strong>25.3<span className="metric-unit">KB</span></strong><span>total footprint</span></div>
              <div><strong>5<span className="metric-unit">/5</span></strong><span>project docs found</span></div>
            </div>
            <div className="composition" aria-label="File composition: six Python files, five Markdown files, one TOML file, one other file">
              <div className="composition-label"><span>File composition</span><span>13 total</span></div>
              <div className="composition-bar">
                <span className="bar-python" style={{ width: "46%" }} />
                <span className="bar-markdown" style={{ width: "38%" }} />
                <span className="bar-toml" style={{ width: "8%" }} />
                <span className="bar-other" style={{ width: "8%" }} />
              </div>
              <div className="legend"><span><i className="bar-python" />Python 6</span><span><i className="bar-markdown" />Markdown 5</span><span><i className="bar-toml" />TOML 1</span></div>
            </div>
          </div>
        </section>

        <section id="content" className="intro-band" aria-labelledby="intro-title">
          <p className="section-number">01 / The first useful page</p>
          <div>
            <h2 id="intro-title">Context without the ceremony.</h2>
            <p>Point Repo Scout at a checkout and get the facts that make the next decision easier: Git state, project docs, file mix, footprint, and the largest files worth opening first.</p>
          </div>
        </section>

        <section id="snapshot" className="snapshot-section" aria-labelledby="snapshot-title">
          <div className="section-heading-row">
            <div>
              <p className="section-number">02 / Snapshot lab</p>
              <h2 id="snapshot-title">One command. Two useful shapes.</h2>
            </div>
            <div className="format-switch" role="group" aria-label="Snapshot output format">
              <button className={format === "text" ? "active" : ""} type="button" onClick={() => setFormat("text")} aria-pressed={format === "text"}>Text</button>
              <button className={format === "json" ? "active" : ""} type="button" onClick={() => setFormat("json")} aria-pressed={format === "json"}>JSON</button>
            </div>
          </div>
          <div className="snapshot-layout">
            <div className="terminal" aria-live="polite">
              <div className="terminal-topline"><span className="terminal-dots" aria-hidden="true"><i /><i /><i /></span><span>repo-scout --languages .</span><span className="terminal-mode">{format}</span></div>
              <pre><code>{output}</code></pre>
            </div>
            <aside className="snapshot-aside">
              <p className="aside-label">Designed for the next move</p>
              <h3>Readable by people. Stable for scripts.</h3>
              <p>Human output gives a handoff its first page. JSON makes the same snapshot easy to pipe into review tooling or an agent workflow.</p>
              <a href="https://github.com/becastil/Chats-empty-repo/blob/main/README.md">Read the README <span aria-hidden="true">-&gt;</span></a>
            </aside>
          </div>
        </section>

        <section id="controls" className="controls-section" aria-labelledby="controls-title">
          <div className="section-heading-row controls-heading">
            <div>
              <p className="section-number">03 / Small controls, real leverage</p>
              <h2 id="controls-title">Keep the signal close.</h2>
            </div>
            <p className="section-side-note">The defaults stay boring. The useful edges are one flag away.</p>
          </div>
          <div className="control-grid">
            {controls.map((control) => (
              <article className="control-item" key={control.flag}>
                <span className="control-flag">{control.flag}</span>
                <h3>{control.title}</h3>
                <p>{control.copy}</p>
              </article>
            ))}
          </div>
        </section>

        <section id="team-pilot" className="pilot-section" aria-labelledby="pilot-title">
          <div className="pilot-copy">
            <p className="section-number">04 / Founding team pilot</p>
            <h2 id="pilot-title">Prove one policy across every repository.</h2>
            <p className="pilot-lede">
              For software teams using coding agents across multiple repositories,
              Repo Scout turns local standards into comparable CI evidence, then
              verifies whether every rollout bundle enforced the same policy,
              without uploading source code.
            </p>

            <div className="rollout-proof" aria-label="Example cross-repository policy rollout">
              <div className="rollout-proof-heading">
                <code>repo-scout-rollout</code>
                <span><i aria-hidden="true" /> shared policy / verified</span>
              </div>
              <div className="rollout-metrics" aria-label="Rollout evidence coverage">
                <div><strong>3</strong><span>repositories</span></div>
                <div><strong>3 / 3</strong><span>policy fingerprints</span></div>
                <div><strong>3 / 3</strong><span>commits recorded</span></div>
              </div>
              <ul className="rollout-repositories">
                <li><code>platform/api</code><span>ready for CI</span></li>
                <li><code>platform/web</code><span>ready for CI</span></li>
                <li className="needs-action"><code>platform/worker</code><span>remediation required</span></li>
              </ul>
              <p className="rollout-caveat">
                Bundle-reported evidence identifies the scanned revisions; pilot
                support adds the operating process for reviewing freshness and fixes.
              </p>
              <code className="rollout-command">repo-scout-rollout api.md web.md worker.md</code>
            </div>
          </div>

          <aside className="pilot-offer" aria-labelledby="pilot-offer-title">
            <p className="pilot-kicker">Founding team pilot</p>
            <div className="pilot-price">
              <strong><sup>$</sup>299</strong>
              <span>one time<br />90 days</span>
            </div>
            <h3 id="pilot-offer-title">Standardize up to 10 repositories.</h3>
            <ol className="pilot-benefits">
              {pilotBenefits.map((benefit) => <li key={benefit}>{benefit}</li>)}
            </ol>
            <a className="button button-pilot" href={pilotRequestUrl}>
              Apply for the $299 pilot <span aria-hidden="true">-&gt;</span>
            </a>
            <a className="pilot-details" href="https://github.com/becastil/Chats-empty-repo/blob/main/BUSINESS_MODEL.md">
              Read the complete pilot terms
            </a>
            <p className="pilot-note">Seeking three founding teams before billing or license enforcement is built. Requests are public; never include source code or sensitive details.</p>
          </aside>
        </section>

        <section className="closing-band" aria-labelledby="closing-title">
          <div>
            <p className="eyebrow"><span className="eyebrow-dot" /> Ready for the next checkout</p>
            <h2 id="closing-title">Start free. Standardize when the team is ready.</h2>
          </div>
          <div className="install-block">
            <span>portable quick start</span>
            <code>{quickStart}</code>
            <div className="install-actions">
              <button type="button" onClick={copyCommand}>{copied ? "Copied" : "Copy setup"}</button>
              <a href={portableUrl}>Download v{releaseVersion}</a>
            </div>
          </div>
        </section>
      </div>

      <footer className="site-footer">
        <span>repo-scout / local context, made legible</span>
        <span>MIT / open source</span>
      </footer>
    </main>
  );
}
