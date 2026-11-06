# Trattoria Trussardi — estrutura do projeto

Projeto de pré-lançamento de um fan e-book artesanal inspirado em *JoJo's Bizarre Adventure: Parte 4*.

## Página de prévia

- Vercel: https://trattoria-trussardi-jeanlorencini60-2052.vercel.app
- Página em modo de pré-lançamento, sem checkout e com indexação desativada.
- A página apresenta as sete receitas do PDF enviado e identifica o projeto como obra independente de fã.

## Materiais sociais

- `social/trattoria-pin-model.svg`: peça vertical 2:3 para Pinterest.
- `social/trattoria-instagram-feed-model.svg`: peça 4:5 para o feed do Instagram.
- `social/trattoria-hero.svg`: arte da página de prévia.

As peças de Pinterest e Instagram são arquivos separados e usam composições diferentes.

## Próximas etapas antes de vender

1. Obter e documentar as autorizações necessárias para exploração comercial da propriedade intelectual.
2. Definir um domínio próprio coerente com a marca Trattoria Trussardi.
3. Criar o produto e o checkout próprios na Kiwify.
4. Criar uma propriedade GA4 e configurar Meta Pixel e Pinterest Tag para este produto.
5. Testar o checkout, a entrega do PDF e os eventos de compra antes de ativar anúncios.

## Automação anterior preservada

A estrutura do projeto mantém os componentes de automação anteriores:
- `app/main.py`
- `config/catalog.json`
- `.github/workflows/`

Esses componentes não fazem parte da página da Trattoria e não foram removidos nesta migração.
