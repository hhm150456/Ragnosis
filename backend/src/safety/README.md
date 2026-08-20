# Safety Layer

The query pipeline applies two safety stages:

1. `confidence.py` refuses before generation when the best retrieved
	`combined_score` is below `MIN_CONFIDENCE_THRESHOLD`.
2. `faithfulness.py` asks the same LLM client whether each generated claim is
	supported by its cited chunk. Failed checks remain visible as unverified
	claims and downgrade the answer to `partial_refusal`.

The faithfulness check fails closed: malformed or unavailable verifier output
is treated as unverified rather than trusted.
