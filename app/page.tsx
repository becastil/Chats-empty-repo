"use client";

import { useState } from "react";

const snapshotText = `Repo Scout Snapshot
Root: /workspace/checkout
Git: main, clean
Docs: 5 present, 0 missing
Files: 13 scanned, 25,311 bytes

Languages:
  Python: 6
  Markdown: 5
  TOML: 1
  Other: 1`;

const snapshotJson = `{
  "git": { "branch": "main", "dirty_files": 0 },
  "docs": { "present": 5, "missing": 0 },
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
    flag: "--max-files",
    title: "Bound the scan",
    copy: "Set a clear file-count limit before a large checkout becomes a surprise.",
  },
  {
    flag: "--languages",
    title: "See the shape quickly",
    copy: "Add best-effort language totals while keeping raw extension counts intact.",
  },
];

export default function Home() {
  const [format, setFormat] = useState<"text" | "json">("text");
  const [copied, setCopied] = useState(false);
  const output = format === "text" ? snapshotText : snapshotJson;

  async function copyCommand() {
    await navigator.clipboard?.writeText("python3 -m repo_scout --languages .");
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
          <a href="#controls">Controls</a>
          <a className="nav-link-strong" href="https://github.com/becastil/Chats-empty-repo">
            Source <span aria-hidden="true">-&gt;</span>
          </a>
        </nav>
      </header>

      <div id="top" className="page-shell">
        <section className="hero" aria-labelledby="hero-title">
          <div className="hero-copy">
            <p className="eyebrow"><span className="eyebrow-dot" /> Local repository intelligence</p>
            <h1 id="hero-title">Start every handoff with the shape of the repo.</h1>
            <p className="hero-lede">
              Repo Scout gives reviews, agents, and new teammates one compact page of context before anyone starts guessing.
            </p>
            <div className="hero-actions">
              <a className="button button-primary" href="#snapshot">Explore a snapshot <span aria-hidden="true">-&gt;</span></a>
              <button className="button button-secondary" type="button" onClick={copyCommand}>
                {copied ? "Copied" : "Copy quick start"}
              </button>
            </div>
            <p className="microcopy">Dependency-free. Runs locally. No API key.</p>
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

        <section className="closing-band" aria-labelledby="closing-title">
          <div>
            <p className="eyebrow"><span className="eyebrow-dot" /> Ready for the next checkout</p>
            <h2 id="closing-title">Make orientation part of the workflow.</h2>
          </div>
          <div className="install-block">
            <span>quick start</span>
            <code>PYTHONPATH=src python3 -m repo_scout --languages .</code>
            <button type="button" onClick={copyCommand}>{copied ? "Copied" : "Copy command"}</button>
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
