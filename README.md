# OFERTAS MIL +

Máquina de ofertas do Mercado Livre para o Canal do WhatsApp.

## Configurado

- Marca: OFERTAS MIL +
- Canal: https://whatsapp.com/channel/0029VbE8GNCFXUugvlHSwM2F
- 5 links de afiliado iniciais em `config/catalog.json`
- resolução dos links `meli.la`
- consulta da API pública de item do Mercado Livre quando o MLB é identificado
- histórico de preço em SQLite
- filtro mínimo de desconto/preço
- bloqueio de republicação por 7 dias
- GitHub Actions a cada 30 minutos
- `DRY_RUN=true` por segurança

## Fluxo

Mercado Livre → resolve link → consulta item → registra preço → filtra → gera anúncio → publica no Canal do WhatsApp.

## Instalação no GitHub

1. Crie o repositório `ofertas-mil-plus`.
2. Faça upload do conteúdo desta pasta para a raiz do repositório.
3. Vá em **Actions** → **OFERTAS MIL +** → **Run workflow**.
4. Deixe `DRY_RUN=true` no primeiro teste.
5. Confira os logs e o arquivo `data/offers.sqlite3`.

## Segredos para publicação

Em **Settings → Secrets and variables → Actions**:

Secret:
- `WHAPI_TOKEN`
- `WHATSAPP_CHANNEL_JID`

Variable opcional:
- `DRY_RUN=false` quando estiver tudo validado
- `WHAPI_BASE_URL=https://gate.whapi.cloud`

Nunca coloque tokens no código ou no `catalog.json`.

## Publicação no WhatsApp

O módulo de publicação está preparado para um provedor compatível com Canais do WhatsApp, via Whapi.Cloud. A publicação permanece desligada enquanto `DRY_RUN=true`.

## Mercado Livre

Use apenas os links de afiliado oficiais gerados pelo programa do Mercado Livre. O sistema não fabrica links de afiliado e não automatiza cliques ou compras.


## Landing page

- Produção: https://guiadoacougue.com.br
- Vercel: https://guia-acougue-jeanlorencini60-2052.vercel.app
