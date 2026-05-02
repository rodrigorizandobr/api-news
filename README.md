# API News (FastAPI + Cloud Functions + Terraform)

API de noticias com contrato estavel, baseada em Python/FastAPI, com cache no Firestore e deploy em Google Cloud Functions (gen2) via Terraform.

## Objetivo

- Fornecer endpoint unico e estavel para busca de noticias.
- Controlar custo de consulta BigQuery com guardrails.
- Manter deploy simples, reprodutivel e barato.

## Arquitetura

- Backend: Python + FastAPI em Cloud Functions.
- Fonte de dados: GDELT/BigQuery.
- Cache: Firestore.
- Infra as code: Terraform.

## Pre-requisitos

Instale e configure localmente:

- Python 3.12+
- make
- gcloud CLI autenticado
- Terraform >= 1.5.0
- zip

Validacoes rapidas:

```bash
python3 --version
terraform --version
gcloud auth list
```

## Setup local (desenvolvimento)

Na raiz do projeto:

```bash
make install
make test
```

Executar API local com emulador Firestore:

```bash
# Terminal 1
make firestore-emulator

# Terminal 2
make dev
```

API local: http://localhost:8080

Smoke test:

```bash
curl "http://localhost:8080/health"
curl "http://localhost:8080/news?q=tesla,spacex&date=2026-04-09&language=en&country=US"
```

## Criacao de infraestrutura (Terraform)

1. Criar arquivo local de variaveis (nao versionado):

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
```

2. Editar terraform.tfvars com os valores do seu projeto GCP.

Opcional para ambientes dedicados (dev/prd), tambem locais e nao versionados:

```bash
cp environments/dev.tfvars.example environments/dev.tfvars.local
cp environments/prd.tfvars.example environments/prd.tfvars.local
```

Para aplicar com arquivo de ambiente:

```bash
terraform plan -var-file=environments/dev.tfvars.local -out=tfplan
terraform apply tfplan
```

3. Voltar para raiz e gerar pacote da funcao:

```bash
cd ..
make build-cf
```

4. Planejar e aplicar:

```bash
make terraform-plan
make terraform-apply
```

5. Obter URL da funcao:

```bash
cd terraform
terraform output -raw function_uri
```

## Como rodar em producao

Exemplo de chamada:

```bash
FUNCTION_URL=$(cd terraform && terraform output -raw function_uri)
curl "${FUNCTION_URL}/news?q=tesla,spacex&date=2026-04-09&language=en&country=US"
```

Health check:

```bash
curl "${FUNCTION_URL}/health"
```

## Guardrails de custo

- Limite por query BigQuery via `bigquery_max_bytes_billed`.
- Budget mensal no projeto via Terraform (`enable_project_budget_guardrail`).
- Cache historico no Firestore reduz custo de repeticao.

## Seguranca para repositorio publico

Arquivos que NAO devem ir para Git publico:

- `terraform/terraform.tfvars`
- `terraform/**/*.tfvars`
- `terraform/*.tfstate`
- `terraform/*.tfstate.*`
- Chaves/certificados (`*.pem`, `*.key`, `*.p12`, `*.pfx`)
- JSONs de credenciais (`*service-account*.json`, `*credentials*.json`)

O `.gitignore` ja foi ajustado para bloquear esses artefatos.

Antes de publicar, confirme:

```bash
git status --ignored
```

## Estrutura do projeto

- `api/`: aplicacao FastAPI, logica de negocio, testes
- `terraform/`: infraestrutura cloud
- `DEPLOYMENT.md`: guia detalhado de deploy
- `api/README.md`: contrato e payload da API
- `api/AUTH.md`: opcoes de autenticacao

## Comandos principais

```bash
make help
make install
make test
make dev
make firestore-emulator
make build-cf
make terraform-plan
make terraform-apply
```

## Troubleshooting rapido

- Falha no deploy Terraform:

```bash
cd terraform
terraform show
terraform state list
```

- Erro de autenticacao GCP:

```bash
gcloud auth login
gcloud config set project <SEU_PROJECT_ID>
```

- API sem cache local:

```bash
echo $FIRESTORE_EMULATOR_HOST
```

## Referencias

- [DEPLOYMENT.md](DEPLOYMENT.md)
- [api/README.md](api/README.md)
- [api/AUTH.md](api/AUTH.md)
- [AUTHENTICATION-OPTIONS.md](AUTHENTICATION-OPTIONS.md)
