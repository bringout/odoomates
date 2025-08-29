# Security

Access control and security definitions in accounting_pdf_reports.

## Access Control Lists (ACLs)

Model access permissions defined in:
- **[ir.model.access.csv](../accounting_pdf_reports/security/ir.model.access.csv)**
  - 24 model access rules

## Record Rules

Row-level security rules defined in:

```mermaid
graph TB
    subgraph "Security Layers"
        A[Users] --> B[Groups]
        B --> C[Access Control Lists]
        C --> D[Models]
        B --> E[Record Rules]
        E --> F[Individual Records]
    end
```

Security files overview:
- **[ir.model.access.csv](../accounting_pdf_reports/security/ir.model.access.csv)**
  - Model access permissions (CRUD rights)

Notes
- Access Control Lists define which groups can access which models
- Record Rules provide row-level security (filter records by user/group)
- Security groups organize users and define permission sets
- All security is enforced at the ORM level by Odoo
