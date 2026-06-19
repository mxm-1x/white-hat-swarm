# ACME Internal Security Policy (excerpt) — used by the Compliance Auditor (RAG source)

## SOC 2 — Common Criteria
- CC6.1: Logical access controls must prevent unauthorized data disclosure.
- CC7.1: Vulnerabilities must be remediated and the fix independently verified
  before deployment to production.
- CC7.2: All changes to production code require a tamper-evident audit record
  identifying the change, the verifier, and the approver.

## OWASP Top 10 (2021)
- A03:2021 Injection — User input must never be concatenated into SQL, OS, or
  template strings. Use parameterized queries / prepared statements.
- A09:2021 Security Logging & Monitoring Failures — Security-relevant events
  (detection, remediation, approval) must be logged immutably.

## Remediation acceptance criteria
1. The root-cause vulnerability class is eliminated (not merely input-filtered).
2. The full existing regression suite passes.
3. A boundary/abuse test demonstrating the original exploit now fails to exploit.
4. No new secrets, network calls, or PII handling are introduced by the patch.
5. A human approver signs off before production deployment.
