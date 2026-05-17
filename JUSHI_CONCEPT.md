# JuShi Concept Notes

## Working Definition

`JuShi` in this project means a sentence frame that became memorable through an
original utterance, scene, or event, and later gets reused by replacing some of its
slots while preserving audience recall of that source.

This is stronger than:

- generic grammar templates
- fixed expressions with no known origin
- ordinary rhetorical patterns that are reusable but not referential

A real `JuShi` is usually intertextual. It carries memory.

## Core Properties

A sentence should qualify as `JuShi` only when most of these are true:

1. There is an identifiable original or early canonical moment.
2. Later reuse keeps enough of the structure for recognition.
3. Replacements can affect nouns, verbs, places, people, or roles.
4. The reuse gains meaning from the listener recalling the earlier scene.
5. The sentence is quoted, parodied, drifted, or remixed across contexts.

## What The Current Repo Already Covers

The codebase already has useful infrastructure for this:

- raw-text ingestion
- template extraction with slots
- pattern examples
- tagging
- search and browse UI
- canonical / variant linking

This is a good foundation for a `JuShi` corpus.

## What Is Missing In The Code

The missing layer is explicit source-memory modeling.

The current schema does not store:

- the original event or scene behind a pattern
- the earliest or canonical quoted utterance
- a description of why the frame is culturally recognizable
- whether a pattern is just structurally common versus truly recall-inducing
- links between later examples and the origin they are invoking

Because of that, the app can answer:

- "what patterns exist?"
- "what examples match this template?"

But it cannot reliably answer:

- "what moment does this pattern point back to?"
- "which variant is the culturally canonical one?"
- "why does this reuse feel recognizable?"

## Recommended Product Direction

### 1. Add origin-level data

Add a first-class entity for the memorable source moment.

Suggested shape:

```text
source_moments
  id
  title
  description
  canonical_quote
  source_url
  happened_at
  platform
  recall_notes
```

Then link patterns to moments:

```text
sentence_patterns
  source_moment_id nullable FK
  recall_confidence
  is_intertextual
```

### 2. Separate syntax reuse from reference reuse

Not every reusable template is a `JuShi`.

The pipeline should eventually distinguish:

- generic pattern: reusable syntax only
- `JuShi`: reusable syntax plus recoverable cultural origin

That can start with a simple boolean plus reviewer notes, then become a scored model.

### 3. Upgrade pattern detail pages

Pattern detail pages should eventually show:

- canonical source moment
- earliest known usage
- notable drift variants
- example substitutions
- explanation of what people are recalling

### 4. Improve ranking

High-value `JuShi` candidates are usually patterns where:

- the sentence frame repeats across multiple texts
- slot values vary widely
- the surrounding discourse clusters around a recognizable event or meme
- users keep the structure while swapping named entities or roles

## Recommended Search Modes

The current search is template-first. Long term the product likely needs:

- template search: `感谢*让我*`
- recall search: search by the original quote or event
- variant search: show drifted versions of the same frame
- example search: find concrete reuses of a known `JuShi`

## Practical Next Steps

1. Keep the current template extraction pipeline.
2. Add nullable origin fields or a `source_moments` table.
3. Extend APIs so pattern detail can return origin metadata.
4. Add UI copy that explains `JuShi` as recall-inducing sentence structure, not just
   generic fixed expressions.
5. Add curation or admin workflows for attaching patterns to canonical source moments.

## Naming Note

The repository directory is still named `jushu/`.

That is acceptable for now. The low-risk change is to update user-facing naming and
documentation to `JuShi`, while leaving internal paths, package names, and database
identifiers unchanged until there is a deliberate migration plan.
