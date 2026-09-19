# Authentication and privacy

Use this procedure only when customer-specific records must be read or modified. General information does not require authentication.

## Sequence

1. Determine that private access is actually needed.
2. Use the available read/lookup mechanism required by the runtime, but do not disclose anything it returns.
3. Ask the customer to provide permitted verification values. Under the banking policy, successful verification normally means any two correct values among date of birth, email, phone number, and address.
4. Compare only the values the customer supplies. Name and user ID identify a record but do not count as the two verification values.
5. If fewer than two valid values have been established, request only the missing permitted value(s). If a supplied value is wrong, say verification is incomplete without revealing the stored value.
6. After two values match, call the required verification logging tool. Verification is complete only when that call succeeds.
7. Record `identity_verified_and_logged = true` and do not verify again in the same conversation.

## Privacy boundaries

- Before logged verification, do not reveal balances, transactions, profile fields, account status, loan details, or other customer-specific information.
- Never read a stored value aloud and ask the customer to agree with it.
- Do not count information obtained only from private records as customer-provided evidence.
- Do not request documents, receipts, or additional evidence unless retrieved KB guidance explicitly authorizes the exact process.
- If verification cannot be completed, do not attempt the protected access or action. Use retrieved policy to give the permitted next step.

Authentication is a gate, not the customer's goal. After it succeeds, immediately resume the original intent.
