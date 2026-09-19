# Answer-contract adapter

For multiple choice, solve independently, compare against every option, normalize
equivalent forms, identify the strongest competitor and discriminating evidence, then
return the exact requested label and text. Do not anchor on an option first.

For exact match, normalize units, notation, capitalization, significant figures,
precision, ordering, and transformation direction. Remove alternatives and hedging
from `Answer:`. For numbers, expressions, strings, entities, formulas, and short
explanations, preserve the representation explicitly requested by the task.

Use the `answer_format` check in `scripts/hle_review.py`; it checks form only. The
final saved response must contain one independently extractable answer.
