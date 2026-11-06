# Radar TikTok

Agente para o Codex que pesquisa um nicho no TikTok, encontra concorrentes e baixa os vídeos para estudo. Por padrão, ele busca os vídeos que pegaram **poucas views**: dá para ver o que o concorrente tentou e fazer melhor.

## O que ele faz

1. Pesquisa palavras-chave do nicho e encontra perfis concorrentes.
2. Compara cada vídeo com a mediana de views do próprio perfil.
3. Baixa na maior qualidade disponível.
4. Remove os metadados, sem recodificar o vídeo.
5. Renomeia para `CV1.mp4`, `CV2.mp4`...
6. Separa por pasta e salva um `mapa.csv` com perfil, views e link.

```text
videos/
  2026-11-06/
    poucas_views/
      CV1.mp4
      CV2.mp4
    mapa.csv
```

## Instalar

Precisa de Python 3.9 ou mais novo, `yt-dlp` e `ffmpeg`.

```bash
brew install python yt-dlp ffmpeg
```

```bash
git clone <link-deste-repositório>
```

```bash
cd radar-tiktok
```

```bash
cp config.exemplo.json config.json
```

Abra o Codex nessa pasta. Ele lê o `AGENTS.md` e encontra a skill sozinho. Depois é só pedir:

> Pesquisa o nicho de estudo para concurso com câmera de cima, só perfis brasileiros, e baixa 30 vídeos com poucas views.

## Usar sem o Codex

```bash
python3 radar.py --perfis perfil1,perfil2 --qtd 10
```

| Opção | O que faz |
|---|---|
| `--modo poucas` | Vídeos abaixo da mediana do perfil, com 14 dias ou mais (padrão) |
| `--modo muitas` | Vídeos mais acima da mediana do perfil |
| `--modo ambos` | Divide a quantidade entre as duas pastas |
| `--qtd 30` | Total de vídeos |

## Configuração

| Campo | Padrão | Para que serve |
|---|---|---|
| `dias` | 180 | Idade máxima dos vídeos |
| `idade_minima_poucas` | 14 | Idade mínima para contar como vídeo fraco |
| `max_por_perfil` | 6 | Limite de vídeos por perfil |
| `prefixo` | `CV` | Início do nome dos arquivos |
| `marcar_samsung` | `false` | Grava fabricante Samsung nos metadados, para ferramentas que travam com arquivos sem essa informação |

## Limites

- A busca interna do TikTok pede login. O agente usa páginas públicas de descoberta.
- O TikTok pode bloquear leituras em sequência. O radar lê 2 perfis por vez e tenta de novo, mas não burla bloqueio nem captcha.
- A qualidade depende do que o TikTok entrega em cada vídeo.
- Nenhuma senha, cookie ou chave é necessária.
- As regras do TikTok restringem coleta automatizada. Use em pequeno volume, para estudo pessoal.
- Os vídeos têm dono: estude as ideias, mas não reposte o conteúdo.

## Testes

```bash
python3 -m unittest discover tests
```
