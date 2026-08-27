# MODAVIS competency questions and traceability

Status: normative requirements record for release `0.1.0`

MODAVIS competency questions have stable identifiers and executable SPARQL
queries. `config/competency-questions.json` is the machine-readable source of
truth for question text, module coverage, required public terms, example
inputs, and expected non-empty results. CI verifies that the manifest and query
directory agree, that every required term is declared and used by its query,
that every example exists, and that every normative module and the vocabulary
are covered.

Module-level coverage means that each public term inherits at least one
documented use-case context from its declaration-owning module. The
`requiredTerms` list identifies the terms that the query must exercise
directly. Terms not yet needed by a domain query must still be justified by a
module question, documented, shaped where appropriate, and reviewed before
namespace freeze; the coverage rule must not be used to preserve speculative
placeholders.

| ID | Module scope | Question | Executable query |
| --- | --- | --- | --- |
| CQ-CORE-01 | core | Which identified resources have canonical labels, and which recorded temporal extent qualifies them? | `core-identity-and-time.rq` |
| CQ-INST-01 | instrument | Which components belong to an instrument and which contextual functional roles are assigned to them? | `components-and-roles.rq` |
| CQ-EVID-01 | evidence | Which fixed source snapshot and selected fragment support a citable source resource? | `source-fixity.rq` |
| CQ-PROV-01 | provenance | Which accountable processing activity used which input and generated which output? | `provenance-activity-lineage.rq` |
| CQ-ASSERT-01 | assertion, evidence | What subject, predicate, object, source fragment, and evidence role constitute a qualified assertion? | `assertion-evidence.rq` |
| CQ-ASSERT-02 | assertion | Which assertions conflict, under which criterion, and which accountable decision chose a member? | `assertion-conflict-decision.rq` |
| CQ-EVENT-01 | events, evidence, provenance | Which documented event affected which entity, and which source, evidence, record, and generation activity trace it? | `event-trace.rq` |
| CQ-ORGAN-01 | organ, instrument | Which qualified memberships connect a pipe organ to its organ components? | `organ-structure.rq` |
| CQ-MEDIA-01 | media, evidence | Which digital representation represents which resource, with what status, format, and fixity information? | `media-representation-fixity.rq` |
| CQ-AUDIO-01 | audio | Which source signal and extraction region produced an audio sample, and which playback, loop, and tuning records use it? | `audio-sample-playback.rq` |
| CQ-MIDI-01 | MIDI, audio | Which MIDI note and note-on velocity selection bounds activate a sampled-playback record? | `midi-playback-binding.rq` |
| CQ-CONTEXT-01 | context, assertion | Under which explicit dimension, relation, and identified value does an assertion apply? | `assertion-context.rq` |
| CQ-VMI-01 | virtual instrument, instrument, audio | Which product version implements a playable virtual instrument derived from which physical instrument state and using which sample? | `virtual-instrument-source-lineage.rq` |
| CQ-HERITAGE-01 | heritage | Which agent assigned a contextual heritage status to a resource, and which fixed, governed knowledge snapshot and historical review preserve the resulting assertions? | `heritage-knowledge-governance.rq` |
| CQ-VOCAB-01 | vocabulary | Which governed concepts are available in each MODAVIS concept scheme, with which labels and definitions? | `governed-vocabulary-discovery.rq` |

The natural-language question is authoritative for intent; the query is its
executable regression form. A query returning rows proves that a fixture can
answer the question, not that every future dataset is complete.
