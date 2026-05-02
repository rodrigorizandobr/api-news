# Autenticação da API (JWT Bearer Only)

A API usa exclusivamente `Authorization: Bearer <token>`.

## Configuração Terraform

No arquivo local `terraform/terraform.tfvars` (ignorado pelo Git):

```hcl
auth_jwt_secret       = "coloque-um-secret-forte-min-32-chars"
auth_jwt_expiry_hours = 24
```

## Gerar Token

```bash
cd api
AUTH_JWT_SECRET="coloque-um-secret-forte-min-32-chars" python generate_token.py
```

## Chamar Endpoint

```bash
curl -H "Authorization: Bearer <token>" \
  "https://api-news.../news?q=bitcoin&date=2026-04-09&language=en&country=US"
```

## Observações

- `Basic Auth` não é mais suportado.
- Requests sem Bearer token em `/news` retornam `401`.
