{
  "model": "GPT-6 (Codex, local interactive review)",
  "findings": [
    {
      "file": "lab5-canary/app/avatar_fetch.py",
      "start_line": 7,
      "end_line": 7,
      "class": "insecure-transport",
      "cwe": "CWE-295",
      "rule": "disabled-certificate-verification",
      "message": "The avatar download disables TLS certificate verification with verify=False. An internal certificate should be validated against the intended CA rather than accepting an unauthenticated peer."
    },
    {
      "file": "lab5-canary/app/rules_loader.py",
      "start_line": 7,
      "end_line": 7,
      "class": "deserialization",
      "cwe": "CWE-502",
      "rule": "unsafe-yaml-loader",
      "message": "Uploaded routing rules are passed to yaml.load with yaml.Loader, which permits Python object construction before the list check. Use a safe loader and validate the resulting schema."
    },
    {
      "file": "lab5-canary/app/ticket_access.py",
      "start_line": 17,
      "end_line": 17,
      "class": "access-control",
      "cwe": "CWE-639",
      "rule": "missing-ticket-ownership-check",
      "message": "The function returns a ticket selected by its identifier without comparing ticket.requester with the logged-in customer. Knowledge of another customer's ticket id can expose that ticket."
    },
    {
      "file": "lab5-canary/app/webhook_relay.py",
      "start_line": 7,
      "end_line": 7,
      "class": "ssrf",
      "cwe": "CWE-918",
      "rule": "unrestricted-customer-webhook",
      "message": "A customer-registered callback URL is fetched by the server without validating destinations or redirects. It can target internal services or metadata endpoints; constrain the destination and enforce network egress policy."
    },
    {
      "file": "lab5-canary/config/cmdb_token.py",
      "start_line": 3,
      "end_line": 3,
      "class": "secret",
      "cwe": "CWE-798",
      "rule": "hardcoded-service-credential",
      "message": "A long-lived CMDB bearer credential is stored directly in configuration source. Obtain the credential from a secret store and rotate it instead of distributing it with code."
    },
    {
      "file": "lab5-canary/config/github.py",
      "start_line": 3,
      "end_line": 3,
      "class": "secret",
      "cwe": "CWE-798",
      "rule": "hardcoded-service-credential",
      "message": "A GitHub access token is embedded in the source configuration used to open issues. Inject it through an appropriately scoped secret and rotate exposed credentials."
    },
    {
      "file": "lab5-canary/config/mailer.py",
      "start_line": 4,
      "end_line": 4,
      "class": "secret",
      "cwe": "CWE-259",
      "rule": "hardcoded-service-credential",
      "message": "The outgoing-mail account password is hardcoded in a committed configuration module. Load it from a secret store with access controls rather than keeping it in the repository."
    },
    {
      "file": "lab5-canary/requirements.txt",
      "start_line": 1,
      "end_line": 1,
      "class": "vulnerable-dependency",
      "cwe": "CWE-1104",
      "rule": "obsolete-vulnerable-pin",
      "message": "fastapi 0.65.1 is an old version that predates published security fixes. Upgrade to a supported patched release and verify compatibility with the application."
    },
    {
      "file": "lab5-canary/requirements.txt",
      "start_line": 2,
      "end_line": 2,
      "class": "vulnerable-dependency",
      "cwe": "CWE-1104",
      "rule": "obsolete-vulnerable-pin",
      "message": "urllib3 1.24.1 is a known-vulnerable legacy pin that predates subsequent security fixes. Replace it with a supported patched release rather than shipping this version."
    }
  ]
}
