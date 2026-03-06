# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | Yes                |

Only the latest minor release receives security patches. Users are encouraged to stay
on the most recent version.

## Reporting a Vulnerability

If you discover a security vulnerability in netmap, please report it responsibly.
**Do not open a public GitHub issue for security vulnerabilities.**

Instead, send an email to **security@netmap.dev** with:

- A description of the vulnerability
- Steps to reproduce the issue
- The affected version(s)
- Any potential impact assessment

### What to Expect

- **Acknowledgement** within 48 hours of your report.
- **Status update** within 7 days with an initial assessment.
- **Fix timeline** — critical vulnerabilities will be patched as soon as possible,
  typically within 14 days. Lower-severity issues will be addressed in the next
  scheduled release.

If the vulnerability is accepted, we will:

1. Develop and test a fix in a private branch.
2. Assign a CVE identifier if applicable.
3. Release a patched version and publish a security advisory.
4. Credit the reporter (unless anonymity is requested).

If the vulnerability is declined, we will provide a detailed explanation of why.

## Security Considerations

Netmap is a network scanning and topology discovery tool. By its nature, it interacts
with network devices and services. Operators should:

- Run netmap only on networks you are authorized to scan.
- Restrict API access using authentication (JWT tokens are required for all
  non-health endpoints).
- Deploy behind a reverse proxy with TLS in production.
- Keep the database credentials secure and avoid default passwords.
- Review the Docker Compose configuration before deploying to production.
