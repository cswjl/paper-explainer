---
name: paper-explainer
description: Turns an academic paper into a complete, concise explainer PDF (typeset with XeLaTeX) written in the user's language, Chinese or English, saved with the original paper in a new subfolder "<year> - <acronym> - <English title>" of the user's explainer folder. A reader with a CS undergraduate background can master every theorem, proof and experimental number without opening the paper. Use it whenever the user wants a paper explained or fully understood, e.g. "explain this paper", "walk me through this paper", "讲解一下……", "讲讲这篇论文", "论文讲解", "精读/解读这篇论文", "帮我读懂/详解这篇 paper", or gives a paper title, arXiv link or PDF and wants to understand it thoroughly, even without mentioning PDF, LaTeX or folders. Not for one or two specific questions about a paper, a one-sentence summary, writing a review, or making group-meeting slides.
compatibility: Needs TeX Live (xelatex, with the bundled Fandol fonts for Chinese) and Python 3 with PyMuPDF and Pillow.
---

# Paper explainer: a LaTeX explainer PDF

The reader has a CS undergraduate background, hasn't read the paper and doesn't intend to. The explainer must do three things at once:

- **Complete**: whatever the paper has, the explainer has (see "What complete means" below), so the reader never needs to open the paper.
- **Concise**: say everything once; use undergraduate knowledge without explaining it; give examples only in the one or two places where concrete numbers help most.
- **Clear**: give the intuition in one sentence first, then the exact statement; explain terms and tools that undergraduate courses don't teach where they are first used.

Earlier explainers were too long: a 17-page paper became more than 60 pages. The main cause was repetition: the same conclusion was said in Section 1, the background, the start of its section, the theorem box, the plain-words line, an explainer's note, a toy example, a summary and the conclusion. Another cause was explaining undergraduate knowledge, such as expectations and gradients, with worked examples. Concision means cutting that repetition and those needless explanations, never the paper's content.

The explainer has three parts:

- Part I: one or two pages telling the whole paper without formulas, then the exact statement, meaning and experiments of every result, in the order of the argument.
- Part II: every proof and long derivation, filling in the non-trivial steps the paper omits; for experiment-driven papers, also every experimental detail.
- Appendices E1–E3 (附 1–3 in Chinese): version differences, errata, references.

**Length reference**: a paper of about 20 pages gives an explainer of about 30; a 50-page paper, about 60. This isn't a target, only a signal: clearly exceeding it usually means something is said more than once, or the reader is being taught what they already know.

This task is long; the context may be compacted midway, and the session may be interrupted. So the inventory (`inventory.md`), outline (`outline.md`), errata (`errata.md`) and checking scripts are written to files in the working directory `_work/` inside the explainer folder (see the path conventions at the start of "Workflow"), never kept only in the conversation.

## Language

Write the explainer, and talk to the user, in the language of the user's own words in the request, not the paper's (papers are almost always in English): a user writing Chinese gets a Chinese explainer, a user writing English an English one. An explicit request ("write it in English", "用中文写") wins. If the request has no words of its own (only a link or a file), use the language the user has been writing in during the conversation. The skill supports Chinese and English; if the user writes in another language, ask which of the two to use.

There is one template for both languages. The switch at the top of its `main.tex` (`\zhtrue` for Chinese, `\zhfalse` for English) sets the typesetting and every fixed label: box names, the plain-words label, equation tags, part titles, headers, appendix numbering and the reading guide. What you write yourself follows the naming conventions for that language in style guide §13, and the explainer PDF's name is in that language too. `check_tex.py` reads the switch to choose its language-specific checks.

## What the reader knows

The reader has the level of a CS graduate, including:

- Calculus.
- Linear algebra: matrix operations, eigenvalues and eigenvectors, norms, inner products, projections.
- Probability and statistics: expectation, variance, conditional probability, common distributions.
- Algorithms and complexity: big-O notation, basic graph concepts.
- Introductory machine learning: supervised learning, loss functions, gradient descent, cross-entropy, softmax, neural networks, overfitting.

These are used without explanation or examples.

What needs explaining is what undergraduate courses usually don't teach but the paper uses: information-theoretic concepts such as entropy, KL divergence and mutual information, as well as Rademacher complexity, PAC-Bayes bounds, the Cheeger inequality, policy gradients, or the noising process of diffusion models. When unsure whether to explain something, imagine a fresh CS graduate reading that spot: explain it only if they would get stuck.

## What complete means

Everything below that the paper has must be in the explainer:

- Every definition, assumption, theorem, lemma, proposition, corollary and claim, with its proof.
- Every algorithm and every numbered equation.
- Every number in every table.
- Every figure: the paper's figures go into the explainer as they are (image files copied from the source, otherwise cropped from the PDF), each with one or two sentences on what it shows.
- All experimental settings and hyperparameters.
- The role of every reference in the paper.

Complete doesn't mean translated, nor expanded: the content may be reorganized and stated more compactly, but nothing may be left out.

## Deliverables

All explainers live in one explainer folder, `<root>`, each in a subfolder of its own, whatever the current working directory. Keeping them together is what lets the skill find related and unfinished explainers. `<root>` is, in this order of precedence:

1. a folder the user names, in the request or in their standing instructions (CLAUDE.md, memory);
2. the environment variable `PAPER_EXPLAINER_DIR` (read it with `echo "$PAPER_EXPLAINER_DIR"` in Bash, or `$env:PAPER_EXPLAINER_DIR` in PowerShell);
3. otherwise a folder on the user's desktop: `论文讲解` for a Chinese explainer, `paper-explainers` for an English one. If only one of the two exists, it is used for both languages, so that all explainers stay together; if both exist, use the one matching the language, and look in both before starting. The desktop is `[Environment]::GetFolderPath('Desktop')` in PowerShell, `xdg-user-dir DESKTOP` where that command exists, and `~/Desktop` otherwise; without a desktop folder, use the home directory.

- If a folder from 1 or 2 doesn't exist (a typo, or another computer), ask the user where to put the explainer; don't create it.
- A default folder from 3 is created when missing. Say in the report where it is, and that setting `PAPER_EXPLAINER_DIR` moves it.
- If the session's working directory doesn't contain `<root>`, first ask for access to it (in the desktop app, with `request_directory`).

Before starting, look at the explainers already in `<root>`:

- If the same paper already has a folder (judged by arXiv ID or title):
  - If it still contains `_work/`, the last run didn't finish. Read the section states in `_work/outline.md` and `_work/errata.md`, continue where it stopped, and tell the user you are continuing the earlier run.
  - If it is finished, ask the user whether to update it (e.g. the paper has a new version) or redo it; don't create a second folder.
- If the new paper relates to an existing explainer (e.g. it exists to remove an assumption of the older paper), say so in a paragraph at the end of Section 1, one or two sentences per explainer (style guide §2). Judge relations by the folder names, and read only Section 1 of an explainer that is clearly related.

Subfolder layout:

```
<year> - <acronym> - <full English title>/
├── 2106.04156v7.pdf                    the paper (the version the explainer is based on)
├── HaoChen2021_SpectralContrastiveLoss_explainer.pdf   the explainer
├── main.tex
├── sections/*.tex
├── figures/                            the paper's figures (paper-fig1.pdf …) and my own
├── checks/                             scripts behind my checks, toy examples and data plots
└── _work/                              exists only while working; deleted before delivery
```

The three parts of the name are joined by " - ". Example: `2026 - G-OPD - Learning beyond Teacher - Generalized On-Policy Distillation with Reward Extrapolation`.

- **Year**: the year of formal publication (conference or journal), not the date of the explainer. For a preprint only, the year of arXiv v1.
- **Acronym**: the paper's own acronym for its method, keeping case and hyphens as they are, e.g. G-OPD, DeRa.
  - If the paper proposes several names, use the one promoted in the title or abstract. The example above uses the framework name G-OPD, not its special case ExOPD.
  - For a theory or analysis paper that proposes no new method, use the common acronym of its central object, e.g. W2S for weak-to-strong generalization.
  - If there is neither the paper's own acronym nor a common one, make one:
    - take a few key words of the method's name and form a short, recognizable acronym, e.g. SpeCL for spectral contrastive loss;
    - don't collide with a well-known acronym in the field, e.g. SCL usually means supervised contrastive learning;
    - say in the report that you made it up.
- **Title**: the full English title, keeping its capitalization. Replace each colon with " - " (a space on each side) and drop the other characters Windows file names can't contain (`? * " < > | / \`).
- **The paper's PDF**: the version the explainer is based on. From arXiv, name it `<id>v<version>.pdf`; otherwise keep the publisher's file name.
- **The explainer's PDF**: `<first author's surname><year>_<short name>_<suffix>.pdf`, with the first author taken from the formal version's author order. Short name and suffix are in the explainer's language: `HaoChen2021_SpectralContrastiveLoss_explainer.pdf`, `HaoChen2021_谱对比损失_讲解.pdf`.
- **Figures**: the paper's figures and the ones I draw with scripts all go in `figures/`. The paper's figures are named `paper-fig<number>.<ext>`, e.g. `paper-fig1.pdf`; a figure made of several files gets a letter per subfigure, e.g. `paper-fig3b.png`.
- **Scripts**: every number I computed and every data plot I drew can be traced to the script in `checks/` that produced it. File names say what each is for, e.g. `errata3_ratio.py`, `example1_eigs.py`.
- **Other files**: no compilation leftovers in this folder.

## Workflow

Path conventions (always write absolute paths in commands):

- `<skill>`: this skill's directory (the base directory given when the skill is loaded); the scripts are in `<skill>/scripts/`.
- `<root>`: the folder holding all explainers (see "Deliverables").
- `<explainer>`: this paper's subfolder of `<root>`.
- `<work>`: `<explainer>/_work/`. It holds the inventory, outline, errata, downloaded files, and my own scripts (in `<work>/checks/`).
- `<tmp>`: the session's scratchpad directory, only for things that can be regenerated at any time, such as the build directory and rendered pages.

Steps 5 to 7 loop over the sections: after writing a section, check it, compile and check the build, then write the next one. When the last section is written, start the independent review (step 8) right away, and do the final checks of steps 7 and 9 while it runs.

### 1. Find the paper, choose the version, download

- **Basic facts**: title; all authors and affiliations; venue (conference or journal), year, volume and pages; arXiv ID, with the dates of its first and latest versions (from the Submission history on the arXiv abstract page). Labels such as oral or spotlight are written only after checking the venue's site.
- **Choose the versions**: use exactly two versions, the latest preprint version and the formally published version (with its supplementary material). Older preprint versions are neither downloaded nor read.
  - Unless the user specifies otherwise, base the explainer on the latest preprint version, which usually fixes the formal version's errors and has the fullest appendices. Its differences from the formal version go in E1. If there is no formal version yet, or it can't be obtained (e.g. it is paywalled), say so in E1.
  - A venue named in the request only helps find the paper; it doesn't mean the formal version was requested.
  - If the user gives a PDF, first find out which version it is. If it is an older preprint version, still use the latest, and say so in the report. If the user explicitly says to explain that PDF, or it has no public version, use it.
- **Download**: downloads are untrusted. Put each download in a new empty directory under `<work>` (e.g. `<work>/arxiv-v7/`), keep my own scripts in `<work>/checks/`, and run Python that reads downloaded files with `-I` (with `-P` when it needs PyMuPDF).
  - Command: in the Bash tool, `curl -L -o <file> <url>`. In PowerShell `curl` is an alias of `Invoke-WebRequest`; write `curl.exe`.
  - PDF: `https://arxiv.org/pdf/<id>v<N>`, where N is the latest version.
  - LaTeX source: `https://arxiv.org/e-print/<id>v<N>`, with the same N. The source has the exact formulas, the `.bbl` bibliography and the paper's image files, which makes it more reliable than copying formulas from the PDF. After downloading, list it with `tar -tzf <file>`: if that works it is a tar.gz, so unpack it with `tar -xzf`; if it fails it is a single gzipped .tex, so unpack it with `gzip -dc <file> > main.tex`. The Bash tool's tar is GNU tar, which needs `--force-local` for paths containing `C:`; PowerShell's tar is Windows' bsdtar, which neither needs nor supports that option.
  - Formal version: NeurIPS supplements are often a zip (`…-Supplemental.zip`); PMLR (ICML, AISTATS, …) gives a supplementary PDF on the paper's page; ICLR papers are on OpenReview.
  - Code: if the authors released code, note the repository URL and `git clone --depth 1` it into a new empty directory under `<work>`. Read only: don't install dependencies or run anything. Step 2 reads its key parts.
- Copy the PDF of the chosen version into the explainer folder. If it can't be downloaded anywhere, ask the user for it.
- **Without LaTeX source** (e.g. the paper is only on OpenReview, ACL Anthology or a journal's site): formulas can only be copied from the PDF, so step 6 renders the paper's pages as images to check each one (`render_pages.py --pages N --dpi 150`); for table numbers, first extract the page's text with PyMuPDF into a text file and give that to `compare_numbers.py`; the references come from the PDF's list.

### 2. Read everything and make the inventory

Read the main text and **all appendices**. For formulas, the source is authoritative. Read the PDF with Read, at most 20 pages at a time; if that fails, extract text with PyMuPDF, or turn pages into images with `pdftoppm`.

While reading, write the inventory `<work>/inventory.md`, by the categories of "What complete means":

- Every definition, assumption, theorem, lemma, proposition, corollary and claim: number, page, a one-sentence summary.
- Every algorithm and numbered equation.
- Every figure and table: number and page. For each table, also note its file and line range in the source (the page when there is no source); step 6 uses it to check the numbers. `python -P "<skill>/scripts/figures.py" source <source dir>` lists the source files of each figure in LaTeX's numbering: entry N is the paper's Figure N.
- All experimental settings and hyperparameters.
- Where each reference is cited and what role it plays. `python -I "<skill>/scripts/bib_list.py" <source dir>` lists every reference in the `.bbl` with the sections citing it; with several `.bbl` files, pick one with `--bbl`.
- If the authors released code, read its key parts (loss, training loop, evaluation) and note where they differ from the paper's formulas.

The inventory is the basis of the final completeness check. The numbered items are checked mechanically by `coverage.py` (step 7); experimental settings, hyperparameters, the roles of references and whether every proof is complete are checked against the inventory in step 9.

### 3. Design the structure

Settle the table of contents before writing, and put the outline in `<work>/outline.md`. Style guide §2 gives two outlines: one for theory papers, one for experiment-driven papers.

While outlining, divide the work so nothing gets written twice: motivation, contributions and the storyline only in Section 1; each result developed only in its own section; the at-a-glance section holds only tables. Whether to use toy examples, and where, is also decided in the outline (style guide §6).

Give each section a state in the outline: not written, written, checked, compiled. Update it after every step; after a compaction, or in a new session, it shows where to continue.

### 4. Set up the skeleton

Copy `main.tex` and `sections/` from `<skill>/assets/template/` into the explainer folder, then:

1. Set the language switch at the top of `main.tex`: `\zhtrue` for a Chinese explainer, `\zhfalse` for an English one.
2. Fill in the per-paper macros below it (`\PaperTitle`, `\ExplainerTitle`, `\PaperVersion`, …).
3. Add the paper's own notation macros.
4. Number `overview.tex` and `appendix.tex` in their final order, e.g. `10_overview.tex`, `14_appendix.tex`, and update the `\input` lines in `main.tex`.
5. For an experiment-driven paper: switch Part II in `main.tex` to the "full details" title and intro (provided there as comments), and rewrite "Two ways to read" and "What the boxes mean" in the reading guide in `00_front.tex` to say that blue boxes hold the paper's key formulas, algorithms and propositions. The guide has both languages' text in `\zhen{Chinese}{English}`; editing the half in use is enough.

Every `\FILL{…}` placeholder must be replaced with real content in the explainer's language; `check_tex.py` finds those left. The template's five boxes and its commands (`\plainsay`, `\ptag`, `\peq`, …) are described in style guide §5. Labels fixed by the template already follow the switch; what you write yourself doesn't need `\zhen`.

### 5. Write section by section

Read `references/style-guide.md` once before writing, and come back to the relevant section while writing. These are the most common problems; the details are all in the style guide:

- **Say everything once**: the division of labour is in §1; no section openers, end-of-section summaries or "in other words" restatements.
- **Use your own words and follow the argument**; don't retell the paper sentence by sentence. The mathematics in boxes must match the paper, apart from typos listed in the errata (§5).
- **Explain only what the reader doesn't know**: undergraduate knowledge is used directly; anything beyond it is explained where it is first used (§4).
- **No derivations in Section 1**: one or two pages telling the whole paper (§3).
- **Complete**: write everything listed in "What complete means". Long proofs and derivations always go to Part II, wherever the paper put them; Part I gives only the idea and key steps (§7).
- **The paper's equations** are displayed with `\ptag` and cited with `\peq` (§5); **the paper's figures** are used as they are (§9).
- **My own inferences and assessments** are marked as such and kept apart from the paper's content (§1, §12).

After each section:

1. Check it (step 6).
2. Compile and check (step 7) in one command, which costs a single round trip (`;` works in both Bash and PowerShell, and runs the check even when the build reports problems):

   ```
   python "<skill>/scripts/build.py" "<explainer>" --build-dir "<tmp>/build" --runs 2; python "<skill>/scripts/check_tex.py" "<explainer>"
   ```

   Fix what they report right away instead of letting it pile up.
3. Update the section's state in `outline.md`.

### 6. Verify and look for errors

- **Numbers come from scripts**: every number in an example or a check box comes from a script that was actually run (numpy, fractions, sympy). Scripts go in `<work>/checks/` and stay with the explainer at delivery. Mental arithmetic slips, and a reader who finds one wrong number stops trusting the whole explainer.
- **What gets a script, and what doesn't**: write scripts for the numbers shown in examples and check boxes, for every suspected error before it goes into E2, and for the central inequality or identity of each main theorem on a few random small instances. Routine steps (algebra, standard inequalities, results the paper only cites) are checked by reading, not by script. The text reports only the checks that support an erratum or a counter-intuitive conclusion, one or two sentences each.
- **Table numbers are checked by script too**: `python -I "<skill>/scripts/compare_numbers.py" <paper source>:<start>-<end> <explainer source>:<start>-<end>` compares the numbers in two text spans in order and lists the mismatches. The paper side's line range is in the inventory; without source, use the page text extracted with PyMuPDF.
- **Check the paper's derivations step by step.** When something seems wrong, test it numerically on random small examples before concluding.
- **For experiment-driven papers**, also check three things: whether numbers quoted in the text match the tables (e.g. "improves by 3.2%"); whether the tables are internally consistent (averages, bold best results); whether the code matches the paper.
- **First try to rescue the statement**: when you find a problem, first see whether the paper's own tools can save the original statement, e.g. a different choice of parameters, or the general form of a cited result. **If "the proof is missing a step" is enough, don't say "the theorem needs stronger conditions".** Turning a step missing from a proof into a defect of the theorem itself is the most common mistake in this kind of explainer, and the most damaging to its credibility.
- If a proof relies on the exact form of an external result, check the original source.
- Record each problem in `<work>/errata.md` as you go. The text states the corrected form directly and points to the matching E2 entry. Each entry gives five things:
  - location
  - problem
  - correction
  - how it was verified (which script in `checks/`)
  - scope: affects constants only, notation only, conclusion unchanged, or conditions must change
- How to write E2 is in style guide §11. If nothing was found, E2 still stays, saying what was checked.

### 7. Compile and check the layout

```
python "<skill>/scripts/build.py" "<explainer>" --build-dir "<tmp>/build" --out "<explainer PDF name>"
```

`build.py` copies the sources to the build directory, compiles with XeLaTeX (3 runs by default) and reports the page count, overfull lines, content off the page, undefined references and links, duplicate labels, formulas in headings without `\texorpdfstring`, and missing glyphs; with `--out` it copies the PDF back into the explainer folder. The goal is zero of everything; with problems the exit status is 2, and the fixes are in style guide §14. While writing section by section, `--runs 2` without `--out` is enough; do a full build at the end.

If the page count clearly exceeds the length reference, first remove repetition and needless explanation following style guide §1, then rebuild.

```
python "<skill>/scripts/check_tex.py" "<explainer>"
```

`check_tex.py` checks the sources against the style guide and reports two kinds of results: "problems" must be fixed, e.g. a missing `\plainsay`, half-width punctuation in Chinese text, a paper equation cited without a link; "notes" are mostly about length, so judge for yourself.

```
python -P "<skill>/scripts/render_pages.py" "<explainer>/<explainer PDF>" "<tmp>/pages" --sheet 3x2
```

`render_pages.py` renders the pages into contact sheets; then **look at every sheet with Read**. Overlapping text in TikZ figures, labels on top of lines and cramped drawings don't show up in the log, only to the eye; several figures in earlier explainers were caught this way. Zoom into suspicious pages with `--pages 12-13 --dpi 150`.

To check the text in the PDF, use PyMuPDF: `pdftotext` can't extract the Chinese that XeLaTeX produces.

When everything is written (with the independent review of step 8 already running), check completeness against the paper:

```
python -P "<skill>/scripts/coverage.py" "<explainer>/<paper PDF>" "<explainer>"
```

`coverage.py` finds every definition, assumption, theorem, lemma, proposition, corollary, claim, algorithm, figure, table and numbered equation in the paper's PDF and lists those the explainer never mentions, plus `\ptag` numbers the paper doesn't have. It also lists numbers the paper only mentions in running text without stating them. Usually the paper is citing another work there, so look at each context; if not, it is a dangling reference in the paper and goes in E2.

### 8. Independent review

Calling something wrong that the paper got right is far worse than missing a typo, so the errata are the riskiest content of the whole explainer.

As soon as every section is written and E2 is settled, start a fresh subagent (Claude models only) and give it:

- the path of the paper (source or PDF);
- the path of the explainer's sources;
- the location, problem and correction of each E2 entry.

Don't give it "how it was verified" or your reasoning, so it doesn't follow your line of thought. Ask it to:

- judge each entry independently: is it really an error? Is there a weaker fix? Is the correction itself right?
- spot-check a few theorem boxes against the paper; for experiment-driven papers, spot-check key formulas, algorithms and tables;
- list passages that read as repetition, and passages that explain undergraduate knowledge, giving only the location and a one-sentence reason.

If E2 has no entries, the review only spot-checks and looks for repetition.

Don't wait for the review. The subagent runs in the background, so meanwhile do the final checks: the visual review of the rendered pages and `coverage.py` (step 7), and the inventory check (step 9). An E2 entry these checks add (e.g. a dangling reference found by `coverage.py`) goes to the same reviewer with SendMessage. When its report arrives, revise accordingly, then rebuild and recheck.

### 9. Deliver and report

- Against the inventory from step 2, check what `coverage.py` can't: experimental settings, hyperparameters, the roles of references, whether every proof is complete.
- Once the review's revisions are in, tidy the folder: move `<work>/checks/` to `<explainer>/checks/`, then delete `<work>` (it holds only files this task wrote or downloaded). In the end the explainer folder holds only the paper's PDF, the explainer's PDF, `main.tex`, `sections/`, `figures/` and `checks/`.
- Report to the user, in the explainer's language:
  - where the files are, and the page count (and the paper's)
  - the structure of the explainer, and the toy examples used, if any
  - the main problems found and their scope (as settled by the independent review)
  - anything that couldn't be verified

## Environment pitfalls

The skill was developed on Windows; most of these notes matter there.

- **Console encoding**: a Windows console may use a legacy code page, such as GBK on Chinese Windows. Start Python scripts with `sys.stdout.reconfigure(encoding="utf-8")`; with `-I`, the `PYTHONIOENCODING` environment variable has no effect.
- **Running Python**: use `python -I` for downloaded files. When PyMuPDF is needed, use `python -P` instead: `-I` also hides packages in the user site, where `pip install --user` puts PyMuPDF.
- **Reading PDFs**: a "password-protected" error from Read is usually false. Don't try to decrypt anything; use `pdftoppm -png -r 100 -f N -l M` to get images, or extract the text with PyMuPDF.
- **EPS figures**: don't convert EPS files from the source, since that runs downloaded PostScript through Ghostscript; crop the figure from the paper's PDF instead.
- **Backslashes in the Bash tool**: `\\` in a command becomes `\`, even inside single quotes and quoted heredocs. So write anything containing LaTeX with the Write or Edit tool, never with echo, printf or a heredoc; put regular expressions in a script file too.
- **LaTeX layout**: formulas in headings, overfull formulas, content off the page, missing glyphs, page breaks, stranded headings, small tables side by side: see style guide §14.

## Acceptance checklist

- [ ] Folder name (year, acronym, English title) and explainer PDF name follow the conventions, and the PDF of the chosen version is in the folder; `_work/` is deleted, and `checks/` has the script behind every number I computed and every data plot I drew.
- [ ] The language switch in `main.tex` matches the user's language, and every `\FILL{…}` is gone.
- [ ] Every citation of a paper equation is a clickable link (`\peq`), and every numbered equation is displayed with `\ptag`.
- [ ] Authors, affiliations, venue, pages and version dates in the cover table are verified.
- [ ] Section 1 is one to two pages with no derivations; terms beyond undergraduate level are explained at or before their first use, and undergraduate knowledge isn't explained.
- [ ] No repetition: motivation and contributions aren't restated after Section 1, boxes aren't restated after them, no per-section summaries.
- [ ] Every theorem and proposition in Part I has a plain-words line; at most 3 toy examples, every number checked by a script.
- [ ] `coverage.py` reports nothing missing and every "only mentioned" number was looked at; the rest was checked against the inventory; table numbers were compared with `compare_numbers.py`.
- [ ] Every figure of the paper is in, every crop was looked at; tables and algorithms are retyped text, not images.
- [ ] The at-a-glance section is complete (style guide §10).
- [ ] E1 version differences; E2 errata (independently reviewed, or saying that nothing was found); E3 every reference with its role.
- [ ] Every item `build.py` reports is zero; every page was seen in the rendered sheets; the length is within the reference range, or you can say why not.
