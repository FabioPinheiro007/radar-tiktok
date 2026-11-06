---
name: radar-tiktok
description: Pesquisa um nicho no TikTok, encontra concorrentes brasileiros e baixa os vídeos com poucas views (ou muitas), com metadados limpos e nomes CV1, CV2... Use quando o usuário pedir para pesquisar um nicho, achar concorrentes ou baixar vídeos do TikTok para estudo.
---

# Radar TikTok

## 1. Entender o pedido

Anote o nicho, o país do público, o formato e o que evitar, como legenda na tela. Se o nicho não foi dito, pergunte.

## 2. Achar concorrentes

1. Crie de 8 a 15 palavras-chave do nicho.
2. Use a busca da web limitada a `tiktok.com` para achar páginas `tiktok.com/discover/<palavra-chave>`.
3. Se tiver navegador, abra essas páginas. Elas são públicas e listam vídeos. Pegue os `@perfil` dos links `/@perfil/video/<id>`.
4. Sem navegador, use só os perfis que aparecerem na busca ou peça uma lista ao usuário.
5. Fique só com perfis do público pedido e tire professores ou lojas que fujam do formato.

A busca interna do TikTok pede login. Não peça a senha do usuário para contornar isso.

## 3. Baixar

Coloque os perfis em `config.json` (copie de `config.exemplo.json`) e rode:

```bash
python3 radar.py --qtd 30
```

- Poucas views é o padrão: vídeos abaixo da mediana do próprio perfil, com pelo menos 14 dias.
- `--modo muitas` pega os mais fortes. `--modo ambos` divide nas duas pastas.
- `--perfis a,b,c` substitui a lista do config.

## 4. Conferir e entregar

1. Veja se algum perfil falhou nas mensagens com `!`. Se muitos falharem, espere alguns minutos e rode de novo. Não burle bloqueio.
2. Abra `videos/<data>/mapa.csv`, que liga cada `CV1.mp4` ao perfil, às views e ao link.
3. Diga ao usuário quantos vídeos baixou, em qual pasta e o que ficou de fora.

Os vídeos são para estudo. Avise o usuário para não repostar o conteúdo de outra pessoa.
