# Authentication & Authorization

Este projeto usa apenas autenticação JWT via Bearer Token para o endpoint `/news`.

## Padrão Obrigatório

- Header: `Authorization: Bearer <token>`
- Algoritmo: `HS256`
- Secret: `AUTH_JWT_SECRET` com no mínimo 32 caracteres

## Configuração

```env
AUTH_JWT_SECRET=your-min-32-char-secret-key-here
AUTH_JWT_ALGORITHM=HS256
AUTH_JWT_EXPIRY_HOURS=24
```

## Gerar Token

```bash
python api/generate_token.py --secret "$AUTH_JWT_SECRET" --expiry-hours 24
```

## Exemplo de Uso

```bash
TOKEN=$(python api/generate_token.py --secret "$AUTH_JWT_SECRET" --expiry-hours 24 | tail -2 | head -1)
curl -H "Authorization: Bearer $TOKEN" \
  "https://api-news.../news?q=bitcoin&date=2026-04-09&language=en&country=US"
```

## Respostas de Erro

- `401 Missing or invalid Authorization header` quando não há Bearer token
- `401 Token has expired` quando token expirou
- `401 Invalid token` quando assinatura/payload são inválidos

## Recomendações de Produção

1. Armazene `AUTH_JWT_SECRET` fora do Git (arquivo local ignorado ou Secret Manager).
2. Faça rotação periódica de secret.
3. Use expiração curta de token para clientes externos.
4. Mantenha TLS/HTTPS obrigatório no tráfego externo.
