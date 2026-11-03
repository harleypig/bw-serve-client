# Security Policy

## Supported versions

`bw-serve-client` is pre-1.0. Only the latest release gets security fixes;
upgrade to it before reporting, and expect a fix to ship as a new release
rather than as a backport.

| Version        | Supported |
|----------------|-----------|
| Latest release | Yes       |
| Anything older | No        |

## Reporting a vulnerability

Do not open a public issue, discussion or pull request for a vulnerability.
Report it privately through GitHub's [private vulnerability
reporting][advisory]: only the repository's maintainers can read the report,
so it stays private until a fix ships.

Include what you can of:

- the affected version, and the `bw` CLI version you ran it against;
- what an attacker can do, and what they need first;
- the steps or code that reproduce it.

You will get an acknowledgement on the advisory, and the fix and the
advisory are published together once a release carries the fix.

## Out of scope

A vulnerability in `bw serve` or the Bitwarden CLI itself belongs to
Bitwarden: report it through [Bitwarden's own process][bitwarden].

[advisory]: https://github.com/harleypig/bw-serve-client/security/advisories/new
[bitwarden]: https://github.com/bitwarden/clients/security/policy
