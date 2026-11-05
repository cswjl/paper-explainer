# Writing guide for explainers

Read this once before writing, and come back to the relevant section while writing. This file and the template are the reference; don't browse finished explainers for style. Open one only to settle a specific layout question, and where it disagrees with this file, this file wins.

The examples below are in English. §13 gives the Chinese form of every naming convention, and the typesetting rules of each language.

## Contents

1. Reader, tone and concision
2. Recommended structure
3. Section 1: the whole paper without formulas
4. Terms and preliminaries
5. Theorems, definitions and "in plain words"
6. Toy examples
7. Part II: proofs and details
8. Experiments
9. Figures
10. All results at a glance
11. Appendices: version differences, errata, references
12. Discussion: related work, assessment and follow-up work
13. Language conventions
14. Common LaTeX problems

---

## 1. Reader, tone and concision

**Who the reader is.** The reader has a CS undergraduate background (the exact scope is in SKILL.md, "What the reader knows"), hasn't read the paper and won't. So the explainer never sends the reader back to the paper with "see the paper" or "details in the original": whatever the paper has, the explainer has.

**Tone.** Like explaining a paper to a knowledgeable classmate: direct, concrete, short sentences. When motivation is needed, first say in one sentence why the thing is needed, then what it is. Don't write "obviously", "it is easy to see" or "it is not hard to prove": if something really is obvious, don't say it; if it isn't, write it out.

**Say everything once.** Explainers get long mainly because the same conclusion is said many times. The division of labour:

| Where | What goes there | What doesn't |
|---|---|---|
| Section 1 | The whole story in words: problem, gap, idea, results, experiments, limitations | Derivations |
| Start of a section | One sentence on where the section fits, when that isn't obvious | "This section covers …" openers; motivation already given in Section 1 |
| Theorem box | The exact statement | Explanation |
| Plain words | One sentence: what the result means | Reading out the conditions and conclusion one by one |
| Text after a box | What the box lacks and understanding needs: why a non-obvious condition is needed (what breaks without it), the typical size of key quantities, relations to other results | Restating the box; if none of these applies, nothing |
| Explainer's note | A substantive addition the paper doesn't make, helping understanding or assessment; usually at most one per section | The text again in other words |
| At-a-glance section | Tables | New content |

Never write:

- End-of-section summaries, or transitions and restatements such as "to summarize", "in other words", "that is to say", "it is worth noting that" (Chinese: 总结一下, 换句话说, 也就是说, 值得注意的是).
- Empty praise, such as "this is a beautiful result".
- Remarks about the explainer itself, such as "only the parts relevant here are covered".
- Explanations of standard derivation steps: algebra, differentiation, swapping sums, Jensen, Cauchy–Schwarz and union bounds are written directly; at most, name the inequality used.

After finishing a section, ask of each sentence: if I delete it, what does the reader lose? If nothing, delete it.

**"I" and "the authors".** "I" is the explainer, "the authors" are the paper's authors; keep this consistent throughout (Chinese: 我 and 作者, never 笔者). Mark my own inferences, additions and assessments explicitly, with "this is my inference" or by putting them in an explainer's note, so they don't mix with the paper's content.

## 2. Recommended structure

The file names in both outlines are examples; number them by the actual sections. Part titles come from the template.

### Theory papers

```
00_front          cover, info table, reading guide, table of contents
Part I: Understanding the paper
01_plain          the whole paper without formulas (one to two pages)
02_prelim         preliminaries: tools the paper uses that undergraduate courses don't teach (omit if none)
03_setup          problem setup (paper §2 or the start of §3); notation introduced as it comes
04_… 07_…         one section per main result, in the order of the argument
08_experiments    experiments
09_discussion     discussion: related work, the authors' conclusions and limitations, my assessment, follow-up work
10_overview       all results at a glance
Part II: Complete proofs (skip on first reading)
11_… 13_…         long derivations from the main text (if any), then one section per paper appendix, in order
Part III: Appendices
14_appendix       E1 version differences, E2 errors and consistency checks, E3 the paper's references and their roles
```

### Experiment-driven papers (methods, systems, benchmarks)

```
00_front          as above; rewrite "Two ways to read" and "What the boxes mean" as in SKILL.md step 4
Part I: Understanding the paper
01_plain          the whole paper without formulas
02_prelim         preliminaries: techniques the paper takes for granted that undergraduate courses don't teach
                  (e.g. DPO, the noising process of diffusion models); omit if none
03_method         problem setup and method overview, with an overall pipeline diagram
04_… 05_…         the method's parts, one key design per section; key formulas and algorithms in thmbox;
                  long derivations only sketched
06_experiments    main experiments: every table fully retyped, every figure handled as in §9
07_analysis       ablations and analysis
08_discussion     discussion
09_overview       all results at a glance
Part II: Full details (skip on first reading)
10_derivations    every derivation in full: the long ones from the main text and those in the paper's appendices
11_details        full hyperparameter tables, training and evaluation details, extra experiments
Part III: Appendices
12_appendix       E1, E2, E3
```

### Notes

- **No separate background section.** Motivation and contributions from the paper's introduction go in Section 1. Prior work needed to understand the method, such as the method this paper improves, goes in the preliminaries or the setup.
- **Section titles** are in the explainer's own words, followed by the location in the paper, e.g. "Main theorem for population data (paper §3.3)", "Experiments (paper §6, Appendix A)". Readers use this to find their way in the paper later.
- **Sections follow the argument**, not necessarily the paper's sections. Split a long section of the paper; merge sections that discuss one thing. A result with only half a page of content joins a neighbouring one.
- **No per-section summaries.** Only when a section runs over four or five pages and its conclusions are scattered does it end with a `sumbox` of at most 3 points.
- **Relations to explainers already in the folder** go at the end of Section 1, one or two sentences per explainer. When a relation is very close (e.g. this paper exists to remove an assumption of that one), the discussion section may say more.

## 3. Section 1: the whole paper without formulas

Often this is the only section a reader reads, so it must stand alone: after reading it, the reader can retell the paper to someone else.

**Structure.** Use `\paragraph`, one idea per paragraph, usually one paragraph each (the template has these paragraphs):

1. **Problem**: what problem, told through a concrete scene, e.g. "a big pile of unlabelled photos".
2. **Gap in existing work**: where existing methods or theory fall short.
3. **Key idea**: in images and metaphors, e.g. "draw every possible augmented image as a point, and connect two points if they may come from the same original image".
4. **Main results**: in words. One or two key quantities may be named, saying what each is and how large it typically is, e.g. "$\alpha$ measures how well the classes are separated".
5. **Experiments**: what was seen, with the one or two most important numbers.
6. **Significance and limitations**.

If needed, add a last paragraph on the relation to existing explainers (§2).

**One to two pages.** Undergraduate knowledge is used without explanation; a concept beyond undergraduate level is set in bold the first time and explained in half a sentence.

**No derivations.** No display formulas and no derivations. Only two things are allowed:

- Naming a few key quantities inline.
- A "word formula": the terms written out in words, joined only by symbols such as $=$, $+$, $\times$, in a `center` environment. For example:
  `loss \ $=$ \ $-2\times$(average inner product of the representations of a positive pair)\ $+$ \ (average squared inner product of the representations of two random images)`

## 4. Terms and preliminaries

**Terms.** Terms taught in undergraduate courses are used directly. Any other term is set in bold the first time and explained in one sentence, e.g. `\textbf{linear probe}`. A Chinese explainer also gives the English original in parentheses the first time, `\textbf{线性探测}（linear probe）`, and uses the Chinese term afterwards; a term with no established Chinese translation gets my own translation plus the English the first time, and that translation afterwards.

**Preliminaries (`02_prelim`).** Only tools that the paper uses, that undergraduate courses don't teach, and that can't be explained in a sentence or two where they are used. Each tool gets a short paragraph:

1. One sentence of intuition: what it captures.
2. The definition, and the one or two properties this paper uses.
3. What this paper does with it.

Usually no worked example; only when the definition itself is counter-intuitive, add a two- or three-line example. When there are only one or two such tools, skip this section and explain each where it is first used.

**Notation.** No notation table up front. Notation is explained in the setup where it first appears; all symbols are collected in the notation table of the at-a-glance section. General notation such as $\E$, $\nabla$, $\log$, $O(\cdot)$ isn't explained; notation that is easy to misread is, e.g. what $\Otil$ hides, or how large a constant $\lesssim$ hides.

**When one symbol has two meanings** (common in papers), the explainer distinguishes them with different notation and explains this in a "reused notation" entry of E2.

## 5. Theorems, definitions and "in plain words"

Boxes and commands defined by the template (their labels follow the language switch):

| Environment or command | Use |
|---|---|
| `\begin{thmbox}{Theorem 3.8 (Main theorem: …)}` | the paper's theorems, lemmas, propositions, assumptions, algorithms and key formulas: the exact statement, numbered as in the paper |
| `\begin{defbox}{Definition 3.3 (…)}` | the paper's definitions |
| `\begin{notebox}` | explainer's note: explanation, connections or assessment beyond the paper, with real substance |
| `\begin{checkbox}[Toy example (1): …]` | my own examples and checks, every number from a script; only a few in the whole explainer |
| `\begin{sumbox}` | the reading guide; only a very long section ends with one listing its points |
| `\plainsay{…}` | after a theorem or proposition in Part I: one sentence on what it means |
| `\ptag{6}` | the paper's equation number, shown as "(paper 6)" (Chinese: "(原文 6)"); also creates the link target |
| `Eq.~\peq{6}` | cites a paper equation, shown as "Eq. (6)" (Chinese: `式~\peq{6}`, "式 (6)"); (6) links to where the explainer displays it |
| `\proofhead{Proof}` | heading of a proof |

Box colours show **where the content comes from**: blue and teal boxes are the paper's, orange and green boxes are the explainer's additions. The reading guide tells the reader this, so don't mix them up.

```latex
\begin{thmbox}{Theorem 3.8 (Main theorem: population pre-training data)}
Let the representation dimension be $k\ge2r$, and suppose Assumption 3.6 holds for some $\alpha>0$. … Then
\[
  \Err(\fpop)\le\Otil\Bigl(\alpha\big/\rho_{\lfloor k/2\rfloor}^2\Bigr).
\]
\end{thmbox}

\plainsay{If almost no edges connect different classes and each class is well connected inside, linear classification on the learned representation has low error.}
```

- **Box title**: "Theorem 3.8 (Main theorem: …)", numbered as in the paper, with a short name in parentheses. Definitions use `defbox`; assumptions, lemmas, propositions, claims, corollaries, algorithms and key formulas all use `thmbox`, because they are all the paper's content.
- **Inside the box**: an exact statement of the paper's result in the paper's notation (in a Chinese explainer, an exact Chinese rendering). A typo is corrected inside the box; one sentence after the box says so and points to its E2 entry.
- **Plain words**:
  - When: after every theorem and proposition in Part I; after lemmas, corollaries, assumptions, algorithms and formula boxes only when their meaning isn't plain; usually none in Part II.
  - How: one sentence, no new symbols, saying what the result means.
  - Don't translate the formula term by term. For the example above, "the error is at most $\alpha$ divided by the square of $\rho$, times log factors" just reads the formula aloud.
- **Text after the box**: only what the box lacks and understanding needs (see the table in §1). Three kinds are common: why a non-obvious condition is needed and what breaks without it; the typical size of key quantities; relations to the results before and after. If none applies, go straight to the next result.
- **The paper's numbered equations** are marked with `\ptag{N}`: `\[ … \ptag{6} \]` shows "(paper 6)" and creates the link target. In `align*` and `multline*` also use `\ptag{N}`; never write `\tag{paper N}` directly. Each of the paper's equations is displayed once. The explainer's own equations are unnumbered, or numbered automatically with `\label`. Write the number exactly as the paper does, dots and letters included: `\ptag{3.2}`, `\ptag{A.1}`, `\ptag{12a}`.
- **Citing a paper equation** always uses a link, `Eq.~\peq{6}`, so one click jumps to the formula. Several in a row: `Eqs.~\peq{5}\peq{6}`; a range: `Eqs.~\peq{15}--\peq{22}`. Equation numbers in section titles and box titles are not linked. Quoting the paper's own wording (e.g. an erratum saying the paper writes "Eq. (11)" where (12) is meant) goes in quotation marks.

## 6. Toy examples

**Whether to use one.** Toy examples are optional. Only two situations justify one:

- A quantity in a result is abstract enough that it is hard to grasp without computing concrete numbers, e.g. when a bound says anything at all.
- The method's mechanism has a counter-intuitive side, e.g. a reward that is negative exactly when the answer is right.

When the method is a standard computational pipeline, a flow diagram works better than a toy example.

**How to choose one.** It fits in a few lines of matrices or one small picture, and still shows the phenomenon above. For example, for spectral contrastive learning (HaoChen et al., 2021), a "cat-and-dog graph" of 6 augmented images in two classes with no edges between them makes every eigenvalue computable by hand.

**How to use it.**

- Give the setup once, in the problem setup, in a box titled "Toy example (1): …" (Chinese: "小例子（一）：…").
- Afterwards use it only at the one or two most important results, at most 3 places in all. Each time, write only the newly computed quantities, in a few lines or a small table, without the computation.
- Standard tools such as KL divergence, softmax and policy gradients get no worked example.

**Where the numbers come from.** Every number is computed by a script, which also checks that the theorem's inequalities hold on the example. If a bound says nothing on the example (e.g. its right side exceeds 1), say so and explain why in one sentence; that itself helps the reader understand the bound.

## 7. Part II: proofs and details

- **Sections**: first the long derivations from the main text (if any), then one section per paper appendix, in order, titled like "Complete proof of the main theorem (paper Appendix B)". For experiment-driven papers this part also holds the full hyperparameter tables, training and evaluation details, and extra experiments.
- **Statements**:
  - Theorem and lemma numbers match the paper.
  - A result already stated in Part I gets only a title and a pointer here, e.g. "Proof of Theorem 3.8 (statement in Section~\ref{sec:main})", not a second copy.
  - A lemma that only appears in Part II is first stated in a `thmbox`, then proved.
  - Proofs begin with `\proofhead{Proof}` and end with `\qedsym`.
- **Fill in omitted steps**: only the non-trivial ones, i.e. steps where the reader would have to stop and think. Standard steps are written directly. In an inequality chain, mark the steps that need justification with `\overset{(a)}{\le}`, and give the reasons right after:

  ```latex
  \[
    \norm{U-\Fsc B\tp}_F^2 \overset{(a)}{\le} \sum_i \frac{\phi_i}{\lambda_{k+1}}
    \overset{(b)}{=} \frac{\phiy}{\lambda_{k+1}}.
  \]
  (a) Eq.~\peq{26} for each class; (b) each edge between two classes is counted once in each of them.
  ```

- **The paper's equations** are tagged with `\ptag{N}` and cited with `Eq.~\peq{N}` (§5). An equation already displayed in Part I is not displayed again; link to it.
- **Typos**: correct them in the proof, adding a sentence such as "The paper has … here; see E2, item N."
- **Checks**: the numerical checks of SKILL.md step 6 (suspected errors, the main theorems) are reported only when they support an erratum or cover an error-prone spot, one or two sentences each, e.g. "In twenty thousand random small examples the original inequality fails about half the time, with the ratio reaching exactly 2; the corrected one never fails."

## 8. Experiments

- **Algorithms**: write the pseudocode in a `thmbox` titled like "Algorithm 1 (training)", each line matching a formula in the paper. No `\plainsay` when the algorithm is plain.
- **Tables**: every table in the paper is retyped in full, every number copied exactly, without rounding. Mark the source with `\caption*{Paper Table 1: …}` (Chinese: `\caption*{原文表 1：……}`) so it doesn't take one of the explainer's table numbers. After retyping, check it against the paper with `compare_numbers.py`.
- **Figures**: see §9.
- **Hyperparameters and training details**: optimizer, learning rate, batch size, epochs, data augmentation and hardware.
  - Theory papers usually have few experiments: list everything in the experiments section.
  - Experiment-driven papers: the experiments section lists only the settings needed to understand the results; the full hyperparameter tables go in Part II.
- **Code**: if the authors released code, give the repository URL. Where the implementation differs from the paper's formulas (e.g. the loss actually has an extra factor), point it out and record it in E2.
- **Interpretation**: after each table, one or two sentences on which of the paper's claims it supports. When a claim needs a discount, e.g. only one dataset, or a gain smaller than run-to-run noise, add a sentence saying so.

## 9. Figures

### The paper's figures: use the originals

The reader sees the paper's own figure: the most reliable choice, with no redrawing.

**Getting them**, in this order (`<skill>`, `<explainer>` and `<tmp>` are the path conventions at the start of "Workflow" in SKILL.md):

1. **Image files in the source.** `python -P "<skill>/scripts/figures.py" source <source dir>` lists each figure's caption and image files in LaTeX's numbering: entry N is the paper's Figure N. Copy PDF, PNG and JPG files straight into `figures/`, named `paper-fig<N>.<ext>`; a figure made of several files gets a letter per subfigure, e.g. `paper-fig1a.png`, `paper-fig1b.png`.
2. **Crop from the paper's PDF.** When the source has no image file (the figure is drawn with LaTeX code), only EPS files, or there is no source:

   ```
   python -P "<skill>/scripts/figures.py" crop <paper PDF> --figure N --out "<explainer>/figures/paper-figN.png"
   ```

   The script finds the figure's region and writes a 300 dpi PNG. If it picks the wrong region, look at the pages with the boxes drawn using `python -P "<skill>/scripts/figures.py" list <paper PDF> --preview "<tmp>/preview"`, then give the region with `--page P --rect x0,y0,x1,y1`.

**Inserting.** The caption uses `\caption*`, "Paper Figure N: explanation" (Chinese: "原文图 N：中文说明"), like the paper's tables, so it doesn't take one of the explainer's figure numbers:

```latex
\begin{figure}[htbp]
  \centering
  \includegraphics[width=\linewidth]{paper-fig1}
  \caption*{Paper Figure 1: the augmentation graph (left) and the features from its spectral decomposition (right).}
\end{figure}
```

Choose the width by the original's size, `\linewidth`, `0.7\linewidth` and so on; don't blow up small figures.

**Explaining.** The text says in one or two sentences what the figure shows and where to look, e.g. "the curves rise with k but barely move beyond k=10". In a Chinese explainer, the figure's labels are in English, so the caption gives Chinese for the English terms in the legend. Subfigures and axes aren't described one by one unless the figure can't be read without it.

**Checking.** After cropping, open the PNG with Read: axis labels, legends and subfigure titles are not cut off, and no body text or running header got in. After compiling, check its size and sharpness again in the rendered pages.

**When to draw another one.** Only when the original isn't enough: e.g. a simplified version is needed, labels in the explainer's language are needed (Chinese), or the toy example should be shown as a picture. Such a figure is drawn with TikZ and is the explainer's own, numbered as "Diagram N" (Chinese: "插图 N"); the original stays.

**Tables and algorithms are never cropped.** They are retyped as text, so table numbers can be checked with `compare_numbers.py` and algorithm lines matched to formulas.

### The explainer's own figures

- **Tools**: overview pipelines, result dependency graphs and toy examples are drawn with TikZ; data plots with pgfplots. Script-generated figures (e.g. matplotlib) are saved as PDF in `figures/`, and their scripts go in `checks/`.
- **Colours**: `ser1`–`ser6` from the template (checked for colour-blind separability), in order; line styles `serA`, `serB`, `serC`, … With two or more curves, include a legend and also label the curves directly.
- **Numbering**: the explainer's own figures are numbered; the paper's figures are referred to as "Paper Figure 1" (Chinese: "原文图 1").
- **Checking**: after compiling, render the pages and check each figure. Common problems and fixes:
  - overlapping text: move nodes, or anchor the labels (`anchor=north` etc.);
  - long labels: break them into two lines with `align=center` and `\\`;
  - crowded text in a box: a smaller font (`\scriptsize`) or a wider box;
  - a figure too wide: scale it (`scale=0.9, transform shape`) or rearrange it.

## 10. All results at a glance

Placed at the end of Part I, only for looking things up later: no new content, and no explanation beyond one introductory sentence.

**Theory papers:**

1. **Results table** (longtable): result number | content (conditions and conclusion, in corrected form) | meaning (one sentence; the plain-words line can be reused).
2. **Relations between results**: when there are many results (6 or more) and the dependencies aren't simple, a TikZ dependency graph with arrows from the lemma used to the theorem using it, Part I and Part II results separated by a dashed line. Omit it when there are few results.
3. **Notation**: symbol | meaning and where it first appears.

**Experiment-driven papers:**

1. **Method components**: component | role | corresponding formula or algorithm | where in the explainer.
2. **Notation**.

## 11. Appendices: version differences, errata, references

The explainer's own appendices are numbered E1, E2, E3 (Chinese: 附 1, 附 2, 附 3), so they aren't confused with the paper's Appendices A, B, C; the template's `appendix.tex` already does this.

**E1 Version differences.** E1 compares exactly two versions: the latest preprint version, on which the explainer is based, and the formal version. Older preprint versions are not compared. Open with one sentence naming the two, with the date of the preprint version, the venue of the formal one, and where the formal version and its supplement came from. Then a three-column table: item | latest preprint | formal version. Only substantive differences:

- theorem numbers and conditions
- experimental data
- sections, appendices and experiments added or removed
- references added or removed

When there is no formal version, when it can't be obtained, or when the two differ only in layout and wording, drop the table and say so in a sentence or two.

**E2 Errors and consistency checks.** Open with two or three sentences on:

- whether these problems shake the main conclusions;
- the category of each entry: conditions or constants, missing steps, substantive gaps, wording and notation;
- the fact that the entries were independently reviewed.

Then a three-column table: no. | location | problem. The "problem" column gives the problem, the correction and how it was verified, and ends with the scope of the impact (e.g. "affects constants only"). Keep it compact, without reasoning. Order the entries by severity: first those affecting a theorem's conditions or constants, then gaps in proofs, then typos and notation.

After the table, a paragraph "Parts checked and found correct" lists the main results verified by script with no problem found, so the reader knows what was checked.

When nothing was found, drop the table and keep only the opening and "Parts checked and found correct", saying what was checked.

**E3 The paper's references and their roles.** Every reference of the version used must appear. A two-column table: reference | role in the paper. To keep it from filling pages, there are two forms:

- References whose results, methods, data or code the paper actually uses: one row each, in the paper's reference order. The role is specific, "provides the higher-order Cheeger inequality (Lemma B.4)", not "related work".
- References only listed in batches in the introduction or related work: grouped by role at the end of the table, one row per group, e.g. "empirical contrastive learning methods: Chen et al.\ 2020a; He et al.\ 2020; Grill et al.\ 2020". A rule and a bold heading row spanning both columns separate them from the rows above; the template's table already has both:

  ```latex
  \midrule
  \multicolumn{2}{@{}l@{}}{\textbf{Cited only in batches in the introduction or related work, grouped by role}} \\
  ```

  (Chinese heading: 只在引言和相关工作里成批列举的文献，按作用分组.) If the paper has no such references, delete the rule and the heading.

References in the version used but not in the formal version are marked, e.g. "(new in v7)" (Chinese: "（v7 新增）").

## 12. Discussion: related work, assessment and follow-up work

This section comes after the experiments: only once readers know what the paper did can they see how it differs from other work. Usually one to two pages.

**Related work.** Summarize along the paper's own lines of related work, one or two sentences per line: what that line does, and how this paper differs. The role of each individual reference is given only in E3, not listed here.

**How the authors see their work.** One paragraph: the conclusion section, the limitations the authors state, and any broader-impact statement (often in the NeurIPS checklist or the supplementary material).

**My assessment.** Two or three strengths and two or three limitations, each with a one-sentence reason. Distinguish "problems the paper doesn't address" from "things the paper gets wrong"; write the latter only when E2 supports it.

**Follow-up work.** At most the 5 most relevant papers, as a table: paper | venue and year | relation to this paper. Each must first be verified to exist on arXiv, Semantic Scholar or the venue's site, with title, authors and year matching; better none than a wrong one. If none can be verified, omit this subsection.

## 13. Language conventions

### Names you write

The template's fixed labels follow its language switch. The names below are what you write yourself, and `check_tex.py` and `coverage.py` rely on them, so keep them exactly:

| Item | English explainer | Chinese explainer |
|---|---|---|
| Theorem-like box title | Theorem 3.8 (Main theorem: …) | 定理 3.8（主定理：…） |
| Other result names | Definition, Assumption, Lemma, Proposition, Corollary, Claim, Algorithm | 定义、假设、引理、命题、推论、断言、算法 |
| Toy example box | Toy example (1): … | 小例子（一）：… |
| Citing a paper equation | `Eq.~\peq{6}`, `Eqs.~\peq{5}\peq{6}` | `式~\peq{6}` |
| The paper's figures and tables | Paper Figure 3, Paper Table 2 | 原文图 3、原文表 2 |
| The explainer's own figures | Diagram 1 (numbered by LaTeX) | 插图 1 |
| The explainer's appendices | E1, E2, E3 | 附 1、附 2、附 3 |
| Location in the paper, in titles | (paper §3.3) | （原文 §3.3） |
| Marking an inference | "this is my inference" | “这是我的推断” |
| Explainer PDF | `HaoChen2021_SpectralContrastiveLoss_explainer.pdf` | `HaoChen2021_谱对比损失_讲解.pdf` |

### Chinese typesetting

- **Punctuation**: Chinese sentences use full-width punctuation: ，。：；？！（）“”. No half-width commas, full stops, colons or parentheses inside Chinese text. English phrases and formulas use half-width punctuation as usual.
- **English names**: English personal names, paper titles and venue names stay in English; authors get their affiliation in parentheses the first time.
- **Spacing**: xeCJK handles the space between Chinese and inline math or English automatically. Whether the source has spaces there doesn't matter, but be consistent within one explainer.

### English typesetting

- **Quotes and dashes**: ``…'' for quotations, `--` for ranges, `---` for dashes.
- **Spaces after abbreviations**: after a full stop that doesn't end a sentence (et al., e.g., i.e., Eq.), write `\ ` or `~`, e.g. `et al.\ (2021)`, `Eq.~\peq{7}`, `Section~\ref{…}`.
- **Spelling**: one variety of English (American or British) per explainer.

### Both languages

- **Dates**: YYYY-MM-DD, e.g. 2026-11-03.
- **Cross-references**: as in the template, e.g. `Section~\ref{sec:tools}` (Chinese: `第~\ref{sec:tools} 节`); the explainer's own equations as `Eq.~(\ref{eq:x})` (Chinese: `式~(\ref{eq:x})`); the paper's equations as in §5. All of these become links.
- **Numbers**: copied with the paper's precision, without rounding. Numbers I computed get 2 to 3 significant digits; use fractions or radicals where an exact comparison matters.
- **Lists**: items that are full sentences end with a full stop.

## 14. Common LaTeX problems

When `build.py` or the rendered pages show a problem:

- **Overfull lines**: split long formulas with `align*`, `split` or `multline`; turn an over-long inline formula into a displayed one.
- **Content off the page**:
  - A float taller than the page: make the figure narrower, or limit its height with `height=0.85\textheight,keepaspectratio`; turn a long table into a `longtable`.
  - Content running off the bottom: usually something unbreakable is too tall, such as a `minipage`, a `\parbox` or a very long formula; split it. The template's five boxes can all break across pages.
- **Formulas in headings**: use `\texorpdfstring{$k$}{k}` in section titles with math, otherwise the formula is dropped or garbled in the PDF bookmarks.
- **Missing glyphs**: Fandol lacks a few rare Chinese characters; rephrase, or use another character. A math symbol typed as a Unicode character should be written as a LaTeX command instead.
- **Page breaks**: the template doesn't force a page break after the table of contents or between parts; don't add `\clearpage` back, or each one leaves most of a page blank.
- **A heading stranded at the bottom of a page, or a box split leaving one or two lines**: put `\Needspace{N\baselineskip}` before the heading or box (N being the height of the heading plus the next few lines). Use the capitalized `\Needspace`: lowercase `\needspace` often breaks the page too early in this template, leaving big gaps.
- **Several small tables side by side** (e.g. hyperparameter tables): don't put them in `table` floats, which often get pushed to a page of their own; several floats in one subsection can even swap order. Use a `center` environment with `\captionof*{table}{Paper Table N: …}`. The main results tables use floats as usual.
