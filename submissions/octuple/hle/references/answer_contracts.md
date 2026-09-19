# Answer-contract adapter

For multiple choice, derive an initial view, then compare every option using:

`option | literal entailment | standard disciplinary reading | likely author intent |`
`coverage of supplied details | fatal flaw`

Wording such as “most plausible,” “best explains,” or “most closely” may ask for the
standard intended analogy rather than a formally forced theorem. Normalize equivalent
forms and steelman the strongest competitor. Return the exact requested label and text;
do not place alternatives in the answer field.

For exact match, normalize units, notation, capitalization, significant figures,
precision, ordering, and transformation direction. Remove alternatives and hedging
from `Answer:`. For numbers, expressions, strings, entities, formulas, and short
explanations, preserve the representation explicitly requested by the task.

The response guard validates delivery and the default schema, not correctness. The
final saved response must contain one independently extractable answer.
